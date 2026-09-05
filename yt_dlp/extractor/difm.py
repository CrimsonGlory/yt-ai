import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    float_or_none,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    str_or_none,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class DIFMIE(InfoExtractor):
    IE_NAME = 'di.fm'
    IE_DESC = 'DI.FM'
    _VALID_URL = r'https?://(?:www\.)?di\.fm/shows/(?P<show>[\w-]+)/episodes/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.di.fm/shows/airwaves-progressions-radio/episodes/047',
        'skip': 'no playable formats',
        'md5': '71b2fb14dc20d8077c73b1976f1056fe',
        'info_dict': {
            'id': '174775',
            'ext': 'm4a',
            'title': 'Progressions 047 (06 January 2024)',
            'display_id': '047',
            'duration': 7267.0,
            'timestamp': 1704553200,
            'upload_date': '20240106',
            'series': "Airwave's Progressions Radio",
            'series_id': '10554692',
            'episode': '#047',
            'episode_number': 47,
            'artists': ['Airwave'],
            'thumbnail': r're:https://cdn-images\.audioaddict\.com/.+\.png',
            'channel': 'Progressive',
            'channel_id': 'progressive',
        },
    }, {
        'url': 'https://di.fm/shows/airwaves-progressions-radio/episodes/047',
        'only_matching': True,
    }, {
        'url': 'http://www.di.fm/shows/airwaves-progressions-radio/episodes/047',
        'only_matching': True,
    }]
    _API_BASE = 'https://api.audioaddict.com/v1/di'
    _FORMAT_CODECS = {
        1: ('mp3', 'mp3'),
        3: ('aac', 'm4a'),
    }
    _QUALITY_ABR = {
        2: 64,
        3: 96,
        4: 128,
        6: 320,
    }

    def _aa_url(self, url):
        url = url_or_none(unescapeHTML(url) if url else None)
        if not url:
            return None
        return self._proto_relative_url(re.sub(r'\{[^}]*\}$', '', url))

    def _extract_formats(self, tracks):
        formats = []
        for asset in traverse_obj(tracks, (
            ..., 'content', 'assets', lambda _, v: url_or_none(v.get('url')),
        )):
            media_url = self._aa_url(asset.get('url'))
            if not media_url:
                continue
            acodec, ext = self._FORMAT_CODECS.get(
                asset.get('content_format_id'), (None, None))
            abr = self._QUALITY_ABR.get(asset.get('content_quality_id'))
            formats.append({
                'url': media_url,
                'format_id': '-'.join(filter(None, (
                    'http', acodec, str(abr) if abr else None))),
                'ext': ext or 'm4a',
                'acodec': acodec or 'none',
                'vcodec': 'none',
                'abr': abr,
                'filesize': int_or_none(asset.get('size')),
                'http_headers': {'Referer': 'https://www.di.fm/'},
            })
        return formats

    def _extract_episode(self, episode, display_id):
        episode_id = str_or_none(episode.get('id')) or display_id
        tracks = episode.get('tracks') or []
        formats = self._extract_formats(tracks)
        if not formats:
            if episode.get('free') is False:
                self.raise_login_required(
                    'This episode is only available to DI.FM Premium members')
            self.raise_no_formats(
                'No playable audio found', expected=True, video_id=episode_id)

        track = traverse_obj(
            tracks, (lambda _, v: v.get('title') or v.get('content'), any)) or {}
        thumbnail = self._aa_url(traverse_obj(track, (
            (('images', 'default'), 'asset_url'), {str}, any))) or self._aa_url(
            traverse_obj(episode, (
                'show', 'images', ('compact', 'default'), {str}, any)))

        return {
            'id': episode_id,
            'display_id': display_id,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': (
                float_or_none(track.get('length'))
                or float_or_none(traverse_obj(track, ('content', 'length')))
                or float_or_none(episode.get('duration'))),
            'timestamp': parse_iso8601(episode.get('start_at')),
            'series': unescapeHTML(traverse_obj(episode, ('show', 'name', {str}))),
            'series_id': str_or_none(traverse_obj(episode, ('show', 'id'))),
            'episode': unescapeHTML(str_or_none(episode.get('name'))),
            'episode_number': int_or_none(display_id),
            'artists': traverse_obj(track, ('artists', ..., 'name', {str})),
            'channel': traverse_obj(episode, ('show', 'channels', 0, 'name', {str})),
            'channel_id': traverse_obj(episode, ('show', 'channels', 0, 'key', {str})),
            'title': unescapeHTML(traverse_obj(track, (
                ('display_title', 'title', 'track'), {str}, any))) or join_nonempty(
                    unescapeHTML(traverse_obj(episode, ('show', 'name', {str}))),
                    unescapeHTML(str_or_none(episode.get('name'))), delim=' - '),
            'description': traverse_obj(episode, (
                ('description_html', 'description'), {clean_html}, filter, any)),
        }

    def _real_extract(self, url):
        show_slug, display_id = self._match_valid_url(url).group('show', 'id')
        webpage = self._download_webpage(url, display_id, impersonate=True)

        episode = traverse_obj(self._search_json(
            r'"EpisodeDetail\.LayoutEngine"\s*,', webpage, 'episode data',
            display_id, fatal=False), ('episode', {dict}))

        if not traverse_obj(episode, ('tracks', ..., 'content', 'assets', ..., 'url')):
            audio_token = self._search_regex(
                r'"audio_token"\s*:\s*"([0-9a-f]+)"', webpage, 'audio token', default=None)
            episode = self._download_json(
                f'{self._API_BASE}/shows/{show_slug}/episodes/{display_id}',
                display_id, query={'audio_token': audio_token} if audio_token else {},
                headers={'Accept': 'application/json'})

        return self._extract_episode(
            traverse_obj(episode, {dict}, {require('episode data')}), display_id)
