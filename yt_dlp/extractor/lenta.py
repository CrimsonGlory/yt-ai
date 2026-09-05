import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class LentaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lenta\.ru/[^/]+/\d+/\d+/\d+/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://lenta.ru/video/2025/04/03/spasavshiesya-ot-ognya-rossiyane-vyprygnuli-iz-okna-zhilogo-doma-i-popali-na-video/',
        'info_dict': {
            'id': '2564368',
            'ext': 'mp4',
            'title': 'В Казани пара выпрыгнула из окна во время пожара',
            'description': 'md5:6618d01b53456e7f52d6106597d43bff',
            'display_id': 'spasavshiesya-ot-ognya-rossiyane-vyprygnuli-iz-okna-zhilogo-doma-i-popali-na-video',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'duration': 4.0,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://lenta.ru/news/2018/03/22/savshenko_go/',
        'skip': 'video gone',
        'info_dict': {
            'id': '964400',
            'ext': 'mp4',
            'title': 'Надежду Савченко задержали',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 61,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # EaglePlatform iframe embed
        'url': 'http://lenta.ru/news/2015/03/06/navalny/',
        'skip': 'video gone',
        'info_dict': {
            'id': '227304',
            'ext': 'mp4',
            'title': 'Навальный вышел на свободу',
            'description': 'md5:d97861ac9ae77377f3f20eaf9d04b4f5',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 87,
            'view_count': int,
            'age_limit': 0,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _extract_rambler(self, url, display_id, webpage):
        rambler_id = self._search_regex(
            r'data-vid=["\']((?:record::)?[0-9a-fA-F-]+)["\']',
            webpage, 'rambler video id', default=None)
        if not rambler_id:
            return None

        api_params = {
            'checkReferrerCount': True,
            'referrer': url,
        }
        if rambler_id.startswith('record::') or not rambler_id.isdigit():
            api_params['uuid'] = (
                rambler_id if rambler_id.startswith('record::')
                else f'record::{rambler_id}')
        else:
            api_params['id'] = int(rambler_id)

        template_id = self._search_regex(
            r'data-template=["\'](\d+)["\']', webpage, 'player template id', default=None)
        if template_id:
            api_params['playerTemplateId'] = int(template_id)

        player_data = self._download_json(
            'https://api.vp.rambler.ru/api/v3/records/getPlayerData',
            display_id, query={
                'params': json.dumps(api_params, separators=(',', ':')),
            }, fatal=False)
        playlist = traverse_obj(player_data, ('result', 'playList', {dict})) or {}
        m3u8_url = playlist.get('source') or playlist.get('directSource') or playlist.get('old')
        if not m3u8_url:
            return None

        video_id = str(playlist.get('id') or rambler_id)
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', m3u8_id='hls')
        info = {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'description': self._og_search_description(webpage, default=None) or None,
            **traverse_obj(playlist, {
                'title': ('title', {str}),
                'thumbnail': (('customScreenshotOrig', 'snapshot'), {url_or_none}, any),
                'duration': ('duration', {float_or_none(scale=1000)}),
            }),
        }
        info['title'] = info.get('title') or self._og_search_title(webpage, default=display_id)
        return info

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        rambler = self._extract_rambler(url, display_id, webpage)
        if rambler:
            return rambler

        iframe = self._search_regex(
            r'<iframe[^>]+src=["\']([^"\']+)["\']', webpage, 'iframe', default=None)
        if iframe:
            return self.url_result(iframe)

        html5 = self._parse_html5_media_entries(url, webpage, display_id)
        if html5:
            info = html5[0]
            info.update({
                'id': display_id,
                'title': self._og_search_title(webpage, default=display_id),
                'thumbnail': info.get('thumbnail') or self._og_search_thumbnail(webpage),
                'description': self._og_search_description(webpage, default=None) or None,
            })
            return info

        raise ExtractorError('No video found', expected=True)
