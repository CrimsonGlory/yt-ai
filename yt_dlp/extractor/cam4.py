from .common import InfoExtractor
from ..utils import UserNotLive, traverse_obj, url_or_none


class CAM4IE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?cam4\.com/(?P<id>[a-zA-Z0-9_]+)'
    _TESTS = [{
        'url': 'https://www.cam4.com/anal_queen',
        'info_dict': {
            'id': 'anal_queen',
            'ext': 'mp4',
            'title': 're:^anal_queen [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'age_limit': 18,
            'live_status': 'is_live',
            'thumbnail': 'https://snapshots.xcdnpro.com/thumbnails/anal_queen',
        },
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
        m3u8_playlist = traverse_obj(
            self._download_json(
                f'https://www.cam4.com/rest/v1.0/profile/{channel_id}/streamInfo',
                channel_id),
            ('cdnURL', {url_or_none}))
        if not m3u8_playlist:
            raise UserNotLive(video_id=channel_id)

        formats = self._extract_m3u8_formats(m3u8_playlist, channel_id, 'mp4', m3u8_id='hls', live=True)

        return {
            'id': channel_id,
            'title': channel_id,
            'is_live': True,
            'age_limit': 18,
            'formats': formats,
            'thumbnail': f'https://snapshots.xcdnpro.com/thumbnails/{channel_id}',
        }
