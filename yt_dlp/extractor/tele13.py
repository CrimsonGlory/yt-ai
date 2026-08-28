from .common import InfoExtractor
from .rudovideo import RudoVideoIE
from .youtube import YoutubeIE
from ..utils import ExtractorError


class Tele13IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?t13\.cl/videos(?:/[^/]+)+/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.t13.cl/videos/politica/el-gobierno-va-dejar-morir-reforma-constitucional-senador-bianchi-por-agenda-27-8-2026',
        'md5': 'e0932483b08a6f78a89c9f8acbb3bbb1',
        'info_dict': {
            'id': 'bWZJm4',
            'ext': 'mp4',
            'title': 'Entrevista Karim Bianchi',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'creators': ['T13.cl'],
        },
        'add_ie': ['RudoVideo'],
    }, {
        'url': 'http://www.t13.cl/videos/actualidad/el-circulo-de-hierro-de-michelle-bachelet-en-su-regreso-a-la-moneda',
        'md5': '4cb1fa38adcad8fea88487a078831755',
        'info_dict': {
            'id': 'el-circulo-de-hierro-de-michelle-bachelet-en-su-regreso-a-la-moneda',
            'ext': 'mp4',
            'title': 'El círculo de hierro de Michelle Bachelet en su regreso a La Moneda',
        },
        'skip': 'video gone',
    }, {
        'url': 'http://www.t13.cl/videos/mundo/tendencias/video-captan-misteriosa-bola-fuego-cielos-bangkok',
        'md5': '867adf6a3b3fef932c68a71d70b70946',
        'info_dict': {
            'id': 'rOoKv2OMpOw',
            'ext': 'mp4',
            'title': 'Shooting star seen on 7-Sep-2015',
            'description': 'md5:7292ff2a34b2f673da77da222ae77e1e',
            'uploader': 'Porjai Jaturongkhakun',
            'upload_date': '20150906',
            'uploader_id': 'UCnLY_3ezwNcDSC_Wc6suZxw',
        },
        'add_ie': ['Youtube'],
        'skip': 'Youtube embed; live test uses native rudo.video',
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        # Current T13 VOD pages inject a rudo.video player (JWPlayer is gone).
        rudo_url = self._search_regex(
            r'(https?://rudo\.video/(?:vod|podcast|live)/[0-9a-zA-Z]+)',
            webpage, 'rudo url', default=None)
        if rudo_url:
            return self.url_result(rudo_url, RudoVideoIE)

        yt_id = self._search_regex(
            r'youtube(?:-nocookie)?\.com/embed/(?P<id>[\w-]{11})',
            webpage, 'youtube id', default=None)
        if yt_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={yt_id}', YoutubeIE, yt_id)

        raise ExtractorError('No video embed found', expected=True)
