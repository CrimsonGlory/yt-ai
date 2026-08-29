from .common import InfoExtractor
from ..utils import urljoin


class YourUploadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:yourupload\.com/(?:watch|embed)|embed\.yourupload\.com)/(?P<id>[A-Za-z0-9]+)'
    _TESTS = [{
        'url': 'https://www.yourupload.com/watch/f0PN56si4NJy',
        'md5': '564f99fa69f2acf68ec640f7b7ed5307',
        'info_dict': {
            'id': 'f0PN56si4NJy',
            'ext': 'mp4',
            'title': 'Nature Beautiful short video 720p HD [360p].mp4',
            'thumbnail': '/images/default-preview.png',
        },
    }, {
        'url': 'http://yourupload.com/watch/14i14h',
        'skip': 'video gone',
        'md5': '5e2c63385454c557f97c4c4131a393cd',
        'info_dict': {
            'id': '14i14h',
            'ext': 'mp4',
            'title': 'BigBuckBunny_320x180.mp4',
            'thumbnail': r're:^https?://.*\.jpe?g',
        },
    }, {
        'url': 'http://www.yourupload.com/embed/14i14h',
        'only_matching': True,
    }, {
        'url': 'http://embed.yourupload.com/14i14h',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        embed_url = 'http://www.yourupload.com/embed/%s' % video_id

        webpage = self._download_webpage(embed_url, video_id)

        title = self._og_search_title(webpage)
        video_url = urljoin(embed_url, self._og_search_video_url(webpage))
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'http_headers': {
                'Referer': embed_url,
            },
        }
