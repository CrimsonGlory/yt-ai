import base64
import re
import urllib.parse

from .common import InfoExtractor
from .jstream import JStreamIE
from ..utils import (
    js_to_json,
    traverse_obj,
)


class StreamCoPlatformIE(InfoExtractor):
    IE_NAME = 'streamco:platform'
    IE_DESC = 'J-Stream Equipmedia'
    _VALID_URL = r'https?://api\d+-platform\.stream\.co\.jp/apiservice/plt\d+/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://api01-platform.stream.co.jp/apiservice/plt3/MjY3Mg%3d%3d%23MTM2OA%3d%3d%23280%23168%230%233FE6A0D9E400%23MDoyOjc6YTpmOzEwOzEwOzEw%23',
        'md5': 'a18d0cf147173c2c401d428222f5e205',
        'info_dict': {
            'id': 'eqc288uvkg:1368',
            'ext': 'mp4',
            'title': '【ノンクレジットOP】TVアニメ『ぬきたしTHE ANIMATION』【青藍島ver.】',
            'duration': 90.0,
            'thumbnail': r're:https?://eqc288uvkg\.eq\.webcdn\.stream\.ne\.jp/.+\.jpg',
        },
        'add_ie': ['JStream'],
    }, {
        'url': 'https://api01-platform.stream.co.jp/apiservice/plt3/MTI3NA%3d%3d%23MzMzNw%3d%3d%23280%23168%230%2333E620506400%23OzEwOzEwOzEw%23',
        'only_matching': True,
    }, {
        'url': 'https://api01-platform.stream.co.jp/apiservice/plt3/NDg1%5cMTY0Ng%3d%3d%5c280%5c168%5c0%5c23E6FE50%5c',
        'only_matching': True,
    }]

    @staticmethod
    def _decode_mid(value):
        if not value:
            return None
        value = urllib.parse.unquote(value).strip()
        if re.fullmatch(r'\d+', value):
            return value
        padded = value + '=' * (-len(value) % 4)
        try:
            decoded = base64.b64decode(padded).decode()
        except (ValueError, TypeError):
            return None
        return decoded if re.fullmatch(r'\d+', decoded) else None

    def _real_extract(self, url):
        display_id = urllib.parse.unquote(self._match_id(url))
        webpage = self._download_webpage(url, display_id)
        player = self._search_json(
            r'(?:jstream_\w+\.)?PlayerFactoryIF\.create\s*\(', webpage,
            'player config', display_id, transform_source=js_to_json, fatal=False)

        host, publisher = self._search_regex(
            (r'(?P<publisher>[a-z0-9]+)\.eq\.webcdn\.stream\.ne\.jp/(?P<host>www\d+)/',
             r'ssl-cache\.stream\.ne\.jp/(?P<host>www\d+)/(?P<publisher>[a-z0-9]+)/'),
            f'{traverse_obj(player, "b") or ""}\n{webpage}',
            'JStream host/publisher', group=('host', 'publisher'))

        mid = self._decode_mid(traverse_obj(player, 'm'))
        if not mid:
            parts = [p for p in display_id.replace('\\', '#').split('#') if p]
            if len(parts) >= 2:
                mid = self._decode_mid(parts[1])
        if not mid:
            mid = self._decode_mid(self._search_regex(
                r'[?&]m=([A-Za-z0-9+/=%]+)', webpage, 'movie id'))

        return self.url_result(
            f'jstream:{host}:{publisher}:{mid}', JStreamIE, url_transparent=True)
