from .common import InfoExtractor
from .threeqsdn import ThreeQSDNIE


class NozIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?noz\.de/(?:[^/?#]+/)*video(?:/video)?/(?:[^/?#]*-)?(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.noz.de/lokales/dissen/video/erntetechnik-fuer-die-landwirtschaft-claas-in-dissen-50202654',
        'md5': '24fab78b0203b8fce93a4a81a7d01589',
        'info_dict': {
            'id': 'a4aa1981-1815-4ba3-8378-01fb5272bb7f',
            'ext': 'mp4',
            'title': 'Erntetechnik für die Landwirtschaft: So produziert Claas in Dissen',
            'description': 'md5:e02b8a81ca53cbd0b845aef2200e666f',
            'display_id': '50202654',
            'duration': 496.02,
            'thumbnail': r're:https?://.+\.jpg',
            'timestamp': 1773835776,
            'upload_date': '20260318',
            'is_live': False,
        },
        'add_ie': ['ThreeQSDN'],
        'params': {
            'format': 'best[protocol=https][ext=mp4]/best',
        },
    }, {
        'url': 'http://www.noz.de/video/25151/32-Deutschland-gewinnt-Badminton-Lnderspiel-in-Melle',
        'skip': 'old /video/<id>/ URLs redirect to unrelated articles',
        'info_dict': {
            'id': '25151',
            'ext': 'mp4',
            'duration': 215,
            'title': '3:2 - Deutschland gewinnt Badminton-Länderspiel in Melle',
            'description': 'Vor rund 370 Zuschauern gewinnt die deutsche Badminton-Nationalmannschaft am Donnerstag ein EM-Vorbereitungsspiel gegen Frankreich in Melle. Video Moritz Frankenberg.',
            'thumbnail': r're:^http://.*\.jpg',
        },
    }, {
        'url': 'https://www.noz.de/video/video/ueber-den-wolken-mit-dem-zeppelin-im-luftschiff-ueber-hannover-47772813',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        sdn_id = self._search_regex(
            r'threeQdataId["\']?\s*:\s*["\']([0-9a-f-]{36})["\']',
            webpage, '3Q data id', default=None) or self._search_regex(
            r'playout\.3qsdn\.com/embed/([0-9a-f-]{36})', webpage, '3Q embed id')
        return self.url_result(
            f'https://playout.3qsdn.com/{sdn_id}', ThreeQSDNIE, sdn_id,
            url_transparent=True, display_id=video_id)
