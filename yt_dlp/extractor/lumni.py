from .francetv import FranceTVBaseInfoExtractor


class LumniIE(FranceTVBaseInfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lumni\.fr/video/(?P<id>[\w-]+)'
    _TESTS = [{
        # Worldwide (_monde) VOD; many Lumni titles are France-only
        'url': 'https://www.lumni.fr/video/3-infos-sur-lia',
        'md5': 'cbcad5c6c9c9c82cb703679ed4cea2ca',
        'info_dict': {
            'id': '766c3f67-0caf-466f-94a7-455b919a4932',
            'ext': 'mp4',
            'title': "Les sciences de Nicolas Chateauneuf - 3 infos sur l'IA",
            'duration': 104,
            'timestamp': 1761920176,
            'upload_date': '20251031',
        },
    }, {
        'url': 'https://www.lumni.fr/video/l-homme-et-son-environnement-dans-la-revolution-industrielle',
        'skip': 'video gone',
        'md5': '960e8240c4f2c7a20854503a71e52f5e',
        'info_dict': {
            'id': 'd2b9a4e5-a526-495b-866c-ab72737e3645',
            'ext': 'mp4',
            'title': "L'homme et son environnement dans la révolution industrielle - L'ère de l'homme",
            'thumbnail': 'https://assets.webservices.francetelevisions.fr/v1/assets/images/a7/17/9f/a7179f5f-63a5-4e11-8d4d-012ab942d905.jpg',
            'duration': 230,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._html_search_regex(
            r'<div[^>]+data-factoryid\s*=\s*["\']([^"\']+)', webpage, 'video id')
        return self._make_url_result(video_id, url=url)
