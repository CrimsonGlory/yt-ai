from .anvato import AnvatoIE
from .common import InfoExtractor
from ..utils import ExtractorError, traverse_obj


class FOX4KCIE(InfoExtractor):
    IE_NAME = 'fox4kc'
    IE_DESC = 'FOX 4 Kansas City (WDAF-TV)'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?fox4kc\.com/
        (?:
            video/(?:[^/?#]+/)?(?P<id>\d+)
            |(?P<path>(?!wp-(?:json|admin|content|includes)/)(?:[^/?#]+/){1,}[^/?#]+)
        )
        /?(?:[?#]|$)
    '''
    _TESTS = [{
        'url': 'https://fox4kc.com/video/fbi-probe-into-kansas-city-mayor-pro-tem-expands-new-line-of-inquiry-revealed/11665956/',
        'md5': 'e61bd897e902d48c76ce1d5fc71ebf5f',
        'info_dict': {
            'id': '11665956',
            'ext': 'mp4',
            'title': 'FBI probe into Kansas City Mayor Pro Tem expands, new line of inquiry revealed',
            'description': 'md5:f5cba53ee4ff99b6da3abe48fdb7f845',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'timestamp': 1775171327,
            'upload_date': '20260402',
            'uploader': 'LIN',
            'duration': 232,
            'tags': ['news', 'local news'],
            'categories': ['News'],
        },
        'add_ie': [AnvatoIE.ie_key()],
    }, {
        'url': 'https://fox4kc.com/news/fbi-probe-into-kansas-city-mayor-pro-tem-expands-new-line-of-inquiry-revealed/',
        'info_dict': {
            'id': '11665956',
            'ext': 'mp4',
            'title': 'FBI probe into Kansas City Mayor Pro Tem expands, new line of inquiry revealed',
            'description': str,
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'timestamp': 1775171327,
            'upload_date': '20260402',
            'uploader': 'LIN',
            'duration': 232,
            'tags': ['news', 'local news'],
            'categories': ['News'],
        },
        'params': {'skip_download': True},
        'add_ie': [AnvatoIE.ie_key()],
    }, {
        'url': 'https://www.fox4kc.com/video/fbi-probe-into-kansas-city-mayor-pro-tem-expands-new-line-of-inquiry-revealed/11665956/',
        'only_matching': True,
    }]
    # Public Anvato access key from nxd_app (WDAF / FOX4KC)
    _ANVACK = '70X35QbVjgovptmVD0HwZI0w9lNQk2R1'

    def _anvato_result(self, video_id):
        return self.url_result(
            f'anvato:{self._ANVACK}:{video_id}',
            AnvatoIE, video_id=video_id, url_transparent=True)

    def _extract_anvato_id(self, post):
        video_id = traverse_obj(post, ('lead_media', 'id', {str}))
        if video_id and video_id.isdigit():
            return video_id
        for video_id in traverse_obj(post, ('content_blocks', ..., 'attrs', 'video', {str})) or []:
            if video_id.isdigit():
                return video_id

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        if video_id:
            return self._anvato_result(video_id)

        slug = mobj.group('path').rstrip('/').rsplit('/', 1)[-1]
        posts = self._download_json(
            'https://fox4kc.com/wp-json/wp/v2/posts', slug,
            query={
                'slug': slug,
                'per_page': '1',
                '_fields': 'lead_media,content_blocks',
            })
        video_id = self._extract_anvato_id(traverse_obj(posts, (0, {dict})))
        if not video_id:
            raise ExtractorError('No Anvato video found on this page', expected=True)
        return self._anvato_result(video_id)
