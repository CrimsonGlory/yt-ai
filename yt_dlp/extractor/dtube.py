from .common import InfoExtractor
from ..networking import HEADRequest
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    traverse_obj,
    url_or_none,
)


class DTubeIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = (
        r'https?://(?:www\.)?d\.tube/watch/(?P<id>[\w-]+)',
        r'https?://(?:www\.)?d\.tube/(?:#!/)?v/(?P<uploader_id>[0-9a-z.-]+)/(?P<id>[0-9a-z]{8})',
    )
    _TESTS = [{
        'url': 'https://d.tube/watch/8AnXXgx4Hy5W6eetPnQTAc',
        'md5': '0fd9e3507ce535a29207a7af44974a7f',
        'info_dict': {
            'id': '8AnXXgx4Hy5W6eetPnQTAc',
            'ext': 'mp4',
            'title': 'el video más corto del mundo de geometry dash juego',
            'description': 'dura 5 segundos',
            'uploader': 'zuyohu',
            'uploader_id': 'zuyohu',
            'thumbnail': r're:https?://nas\d\.d\.tube/thumbnails/.+\.jpg',
            'duration': 5,
            'timestamp': 1787753757,
            'upload_date': '20260826',
            'view_count': int,
            'tags': ['randomvideos'],
        },
    }, {
        'url': 'https://d.tube/#!/v/broncnutz/x380jtr1',
        'skip': 'legacy Steemit-hosted videos are no longer available',
        'md5': '9f29088fa08d699a7565ee983f56a06e',
        'info_dict': {
            'id': 'x380jtr1',
            'ext': 'mp4',
            'title': 'Lefty 3-Rings is Back Baby!! NCAA Picks',
            'description': 'md5:60be222088183be3a42f196f34235776',
            'uploader_id': 'broncnutz',
            'upload_date': '20190107',
            'timestamp': 1546854054,
        },
    }]
    _NAS_HOSTS = ('https://nas1.d.tube', 'https://nas2.d.tube')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if self._match_valid_url(url).groupdict().get('uploader_id'):
            raise ExtractorError(
                'Legacy Steemit-hosted DTube videos are no longer available', expected=True)

        video = self._download_json(f'https://api.d.tube/videos/{video_id}', video_id)
        uuid = video['id']

        formats = []
        for host in self._NAS_HOSTS:
            m3u8_url = f'{host}/videos/{uuid}/master.m3u8'
            urlh = self._request_webpage(
                HEADRequest(m3u8_url), video_id, fatal=False, expected_status=404,
                note=f'Checking HLS CDN {host}')
            if not urlh or urlh.status != 200:
                continue
            formats = self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls')
            break

        return {
            'id': video_id,
            'formats': formats,
            **traverse_obj(video, {
                'title': ('title', {strip_or_none}),
                'description': ('description', {strip_or_none}),
                'thumbnail': ('thumbnail_url', {url_or_none}),
                'duration': ('duration', {int_or_none}),
                'view_count': ('views', {int_or_none}),
                'timestamp': ('created_at', {parse_iso8601}),
                'uploader': ('user', 'username', {str}),
                'uploader_id': ('user', 'username', {str}),
                'tags': ('communities', ..., 'name', {str}),
            }),
        }
