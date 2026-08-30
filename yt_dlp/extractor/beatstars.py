from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BeatStarsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[\w-]+\.)?beatstars\.com/(?:(?:[^/?#]+/)?beat/(?:[^/?#]+-)?|(?i:TK))(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.beatstars.com/TK3202809',
        'md5': 'ad20171eeb0ee55a95b136c5fde5cd21',
        'info_dict': {
            'id': '3202809',
            'ext': 'mp3',
            'title': 'LOL',
            'track': 'LOL',
            'display_id': 'lol-3202809',
            'duration': 218,
            'timestamp': 1569157708,
            'upload_date': '20190922',
            'uploader': 'Fly Melodies',
            'uploader_id': 'flymelodies',
            'uploader_url': 'https://www.beatstars.com/flymelodies',
            'artists': ['Fly Melodies'],
            'genres': ['Hip Hop', 'Trap'],
            'tags': ['lil mosey', 'lil tecca', 'lil uzi vert'],
            'thumbnail': r're:https://main\.v2\.beatstars\.com/.+',
        },
    }, {
        'url': 'https://www.beatstars.com/beat/lol-3202809',
        'only_matching': True,
    }, {
        'url': 'https://www.beatstars.com/flymelodies/beat/lol-3202809',
        'only_matching': True,
    }, {
        'url': 'https://flymelodies.beatstars.com/beat/lol-3202809',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        track_id = self._match_id(url)
        data = self._download_json(
            'https://main.v2.beatstars.com/track', track_id,
            query={'id': track_id}, headers={'Accept': 'application/json'})
        details = traverse_obj(data, ('response', 'data', 'details', {dict}))
        if not details:
            raise ExtractorError(
                traverse_obj(data, ('response', 'data', 'message', {str})) or 'Track not found',
                expected=True)

        if traverse_obj(details, ('availability', 'private')):
            self.raise_login_required('This beat is private')

        formats = []
        mp3_url = traverse_obj(details, (
            (('bundle', 'stream', 'url'), 'stream_ssl_url', 'stream_url'),
            {url_or_none}, any))
        if mp3_url:
            formats.append({
                'url': mp3_url,
                'format_id': 'http-mp3',
                'ext': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
            })
        else:
            hls_url = traverse_obj(details, (
                (('bundle', 'hls', 'url'), 'stream_hls_url'), {url_or_none}, any))
            if hls_url:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, track_id, 'mp3', m3u8_id='hls', fatal=False))

        if not formats:
            self.raise_no_formats(
                'No public stream is available for this beat', expected=True, video_id=track_id)

        return {
            'id': track_id,
            'formats': formats,
            'duration': (
                int_or_none(traverse_obj(details, ('bundle', 'stream', 'duration')))
                or parse_duration(details.get('duration'))),
            **traverse_obj(details, {
                'title': ('title', {str}),
                'track': ('title', {str}),
                'display_id': ('title_uri', {str}),
                'description': ('description', {str}, filter),
                'timestamp': ('release_date_time', {int_or_none}),
                'thumbnail': ('artwork', ('original', 'default', 'thumb'), {url_or_none}, any),
                'uploader': ('musician', 'display_name', {str}),
                'uploader_id': ('musician', 'permalink', {str}),
                'uploader_url': ('musician', 'beatstars_uri', {url_or_none}),
                'artists': ('musician', 'display_name', {str}, all),
                'genres': ('genre', ..., 'name', {str}),
                'tags': ('tags', 'list', ..., 'tag', {str}),
            }),
        }
