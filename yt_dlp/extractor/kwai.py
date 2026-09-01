from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class KwaiIE(InfoExtractor):
    IE_DESC = 'Kwai'
    _VALID_URL = (
        r'https?://s\.kw\.ai/p/(?P<id>[\w-]+)',
        r'https?://(?:www\.|m\.)?kwai\.com/(?:@[^/?#]+/)?(?:video|photo|picture)/(?P<id>\d+)',
        r'https?://(?:www\.|m\.)?kwai\.com/photo/\d+/(?P<id>\d+)',
    )
    _MOBILE_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    }
    _TESTS = [
        {
            'url': 'https://www.kwai.com/@Massaki/video/5188578355028744539',
            'md5': '539263e6c292bcdba06867207b1962eb',
            'info_dict': {
                'id': '5188578355028744539',
                'ext': 'mp4',
                'title': 'Ele é nutella ou não? 🤣#rimas#freestyle#rap#hiphop#improviso',
                'description': 'Ele é nutella ou não? 🤣#rimas#freestyle#rap#hiphop#improviso',
                'thumbnail': r're:https?://.+\.(?:webp|jpg|jpeg|png)',
                'duration': 91,
                'timestamp': 1787465805,
                'upload_date': '20260823',
                'uploader': 'Massaki',
                'uploader_id': '3xkkhmxm8thb3pa',
                'uploader_url': 'https://www.kwai.com/@Massaki',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
                'track': 'Áudio original criado por Massaki',
                'artist': 'Massaki',
                'artists': ['Massaki'],
                'width': 720,
                'height': 1280,
            },
        },
        {
            'url': 'https://s.kw.ai/p/bvCMz94h',
            'only_matching': True,
        },
        {
            'url': 'https://s.kw.ai/p/zL3z89CB',
            'only_matching': True,
        },
        {
            'url': 'https://m.kwai.com/@Massaki/video/5188578355028744539',
            'only_matching': True,
        },
        {
            'url': 'https://m.kwai.com/photo/150001174877117/5218696167009868754',
            'only_matching': True,
        },
    ]

    def _extract_video_ld(self, webpage, video_id):
        for ld in self._yield_json_ld(webpage, video_id, default=[]):
            if traverse_obj(ld, '@type') == 'VideoObject' and url_or_none(ld.get('contentUrl')):
                return ld
        return (
            traverse_obj(
                self._search_nuxt_data(webpage, video_id, fatal=False),
                (
                    'seoData',
                    lambda _, v: v.get('id') == 'VideoObject',
                    'innerHTML',
                    {dict},
                    lambda _, v: url_or_none(v.get('contentUrl')),
                    any,
                ),
            )
            or {}
        )

    def _real_extract(self, url):
        display_id = self._match_id(url)
        # s.kw.ai share links redirect to the app store on a mobile UA.
        headers = None if 's.kw.ai' in url else self._MOBILE_HEADERS
        webpage, urlh = self._download_webpage_handle(url, display_id, headers=headers)
        video_ld = self._extract_video_ld(webpage, display_id)

        if not url_or_none(video_ld.get('contentUrl')):
            webpage = self._download_webpage(
                urlh.url, display_id, 'Downloading mobile webpage', headers=self._MOBILE_HEADERS,
            )
            video_ld = self._extract_video_ld(webpage, display_id)

        video_url = url_or_none(video_ld.get('contentUrl'))
        if not video_url:
            self.raise_no_formats(
                'No public video found; it may be private, deleted, or app-only', expected=True, video_id=display_id,
            )

        video_id = (
            display_id
            if display_id.isdigit()
            else self._search_regex(
                r'/(?:video|photo|picture)/(\d+)',
                traverse_obj(video_ld, ('url', {str})) or urlh.url,
                'photo id',
                default=display_id,
            )
        )

        info = self._json_ld(video_ld, video_id, fatal=False, expected_type='VideoObject')
        caption = traverse_obj(video_ld, ('description', {str}))
        if caption:
            info['title'] = caption
            info.setdefault('description', caption)

        return {
            'id': video_id,
            'ext': 'mp4',
            **info,
            'url': video_url,
            **traverse_obj(
                video_ld,
                {
                    'comment_count': ('commentCount', {int_or_none}),
                    'uploader': ('creator', 'mainEntity', 'name', {str}),
                    'uploader_id': ('creator', 'mainEntity', 'identifier', {str_or_none}),
                    'uploader_url': ('creator', 'mainEntity', 'url', {url_or_none}),
                    'track': ('audio', 'name', {str}),
                    'artist': ('audio', 'author', {str}),
                    'repost_count': (
                        'interactionStatistic',
                        lambda _, v: 'ShareAction' in str(traverse_obj(v, 'interactionType')),
                        'userInteractionCount',
                        {int_or_none},
                        any,
                    ),
                },
            ),
        }
