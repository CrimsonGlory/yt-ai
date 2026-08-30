import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    parse_iso8601,
    remove_end,
    traverse_obj,
    url_or_none,
)


class LuticlipIE(InfoExtractor):
    IE_NAME = 'luticlip'
    IE_DESC = 'luticlip.com'
    _VALID_URL = [
        r'https?://(?:www\.)?luticlip\.com/(?!(?:category|categories|tag|actors?|page|content|wp-(?:admin|content|includes|json)|report-abuse)(?:/|$))(?P<id>[^/?#]+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?luticlip\.com/\?(?:[^#]*&)?p=(?P<id>\d+)',
    ]
    _TESTS = [
        {
            'url': 'https://luticlip.com/%d9%85%d8%b1%d8%ac%d8%a7%d9%86-%db%8c%d9%88%d8%aa%db%8c%d9%88%d8%a8%d8%b1-%d9%85%d8%b9%d8%b1%d9%88%d9%81-%da%a9%d9%87-%d8%a8%d9%87-%d8%a8%d9%87%d9%88%d9%86%d9%87-%d8%b2%d9%86%d8%af%da%af%db%8c-2/',
            'md5': 'c2125fb249460feb53da027fd696d86c',
            'info_dict': {
                'id': '52038',
                'ext': 'mp4',
                'display_id': 'مرجان-یوتیوبر-معروف-که-به-بهونه-زندگی-2',
                'title': 'مرجان یوتیوبر معروف که به بهونه زندگی روزمره، ممه های خوش فرم و کص و کونشو مینداخت بیرون قسمت 2',
                'description': 'مرجان یوتیوبر معروف که به بهونه زندگی روزمره، ممه های خوش فرم و کص و کونشو مینداخت بیرون قسمت 2',
                'thumbnail': r're:https?://luticlip\.com/content/uploads/.+\.jpg',
                'duration': 432,
                'timestamp': 1772116991,
                'upload_date': '20260226',
                'uploader': 'Luti Uploader',
                'age_limit': 18,
                'tags': [
                    'Big Ass',
                    'big tits',
                    'HD Porn',
                    'اندام نمایی',
                    'جدید',
                    'دلبری',
                    'کلیپ سکسی',
                    'ممه سکسی',
                    'ممه گنده',
                    'ممه نمایی',
                ],
                'categories': ['انگشت کردن کس', 'بدن نمایی', 'خودراضایی', 'فیلم سکسی', 'ممه گنده', 'میسترس'],
            },
        },
        {
            'url': 'https://luticlip.com/?p=52038',
            'only_matching': True,
        },
        {
            'url': 'https://www.luticlip.com/%d8%b3%da%a9%d8%b3-%d8%b2%d9%86-%d8%ad%d8%b4%d8%b1%db%8c-%d8%a8%d8%a7-%d8%b3%d8%aa-%d9%82%d8%b1%d9%85%d8%b2-%d8%b2%d9%86%d9%87-%d8%af%d8%a7%da%af%db%8c-%d8%b4%d8%af%d9%87-%d9%88-%d8%b4%d8%b1%d8%aa/',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        url_id = urllib.parse.unquote(self._match_id(url))
        webpage = self._download_webpage(url, url_id)
        video_id = self._search_regex(r'\bpostid-(\d+)', webpage, 'post id', default=url_id)
        display_id = urllib.parse.unquote(
            self._search_regex(
                r'luticlip\.com/([^/?#]+)', self._og_search_url(webpage, default='') or url, 'slug', default=url_id,
            ),
        )

        headers = {'Referer': url}
        formats, thumbnail = [], None
        for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
            formats.extend(entry.get('formats') or [])
            thumbnail = thumbnail or entry.get('thumbnail')
        if not formats:
            video_url = url_or_none(self._html_search_meta('contentURL', webpage, default=None))
            if video_url:
                formats.append({'url': video_url, 'ext': 'mp4'})
        if not formats:
            raise ExtractorError('No video source found', expected=True)

        # takcdn closes non-Range GET requests; chunked Range downloads succeed
        for f in formats:
            f.setdefault('http_headers', headers)
            f.setdefault('downloader_options', {})['http_chunk_size'] = 10 << 20

        json_ld = self._search_json_ld(webpage, video_id, default={})
        article = {}
        for ld in self._yield_json_ld(webpage, video_id, default={}):
            article = traverse_obj(ld, (
                '@graph', lambda _, v: v['@type'] == 'Article', any,
            )) or {}
            if article:
                break

        title = (
            self._html_search_regex(r'<h1[^>]+class=["\']entry-title["\'][^>]*>([^<]+)', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or json_ld.get('title')
            or remove_end(self._html_extract_title(webpage, default=''), ' - تماشای فیلم سکسی ایرانی')
            or None
        )

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': (
                json_ld.get('description')
                or self._og_search_description(webpage, default=None)
                or self._html_search_meta('description', webpage, default=None)
            ),
            'thumbnail': (
                thumbnail
                or url_or_none(self._html_search_meta('thumbnailUrl', webpage, default=None))
                or self._og_search_thumbnail(webpage)
            ),
            'duration': parse_duration(self._html_search_meta('duration', webpage, default=None)),
            'timestamp': (
                json_ld.get('timestamp') or parse_iso8601(self._html_search_meta('uploadDate', webpage, default=None))
            ),
            'uploader': (
                self._html_search_meta('author', webpage, default=None)
                or traverse_obj(article, ('author', 'name', {str}))
            ),
            'tags': traverse_obj(article, ('keywords', ..., {str})) or None,
            'categories': traverse_obj(article, ('articleSection', ..., {str})) or None,
            'age_limit': 18,
            'formats': formats,
            'http_headers': headers,
        }
