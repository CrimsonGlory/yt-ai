from .common import InfoExtractor
from ..utils import (
    UserNotLive,
    int_or_none,
    parse_iso8601,
    urljoin,
)
from ..utils.traversal import traverse_obj


class OwncastIE(InfoExtractor):
    IE_NAME = 'owncast'
    IE_DESC = 'Owncast'
    _VALID_URL = r'https?://(?:www\.)?(?P<id>live\.retrostrange\.com)(?:/(?:embed(?:/video)?/?|hls/stream\.m3u8)?)?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://live.retrostrange.com/',
        'info_dict': {
            'id': 'live.retrostrange.com',
            'ext': 'mp4',
            'title': r're:24/7 vintage sci-fi, horror, filmstrips, and ephemera \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
            'description': 'md5:c1c2ee1be6ab6198a007f37fcdc17c9c',
            'thumbnail': 'https://live.retrostrange.com/logo',
            'channel': 'RetroStrange TV',
            'uploader': 'RetroStrange TV',
            'timestamp': int,
            'upload_date': r're:\d{8}',
            'concurrent_view_count': int,
            'tags': ['streaming', 'retro', 'movies', 'sci fi', 'horror', 'tv', 'vintage', 'public domain', 'ad free'],
            'age_limit': 0,
            'is_live': True,
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://live.retrostrange.com/embed/video',
        'only_matching': True,
    }, {
        'url': 'https://live.retrostrange.com/hls/stream.m3u8',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        base = f'https://{video_id}'

        status = self._download_json(
            f'{base}/api/status', video_id, 'Downloading stream status')
        config = self._download_json(
            f'{base}/api/config', video_id, 'Downloading instance config',
            fatal=False) or {}

        if not traverse_obj(status, 'online'):
            raise UserNotLive(video_id=video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'{base}/hls/stream.m3u8', video_id, 'mp4', m3u8_id='hls', live=True)

        nsfw = traverse_obj(config, ('nsfw', {bool}))

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
            'age_limit': 18 if nsfw else 0 if nsfw is False else None,
            **traverse_obj(status, {
                'title': ('streamTitle', {str}),
                'concurrent_view_count': ('viewerCount', {int_or_none}),
                'timestamp': ('lastConnectTime', {parse_iso8601}),
            }),
            **traverse_obj(config, {
                'title': (('streamTitle', 'name'), {str}, any),
                'description': ('summary', {str}),
                'thumbnail': ('logo', {lambda x: urljoin(base, x)}),
                'channel': ('name', {str}),
                'uploader': ('name', {str}),
                'tags': ('tags', ..., {str}, all),
            }),
        }
