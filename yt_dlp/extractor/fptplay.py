import base64
import hashlib
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    join_nonempty,
    traverse_obj,
    url_or_none,
)


class FptplayIE(InfoExtractor):
    _VALID_URL = r'https?://fptplay\.vn/xem-video/(?:[^/]+-)?(?P<id>\w+)(?:/tap-(?P<episode>\d+)?/?(?:[?#]|$)|)'
    _GEO_COUNTRIES = ['VN']
    IE_NAME = 'fptplay'
    IE_DESC = 'fptplay.vn'
    _API_BASE = 'https://api.fptplay.net'
    _API_PREFIX = '/api/v7.1_w'
    _ST_SECRET = '6ea6d2a4e2d3a4bd5e275401aa086d'
    _TESTS = [{
        'url': 'https://fptplay.vn/xem-video/ngu-dinh-dao-6a6955e6ee495ba332e1e6fb',
        'info_dict': {
            'id': '6a6955e6ee495ba332e1e6fb',
            'ext': 'mp4',
            'title': 'Ngự Đình Dao',
        },
        'skip': 'geo-restricted to Vietnam; stream/content APIs return HTTP 410 outside VN (X-Forwarded-For is ignored)',
    }, {
        'url': 'https://fptplay.vn/xem-video/nhan-duyen-dai-nhan-xin-dung-buoc-621a123016f369ebbde55945',
        'md5': 'ca0ee9bc63446c0c3e9a90186f7d6b33',
        'info_dict': {
            'id': '621a123016f369ebbde55945',
            'ext': 'mp4',
            'title': 'Nhân Duyên Đại Nhân Xin Dừng Bước - Tập 1A',
            'description': 'md5:23cf7d1ce0ade8e21e76ae482e6a8c6c',
        },
        'skip': 'video gone',
    }, {
        'url': 'https://fptplay.vn/xem-video/ma-toi-la-dai-gia-61f3aa8a6b3b1d2e73c60eb5/tap-3',
        'md5': 'b35be968c909b3e4e1e20ca45dd261b1',
        'info_dict': {
            'id': '61f3aa8a6b3b1d2e73c60eb5',
            'ext': 'mp4',
            'title': 'Má Tôi Là Đại Gia - Tập 3',
            'description': 'md5:ff8ba62fb6e98ef8875c42edff641d1c',
        },
        'skip': 'video gone',
    }, {
        'url': 'https://fptplay.vn/xem-video/lap-toi-do-giam-under-the-skin-6222d9684ec7230fa6e627a2/tap-4',
        'md5': 'bcb06c55ec14786d7d4eda07fa1ccbb9',
        'info_dict': {
            'id': '6222d9684ec7230fa6e627a2',
            'ext': 'mp4',
            'title': 'Lạp Tội Đồ Giám - Tập 2B',
            'description': 'md5:e5a47e9d35fbf7e9479ca8a77204908b',
        },
        'skip': 'video gone',
    }, {
        'url': 'https://fptplay.vn/xem-video/nha-co-chuyen-hi-alls-well-ends-well-1997-6218995f6af792ee370459f0',
        'only_matching': True,
    }]

    def _signed_api_url(self, api_path):
        path = f'{self._API_PREFIX}/{api_path.lstrip("/")}'
        timestamp = int(time.time()) + 3600
        digest = hashlib.md5(
            f'{self._ST_SECRET}{timestamp}{path}'.encode()).hexdigest()
        st_token = base64.b64encode(bytes.fromhex(digest)).decode().replace(
            '+', '-').replace('/', '_').replace('=', '')
        return f'{self._API_BASE}{path}?{urllib.parse.urlencode({"st": st_token, "e": timestamp})}'

    def _call_api(self, api_path, video_id, note):
        return self._download_json(
            self._signed_api_url(api_path), video_id, note,
            headers={
                'Origin': 'https://fptplay.vn',
                'Referer': 'https://fptplay.vn/',
            },
            expected_status=(403, 406, 410))

    def _real_extract(self, url):
        video_id, slug_episode = self._match_valid_url(url).group('id', 'episode')
        episode = int(slug_episode) - 1 if slug_episode else 0

        vod = self._call_api(
            f'content/vod/{video_id}', video_id, 'Downloading VOD metadata')
        vod_data = traverse_obj(vod, ('data', {dict})) or {}
        if str(traverse_obj(vod, 'status')) != '1':
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        stream = self._call_api(
            f'stream/vod/{video_id}/{episode}/adaptive_bitrate',
            video_id, 'Downloading stream API JSON')
        stream_url = traverse_obj(stream, ('data', 'url', {url_or_none}))
        if not stream_url:
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            stream_url, video_id, 'mp4')
        title = traverse_obj(vod_data, 'title', 'title_vie', 'title_origin', 'name')
        episode_title = None
        if slug_episode:
            episode_title = traverse_obj(
                vod_data, ('episodes', episode, 'title')) or f'Tập {slug_episode}'

        return {
            'id': video_id,
            'title': join_nonempty(title, episode_title, delim=' - '),
            'description': traverse_obj(vod_data, 'description'),
            'thumbnail': traverse_obj(vod_data, 'thumb', 'thumbnail', 'poster'),
            'formats': formats,
            'subtitles': subtitles,
        }
