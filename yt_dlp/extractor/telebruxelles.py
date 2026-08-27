import re

from .common import InfoExtractor


class TeleBruxellesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:telebruxelles|bx1)\.be/(?:[^/]+/)*(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'https://bx1.be/categories/reportages/des-controles-routiers-pour-former-les-policiers-de-demain/',
        'md5': '02703e712c6522dc4651de662e983888',
        'info_dict': {
            'id': '827167',
            'display_id': 'des-controles-routiers-pour-former-les-policiers-de-demain',
            'ext': 'mp4',
            'title': 'Des contrôles routiers pour former les policiers de demain',
            'description': 'md5:578851de0566e47d841b52f8d311a48b',
        },
    }, {
        'url': 'http://bx1.be/news/que-risque-lauteur-dune-fausse-alerte-a-la-bombe/',
        'skip': 'video gone',
        'md5': 'a2a67a5b1c3e8c9d33109b902f474fd9',
        'info_dict': {
            'id': '158856',
            'display_id': 'que-risque-lauteur-dune-fausse-alerte-a-la-bombe',
            'ext': 'mp4',
            'title': 'Que risque l’auteur d’une fausse alerte à la bombe ?',
            'description': 'md5:3cf8df235d44ebc5426373050840e466',
        },
    }, {
        'url': 'http://bx1.be/sport/futsal-schaerbeek-sincline-5-3-a-thulin/',
        'skip': 'video gone',
        'md5': 'dfe07ecc9c153ceba8582ac912687675',
        'info_dict': {
            'id': '158433',
            'display_id': 'futsal-schaerbeek-sincline-5-3-a-thulin',
            'ext': 'mp4',
            'title': 'Futsal : Schaerbeek s’incline 5-3 à Thulin',
            'description': 'md5:fd013f1488d5e2dceb9cebe39e2d569b',
        },
    }, {
        'url': 'http://bx1.be/emission/bxenf1-gastronomie/',
        'only_matching': True,
    }, {
        'url': 'https://bx1.be/berchem-sainte-agathe/personnel-carrefour-de-berchem-sainte-agathe-inquiet/',
        'only_matching': True,
    }, {
        'url': 'https://bx1.be/dernier-jt/',
        'only_matching': True,
    }, {
        # live stream
        'url': 'https://bx1.be/lives/direct-tv/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        article_id = self._html_search_regex(
            r'<article[^>]+\bid=["\']post-(\d+)', webpage, 'article ID', default=None)
        if not article_id:
            article_id = self._search_regex(
                r'\bpostid-(\d+)', webpage, 'article ID', default=None)
        video_id = article_id or display_id

        title = self._html_search_regex(
            r'<h1[^>]*>(.+?)</h1>', webpage, 'title',
            default=None) or self._og_search_title(webpage)
        description = self._og_search_description(webpage, default=None)

        hls_url = self._search_regex(
            r'\bdata-hls-source=(["\'])(?P<url>https?://.+?)\1',
            webpage, 'HLS URL', default=None, group='url')
        rtmp_url = self._search_regex(
            r'\bdata-rtmp-source=(["\'])(?P<url>r(?:tm|mt)ps?://.+?)\1',
            webpage, 'RTMP URL', default=None, group='url')
        if not rtmp_url:
            rtmp_url = self._html_search_regex(
                r'file["\']?\s*:\s*"(r(?:tm|mt)ps?://[^/]+/(?:vod/mp4:"\s*\+\s*"[^"]+"\s*\+\s*"\.mp4|stream/live))"',
                webpage, 'RTMP url', default=None)
            if rtmp_url:
                rtmp_url = re.sub(r'"\s*\+\s*"', '', rtmp_url)
        if rtmp_url:
            rtmp_url = re.sub(r'^rmtp', 'rtmp', rtmp_url)

        stream_url = hls_url or rtmp_url
        if not stream_url:
            self.raise_no_formats('Unable to extract stream URL', video_id=video_id, expected=True)

        is_live = '/stream/live' in stream_url
        if hls_url:
            formats = self._extract_m3u8_formats(
                hls_url, video_id, 'mp4',
                entry_protocol='m3u8' if is_live else 'm3u8_native',
                m3u8_id='hls', live=is_live)
        else:
            formats = self._extract_wowza_formats(
                rtmp_url, video_id,
                m3u8_entry_protocol='m3u8' if is_live else 'm3u8_native')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'formats': formats,
            'is_live': is_live,
        }
