from .common import InfoExtractor


class OutsideTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?outsidetv\.com/(?:[^/]+/)*?play/[a-zA-Z0-9]{8}/\d+/\d+/(?P<id>[a-zA-Z0-9]{8})'
    _TESTS = [{
        'url': 'http://www.outsidetv.com/category/snow/play/ZjQYboH6/1/10/Hdg0jukV/4',
        'md5': '7634ac8cee1fda71e3f425153b81f164',
        'info_dict': {
            'id': 'Hdg0jukV',
            'ext': 'mp4',
            'title': 'Home - Jackson Ep 1 | Arbor Snowboards',
            'description': 'md5:6adec8880757702b868d9d8d85855e50',
            'channel': 'snow',
            'duration': 281.0,
            'thumbnail': 'https://cdn.jwplayer.com/v2/media/Hdg0jukV/poster.jpg?width=720',
            'timestamp': 1545742800,
            'upload_date': '20181225',
        },
        'skip': 'site gone: outsidetv.com redirects to login-walled watch.outsideonline.com; old play URLs 522',
    }, {
        'url': 'http://www.outsidetv.com/home/play/ZjQYboH6/1/10/Hdg0jukV/4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        jw_media_id = self._match_id(url)
        return self.url_result(
            'jwplatform:' + jw_media_id, 'JWPlatform', jw_media_id)
