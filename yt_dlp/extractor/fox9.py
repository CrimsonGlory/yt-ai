from .common import InfoExtractor


class FOX9IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fox9\.com/video/(?P<id>[\w-]+)'
    _WEB_FALLBACK = True
    _TESTS = [{
        'url': 'https://www.fox9.com/video/fmc-do4c877slj73obx8',
        'info_dict': {
            'id': 'fmc-do4c877slj73obx8',
            'ext': 'mp4',
            'title': '87 cars broken into in 1 night in Minneapolis',
            'description': r're:There were 87 cars',
            'thumbnail': r're:https://static-media\.fox\.com/.+',
            'timestamp': 1787452130,
            'upload_date': '20260823',
        },
        'expected_warnings': [r'webpage media fallback'],
        'skip': 'FOX9 m3u8 playlists expire quickly',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if video_id.isdigit():
            return self.url_result(
                'anvato:anvato_epfox_app_web_prod_b3373168e12f423f41504f207000188daf88251b:' + video_id,
                'Anvato', video_id)
        return self._extract_webpage_media(url)


class FOX9NewsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fox9\.com/news/(?P<id>[^/?&#]+)'
    _TEST = {
        'url': 'https://www.fox9.com/news/black-bear-in-tree-draws-crowd-in-downtown-duluth-minnesota',
        'skip': 'extractor broken',
        'md5': 'd6e1b2572c3bab8a849c9103615dd243',
        'info_dict': {
            'id': '314473',
            'ext': 'mp4',
            'title': 'Bear climbs tree in downtown Duluth',
            'description': 'md5:6a36bfb5073a411758a752455408ac90',
            'duration': 51,
            'timestamp': 1478123580,
            'upload_date': '20161102',
            'uploader': 'EPFOX',
            'categories': ['News', 'Sports'],
            'tags': ['news', 'video'],
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        anvato_id = self._search_regex(
            r'anvatoId\s*:\s*[\'"](\d+)', webpage, 'anvato id')
        return self.url_result('https://www.fox9.com/video/' + anvato_id, 'FOX9')
