from .anvato import AnvatoIE
from .common import InfoExtractor
from ..utils import ExtractorError, traverse_obj


class NewsNationIE(InfoExtractor):
    IE_NAME = 'newsnation'
    IE_DESC = 'NewsNation'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?newsnationnow\.com/
        (?:
            video/(?:[^/?#]+/)?(?P<id>\d+)
            |nxs-video/vid-anvato-(?P<nxs_id>[^/?#]+)
            |(?P<path>(?!wp-(?:json|admin|content|includes)/)(?:[^/?#]+/)*[^/?#]+)
        )
        /?(?:[?#]|$)
    '''
    _TESTS = [
        {
            'url': 'https://www.newsnationnow.com/video/trump-seals-new-deals-to-lower-drug-prices-for-americans-newsnation-live/12122908/',
            'md5': 'b29cb1c85e2ea12d572c498484be4dc2',
            'info_dict': {
                'id': '12122908',
                'ext': 'mp4',
                'title': 'Trump seals new deals to lower drug prices for Americans | NewsNation Live',
                'description': str,
                'thumbnail': r're:https?://.+\.(?:jpg|png)',
                'timestamp': 1788208854,
                'upload_date': '20260831',
                'uploader': 'LIN',
                'duration': 133,
                'tags': ['WatchNewsNationNow', 'trump', 'drug prices', 'americans'],
                'categories': ['NewsNation\\NewsNation Live', 'Status\\Published', 'Genre\\Politics', 'Genre\\Health'],
            },
            'add_ie': [AnvatoIE.ie_key()],
        },
        {
            'url': 'https://www.newsnationnow.com/crime/times-square-police-involved-shooting/',
            'info_dict': {
                'id': '12122986',
                'ext': 'mp4',
                'title': 'Police-involved shooting in Times Square, sources say',
                'description': str,
                'thumbnail': r're:https?://.+\.(?:jpg|png)',
                'timestamp': 1788210202,
                'upload_date': '20260831',
                'uploader': 'LIN',
                'duration': 20,
                'tags': list,
                'categories': list,
            },
            'params': {'skip_download': True},
            'add_ie': [AnvatoIE.ie_key()],
        },
        {
            'url': 'https://newsnationnow.com/video/trump-seals-new-deals-to-lower-drug-prices-for-americans-newsnation-live/12122908/',
            'only_matching': True,
        },
        {
            'url': 'https://www.newsnationnow.com/nxs-video/vid-anvato-12122908/',
            'only_matching': True,
        },
        {
            'url': 'https://www.newsnationnow.com/news-nation-live/',
            'only_matching': True,
        },
    ]
    # Public Anvato access key from nxd_app TVE settings
    _ANVACK = 'GNLYj4WPEPgKWUvG6mTVNFejokMyVq3x'
    _API_BASE = 'https://www.newsnationnow.com/wp-json/wp/v2'

    def _anvato_result(self, video_id):
        if not video_id.isdigit():
            self.raise_login_required('This NewsNation livestream requires a TV provider login', method=None)
        return self.url_result(f'anvato:{self._ANVACK}:{video_id}', AnvatoIE, video_id=video_id, url_transparent=True)

    def _extract_anvato_id(self, post):
        video_id = traverse_obj(post, ('lead_media', 'id', {str}))
        if video_id:
            return video_id
        for video_id in traverse_obj(post, ('content_blocks', ..., 'attrs', 'video', {str})) or []:
            if video_id:
                return video_id

    def _download_post(self, slug):
        query = {
            'slug': slug,
            'per_page': '1',
            '_fields': 'lead_media,content_blocks',
        }
        for endpoint in ('posts', 'pages'):
            entries = self._download_json(
                f'{self._API_BASE}/{endpoint}', slug, f'Downloading {endpoint} JSON', query=query, fatal=False,
            )
            post = traverse_obj(entries, (0, {dict}))
            if post:
                return post

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id') or mobj.group('nxs_id')
        if video_id:
            return self._anvato_result(video_id)

        slug = mobj.group('path').rstrip('/').rsplit('/', 1)[-1]
        video_id = self._extract_anvato_id(self._download_post(slug))
        if not video_id:
            raise ExtractorError('No Anvato video found on this page', expected=True)
        return self._anvato_result(video_id)
