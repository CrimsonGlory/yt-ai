import json
import re

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
                'track': 'Áudio original criado por Massaki',
                'artists': ['Massaki'],
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
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
        return {}

    def _extract_nuxt_video_ld(self, webpage, video_id):
        """Packed related-video fields share caption/user_id_str; seoData is the watch page."""
        # IIFE argument lists can contain JS floats like `.0001`
        patched = re.sub(r'([\[,])(\.\d+)', r'\g<1>0\2', webpage)
        return traverse_obj(self._search_nuxt_data(patched, video_id, fatal=False), (
            'seoData', lambda _, v: isinstance(v, dict) and v.get('id') == 'VideoObject',
            'innerHTML', {dict}, any,
        )) or {}

    def _decode_js_string(self, value):
        if not value:
            return value
        try:
            return json.loads(f'"{value}"')
        except json.JSONDecodeError:
            return value

    def _extract_nuxt_photo(self, webpage):
        """Packed window.__NUXT__ IIFE on the desktop PWA (JSON-LD is often omitted)."""
        video_url = self._decode_js_string(self._search_regex(
            r'main_mv_urls:\s*\[\s*\{[^}]*?\burl:\s*"((?:\\.|[^"])+)"',
            webpage, 'nuxt video URL', default=None))
        thumbnail = self._decode_js_string(self._search_regex(
            r'cover_thumbnail_urls:\s*\[\s*\{[^}]*?\burl:\s*"((?:\\.|[^"])+)"',
            webpage, 'nuxt thumbnail', default=None))
        caption = self._decode_js_string(self._search_regex(
            r'\bcaption:"((?:\\.|[^"])*)"', webpage, 'caption', default=None))
        duration_ms = self._search_regex(
            r'adaptationSet:\[\{id:\w+,duration:(\d+)', webpage, 'duration', default=None)
        timestamp_ms = self._search_regex(
            r'\btimestamp:(\d{10,})', webpage, 'timestamp', default=None)
        width, height = self._search_regex(
            r'\}\((?:true|false),\d+,-?\d+,"[^"]*",(\d+),(\d+),',
            webpage, 'dimensions', default=(None, None), group=(1, 2))
        return {
            'url': url_or_none(video_url),
            'thumbnail': url_or_none(thumbnail),
            'title': caption,
            'description': caption,
            'duration': int_or_none(duration_ms, scale=1000),
            'timestamp': int_or_none(timestamp_ms, scale=1000),
            'like_count': int_or_none(self._search_regex(
                r'\blike_count:(\d+)', webpage, 'like count', default=None)),
            'view_count': int_or_none(self._search_regex(
                r'\bview_count:(\d+)', webpage, 'view count', default=None)),
            'comment_count': int_or_none(self._search_regex(
                r'\bcomment_count:(\d+)', webpage, 'comment count', default=None)),
            'repost_count': int_or_none(self._search_regex(
                r'\bforward_count:(\d+)', webpage, 'repost count', default=None)),
            'uploader_id': self._search_regex(
                r'user_id_str:"([^"]+)"', webpage, 'uploader id', default=None),
            'width': int_or_none(width),
            'height': int_or_none(height),
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        # Mobile UA currently serves a Next.js shell with no media; desktop Nuxt
        # still embeds main_mv_urls. s.kw.ai share links redirect to the app store
        # on a mobile UA, so keep desktop first.
        webpage, urlh = self._download_webpage_handle(
            url, display_id, impersonate=True)
        video_ld = self._extract_nuxt_video_ld(webpage, display_id)
        if not url_or_none(video_ld.get('contentUrl')):
            video_ld = self._extract_video_ld(webpage, display_id)
        nuxt = self._extract_nuxt_photo(webpage)

        if not url_or_none(video_ld.get('contentUrl')) and not nuxt.get('url'):
            webpage = self._download_webpage(
                urlh.url, display_id, 'Downloading mobile webpage',
                headers=self._MOBILE_HEADERS, impersonate=True,
            )
            video_ld = self._extract_nuxt_video_ld(webpage, display_id)
            if not url_or_none(video_ld.get('contentUrl')):
                video_ld = self._extract_video_ld(webpage, display_id)
            nuxt = self._extract_nuxt_photo(webpage)

        video_url = (
            url_or_none(video_ld.get('contentUrl'))
            or nuxt.get('url')
            or url_or_none(self._search_regex(
                r'"contentUrl"\s*:\s*"([^"]+)"', webpage, 'content URL', default=None))
        )
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
        caption = (
            traverse_obj(video_ld, ('description', {str}))
            or nuxt.get('title')
            or self._html_search_regex(
                r'Kwai video from [^:]+:\s*(?:&quot;|")(.+?)(?:&quot;|")',
                webpage, 'caption', default=None)
        )
        if caption:
            info['title'] = caption
            info.setdefault('description', caption)

        uploader = self._search_regex(
            r'kwai\.com/@([^/?#]+)', urlh.url, 'uploader', default=None)
        uploader_url = f'https://www.kwai.com/@{uploader}' if uploader else None

        # Packed caption/user_id_str/cover URLs also match related videos
        extra_nuxt = {}
        if not url_or_none(video_ld.get('contentUrl')):
            extra_nuxt = {k: v for k, v in nuxt.items() if k != 'url' and v is not None}

        return {
            'id': video_id,
            'ext': 'mp4',
            **extra_nuxt,
            **info,
            'url': video_url,
            **traverse_obj(
                video_ld,
                {
                    'comment_count': ('commentCount', {int_or_none}),
                    'uploader': ('creator', 'mainEntity', 'name', {str}),
                    'uploader_id': ('creator', 'mainEntity', 'identifier', {str_or_none}),
                    'uploader_url': ('creator', 'mainEntity', 'url', {url_or_none}),
                    'thumbnail': ('thumbnailUrl', (None, 0, ...), {url_or_none}, any),
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
            **{k: v for k, v in {
                'uploader': uploader,
                'uploader_url': uploader_url,
            }.items() if v},
        }
