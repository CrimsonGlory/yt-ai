import hashlib
import json
import time

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AliExpressLiveIE(InfoExtractor):
    _VALID_URL = r'https?://live\.aliexpress\.com/live/(?P<id>\d+)'
    _API_APP_KEY = '12574478'
    _TESTS = [{
        'url': 'https://live.aliexpress.com/live/2800002704436634',
        'md5': '61ecdc0bab941e2edc487e6ab6c911ff',
        'info_dict': {
            'id': '2800002704436634',
            'ext': 'mp4',
            'title': 'CASIMA7.22',
            'thumbnail': r're:https?://.+',
            'uploader': 'Shop1938280 Store',
            'timestamp': 1500717600,
            'upload_date': '20170722',
        },
    }]

    def _call_mtop(self, api, video_id, data, version='1.0'):
        data_str = json.dumps(data, separators=(',', ':'))
        url = f'https://acs.aliexpress.com/h5/{api}/{version}/'
        headers = {
            'Origin': 'https://www.aliexpress.com',
            'Referer': 'https://www.aliexpress.com/',
        }

        def query():
            timestamp = str(int(time.time() * 1000))
            token = ''
            for cookie in self.cookiejar:
                if cookie.name == '_m_h5_tk':
                    token = cookie.value.partition('_')[0]
                    break
            sign = hashlib.md5(
                f'{token}&{timestamp}&{self._API_APP_KEY}&{data_str}'.encode()).hexdigest()
            return {
                'jsv': '2.7.2',
                'appKey': self._API_APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': api,
                'v': version,
                'type': 'originaljson',
                'dataType': 'json',
                'data': data_str,
            }

        result = self._download_json(
            url, video_id, 'Fetching mtop token', query=query(),
            headers=headers, fatal=False)
        if traverse_obj(result, ('data', {dict})):
            return result
        return self._download_json(url, video_id, query=query(), headers=headers)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = traverse_obj(self._call_mtop(
            'mtop.aliexpress.ugc.live.detail', video_id, {'liveId': video_id}),
            ('data', {dict})) or {}

        formats = []
        reply_url = traverse_obj(data, ('replyStreamUrl', {url_or_none}))
        if reply_url:
            formats.extend(self._extract_m3u8_formats(
                reply_url, video_id, 'mp4', m3u8_id='hls'))
        else:
            for quality, stream_url in (traverse_obj(data, ('pullStreamUrl', {dict})) or {}).items():
                if url_or_none(stream_url) and '.m3u8' in stream_url:
                    formats.extend(self._extract_m3u8_formats(
                        stream_url, video_id, 'mp4', m3u8_id=f'hls-{quality}', fatal=False))

        if not formats:
            self.raise_no_formats('No stream URL available', video_id=video_id, expected=True)

        return {
            'id': video_id,
            'formats': formats,
            **traverse_obj(data, {
                'title': ('title', {strip_or_none}),
                'thumbnail': (('showCoverUrl', 'coverName'), {url_or_none}, any),
                'uploader': ('followBar', 'name', {str}),
                'timestamp': ('startTime', {lambda x: float_or_none(x, scale=1000)}),
            }),
        }
