import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class GazetaIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?gazeta\.ru/(?:[^/?#]+/)+(?P<id>[A-Za-z0-9-_.]+)\.s?html'
    _TESTS = [{
        'url': 'https://www.gazeta.ru/politics/2026/08/27/23457307.shtml',
        'md5': '9e09f306ad96fe86dbb49deb76afef6e',
        'info_dict': {
            'id': '2826938',
            'ext': 'mp4',
            'title': 'Герасимов проверил ход выполнения боевых задач «Южной» группировки войск',
            'description': 'md5:6c25be8918a72931dccd64ca8289eb24',
            'display_id': '23457307',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'duration': 256.0,
        },
    }, {
        'url': 'http://www.gazeta.ru/video/main/zadaite_vopros_vladislavu_yurevichu.shtml',
        'md5': 'd49c9bdc6e5a7888f27475dc215ee789',
        'info_dict': {
            'id': '205566',
            'ext': 'mp4',
            'title': '«70–80 процентов гражданских в Донецке на грани голода»',
            'description': 'md5:38617526050bd17b234728e7f9620a71',
            'thumbnail': r're:^https?://.*\.jpg',
        },
        'skip': 'video gone',
    }, {
        'url': 'http://www.gazeta.ru/lifestyle/video/2015/03/08/master-klass_krasivoi_byt._delaem_vesennii_makiyazh.shtml',
        'only_matching': True,
    }, {
        'url': 'http://www.gazeta.ru/video/main/main/2015/06/22/platit_ili_ne_platit_po_isku_yukosa.shtml',
        'md5': '37f19f78355eb2f4256ee1688359f24c',
        'info_dict': {
            'id': '252048',
            'ext': 'mp4',
            'title': '"Если по иску ЮКОСа придется платить, это будет большой удар по бюджету"',
        },
        'skip': 'video gone',
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        self._set_cookie('.gazeta.ru', 'unity_pause_sso', '1')
        webpage = self._download_webpage(url, display_id)

        rambler_id = self._search_regex(
            r'data-id=["\'](record::[0-9a-fA-F-]+)["\']',
            webpage, 'rambler record id', default=None)
        if not rambler_id:
            raise ExtractorError('No Rambler video found', expected=True)

        player_data = self._download_json(
            'https://api.vp.rambler.ru/api/v3/records/getPlayerData',
            display_id, query={
                'params': json.dumps({
                    'checkReferrerCount': True,
                    'referrer': url,
                    'uuid': rambler_id,
                }, separators=(',', ':')),
            })

        playlist = traverse_obj(player_data, ('result', 'playList', {dict})) or {}
        video_id = str(playlist.get('id') or rambler_id)
        m3u8_url = playlist.get('source') or playlist.get('directSource') or playlist.get('old')
        if not m3u8_url:
            raise ExtractorError('No video source found', expected=True)

        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', m3u8_id='hls')

        info = {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'description': self._og_search_description(webpage, default=None),
            **traverse_obj(playlist, {
                'title': ('title', {str}),
                'thumbnail': (('customScreenshotOrig', 'snapshot'), {url_or_none}, any),
                'duration': ('duration', {float_or_none(scale=1000)}),
            }),
        }
        info['title'] = info.get('title') or self._og_search_title(webpage)
        return info
