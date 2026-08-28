from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    url_or_none,
)


class PeerTVIE(InfoExtractor):
    IE_NAME = 'peer.tv'
    _VALID_URL = [
        r'https?://(?:www\.)?peer\.tv/(?:de|it|en)/video/(?P<id>[\w-]+)',
        r'https?://(?:www\.)?peer\.tv/(?:de|it|en)/(?P<id>\d+)',
    ]
    _TESTS = [{
        'url': 'https://www.peer.tv/de/video/die-geislergruppe-aus-der-luft',
        'md5': 'ee402a51e0ded4430821fc5c9138f54c',
        'info_dict': {
            'id': '825',
            'ext': 'mp4',
            'title': 'Die Geislergruppe aus der Luft',
            'description': 'md5:a8759dfa8f590d4c61a959b2e6d7a08f',
            'duration': 63,
            'timestamp': 1565164627,
            'upload_date': '20190807',
            'thumbnail': 'https://player.peer.tv/img/thumbs/903c7ec4d523fafec880db965296f766/hd-preview-n.jpg',
        },
    }, {
        'url': 'https://www.peer.tv/de/841',
        'only_matching': True,
    }, {
        'url': 'https://www.peer.tv/it/404',
        'only_matching': True,
    }, {
        'url': 'https://www.peer.tv/it/video/cascate-di-ghiaccio-in-val-gardena',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        info = self._search_json_ld(webpage, display_id, expected_type='VideoObject')
        video_url = url_or_none(info.get('url'))
        if not video_url:
            raise ExtractorError('Unable to extract video URL', expected=True)

        video_id = self._search_regex(
            r'/public-mp4/(\d+)-', video_url, 'numeric id', default=display_id)

        return {
            **info,
            'id': video_id,
            'url': video_url,
            'title': info.get('title') or self._og_search_title(webpage),
            'description': info.get('description') or self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
