import json
import uuid

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class KidoodleIE(InfoExtractor):
    IE_NAME = 'kidoodle'
    IE_DESC = 'Kidoodle.TV'
    _VALID_URL = r'https?://(?:www\.)?kidoodle\.tv/(?:watch|player(?:/shorts)?)/(?P<series>[^/?#]+)/(?P<id>\d+)'
    _FOLKS_GUEST_TOKEN_URL = 'https://folks.be.kidoodle.tv/v1/auth/guest/token'
    _ALBEDO_API_BASE = 'https://albedo.be.kidoodle.tv/api/2.0'
    _TESTS = [{
        'url': 'https://kidoodle.tv/watch/Numberblocks2022/83111',
        'md5': '74df2851d9148029b0d59d5b225b25c9',
        'info_dict': {
            'id': '83111',
            'ext': 'mp4',
            'display_id': 'Numberblocks2022',
            'title': 'Odds and Evens',
            'description': 'The Numberblocks play an exciting game of bounceball _ and it\'s the Even Tops versus the Odd Blocks. Learn about odd and even numbers with the Numberblocks.',
            'thumbnail': 'https://d1o8tw6489vwho.cloudfront.net/Numberblocks2022/S02/keyart_e11_large.jpg',
            'duration': 302.037333,
            'series': 'Numberblocks',
            'series_id': '2326',
            'season': 'Season 2',
            'season_number': 2,
            'episode': 'Episode 11',
            'episode_number': 11,
            'timestamp': 1494806400,
            'upload_date': '20170515',
            'age_limit': 0,
            'genres': ['Family'],
            'subtitles': 'count:1',
        },
    }, {
        'url': 'https://kidoodle.tv/player/Numberblocks2022/83111',
        'only_matching': True,
    }, {
        'url': 'https://www.kidoodle.tv/player/shorts/Numberblocks2022/83111',
        'only_matching': True,
    }]

    def _auth_headers(self, video_id):
        token = getattr(self, '_kidoodle_token', None)
        if not token:
            token_data = self._download_json(
                self._FOLKS_GUEST_TOKEN_URL, video_id, 'Downloading guest token',
                data=json.dumps({
                    'device_id': str(uuid.uuid4()),
                    'platform': 'web',
                }).encode(),
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                })
            token = traverse_obj(token_data, ('access_token', {str}))
            if not token:
                raise ExtractorError('Unable to obtain Kidoodle guest token', expected=True)
            self._kidoodle_token = token
        return {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}',
        }

    def _call_albedo(self, path_or_url, video_id, note):
        url = (path_or_url if path_or_url.startswith('http')
               else f'{self._ALBEDO_API_BASE}/{path_or_url.lstrip("/")}')
        try:
            return self._download_json(
                url, video_id, note, headers=self._auth_headers(video_id))
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (401, 403):
                self.raise_login_required('This video requires a Kidoodle.TV account')
            raise

    def _real_extract(self, url):
        series, video_id = self._match_valid_url(url).group('series', 'id')
        episode = self._call_albedo(
            f'content/episodes/{video_id}', video_id, 'Downloading episode metadata')
        if not isinstance(episode, dict):
            raise ExtractorError('Unable to extract episode metadata', expected=True)
        if episode.get('requiresSubscription'):
            self.raise_login_required('This video is only available to subscribers')

        video_url = traverse_obj(episode, ('videoUrl', {url_or_none}))
        if not video_url:
            self.raise_no_formats('No video URL', expected=True, video_id=video_id)

        stream = self._call_albedo(video_url, video_id, 'Downloading video stream') or {}
        if traverse_obj(stream, ('drm', 'licenseUrl', {url_or_none})):
            self.report_drm(video_id)

        manifest_url = traverse_obj(stream, ('manifestUrl', {url_or_none}))
        if not manifest_url:
            self.raise_no_formats('No video stream', expected=True, video_id=video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            manifest_url, video_id, 'mp4', m3u8_id='hls')

        genre = traverse_obj(episode, ('content_genre', {str}))
        return {
            'id': str_or_none(episode.get('id')) or video_id,
            'display_id': series,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 0,
            'thumbnail': traverse_obj(episode, (
                'images', lambda _, v: v.get('role') == 'keyart' and v.get('width') == 1280,
                'url', {url_or_none}, any)) or traverse_obj(episode, ('imageUrl', {url_or_none})),
            'genres': [genre] if genre else None,
            **traverse_obj(episode, {
                'title': ('title', {str}),
                'description': (('summary', 'shortSummary'), {str}, any),
                'duration': ('duration', {float_or_none}),
                'series': ('seriesName', {str}),
                'series_id': ('seriesId', {str_or_none}),
                'season_number': ('season', {int_or_none}),
                'episode_number': ('episode', {int_or_none}),
                'timestamp': ('premiere_date', {unified_timestamp}),
            }),
        }
