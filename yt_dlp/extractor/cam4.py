from .common import InfoExtractor
from ..utils import UserNotLive, traverse_obj, url_or_none


class CAM4IE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?cam4\.com/(?P<id>[a-zA-Z0-9_]+)'
    _TESTS = [{
        'url': 'https://www.cam4.com/cindy981',
        'info_dict': {
            'id': 'cindy981',
            'ext': 'mp4',
            'title': 're:^cindy981 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'age_limit': 18,
            'live_status': 'is_live',
            'thumbnail': 'https://snapshots.xcdnpro.com/thumbnails/cindy981',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'live rooms are ephemeral',
    }, {
        'url': 'https://www.cam4.com/foxynesss',
        'skip': 'video gone',
        'info_dict': {
            'id': 'foxynesss',
            'ext': 'mp4',
            'title': 're:^foxynesss [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'age_limit': 18,
            'live_status': 'is_live',
            'thumbnail': 'https://snapshots.xcdnpro.com/thumbnails/foxynesss',
        },
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        # Offline rooms return HTTP 204 with an empty body instead of JSON
        stream_info = self._download_json(
            f'https://www.cam4.com/rest/v1.0/profile/{channel_id}/streamInfo',
            channel_id, transform_source=lambda s: s or '{}',
            expected_status=204) or {}

        formats = []
        for m3u8_url in traverse_obj(stream_info, (('cdnURL', 'edgeURL'), {url_or_none})):
            formats = self._extract_m3u8_formats(
                m3u8_url, channel_id, 'mp4', m3u8_id='hls', live=True,
                fatal=False, errnote=False)
            if formats:
                break
        if not formats:
            raise UserNotLive(video_id=channel_id)

        return {
            'id': channel_id,
            'title': channel_id,
            'is_live': True,
            'age_limit': 18,
            'formats': formats,
            'thumbnail': f'https://snapshots.xcdnpro.com/thumbnails/{channel_id}',
        }
