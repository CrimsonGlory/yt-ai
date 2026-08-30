import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    merge_dicts,
    orderedSet,
    unified_strdate,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class AvjbIE(InfoExtractor):
    IE_NAME = 'avjb'
    IE_DESC = 'AVJB'
    _VALID_URL = (
        r'https?://(?:www\.)?avjb\.com/(?:[a-z]{2}/)?'
        r'(?:videos?|newembed)/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?')
    _TESTS = [{
        'url': 'https://avjb.com/en/video/110590/hongkongdoll-special-short-collection-series-living-with-her-special-billiard/',
        'md5': '02941c8c6b542d0020011737eca0d215',
        'info_dict': {
            'id': '110590',
            'ext': 'mp4',
            'display_id': 'hongkongdoll-special-short-collection-series-living-with-her-special-billiard',
            'title': 'HONGKONGDOLL - SPECIAL Short collection series "Living with her - Special - Billiard"',
            'description': 'HONGKONGDOLL - SPECIAL Short collection series "Living with her - Special - Billiard"',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png|webp)',
            'duration': 1978,
            'upload_date': '20250918',
            'timestamp': 1758176725,
            'uploader': 'Yamada_Ryu',
            'uploader_id': '1707793',
            'view_count': int,
            'like_count': int,
            'tags': ['special'],
            'age_limit': 18,
        },
        'params': {'fixup': 'never'},
    }, {
        'url': 'https://avjb.com/zh/video/110590/hongkongdoll-special-short-collection-series-living-with-her-special-billiard/',
        'only_matching': True,
    }, {
        'url': 'https://avjb.com/en/newembed/110590',
        'only_matching': True,
    }, {
        'url': 'https://www.avjb.com/videos/110590/hongkongdoll-special-short-collection-series-living-with-her-special-billiard/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        if '/newembed/' in url:
            video_path = self._search_regex(
                rf'href=["\']([^"\']+/{video_id}/[^"\']*)',
                webpage, 'video page', default=None)
            if video_path:
                webpage = self._download_webpage(
                    urljoin(url, video_path), video_id, note='Downloading video page')

        headers = {'Referer': 'https://avjb.com/'}
        formats = []

        csrf = self._search_regex(
            r'PLAYER_CSRF\s*=\s*"([^"]+)"', webpage, 'player csrf', default=None)
        if csrf:
            player_api = self._search_regex(
                r'PLAYER_LINES_API\s*=\s*"([^"]+)"',
                webpage, 'player API', default='/player/spped.php')
            data = self._download_json(
                urljoin(url, player_api), video_id, 'Downloading player sources',
                fatal=False, query={'csrf': csrf}, headers=headers) or {}
            default_key = traverse_obj(data, ('defaultKey', {str}))
            for source in traverse_obj(data, ('sources', lambda _, v: url_or_none(v['url']))):
                src, key = source['url'], traverse_obj(source, ('key', {str})) or 'hls'
                preference = 1 if key == default_key else -1
                if determine_ext(src) == 'm3u8':
                    for fmt in self._extract_m3u8_formats(
                            src, video_id, 'mp4', m3u8_id=key, fatal=False, headers=headers):
                        fmt['source_preference'] = preference
                        fmt.setdefault('http_headers', headers)
                        formats.append(fmt)
                else:
                    formats.append({
                        'url': src,
                        'format_id': key,
                        'ext': determine_ext(src, 'mp4'),
                        'source_preference': preference,
                        'http_headers': headers,
                    })

        if not formats:
            mp4_url = url_or_none(self._search_regex(
                (r'(?s)new\s+Playerjs\(\s*\{.*?file\s*:\s*(["\'])(?P<url>https?://[^"\']+)\1',
                 r'<source[^>]+src=(["\'])(?P<url>https?://[^"\']+)\1'),
                webpage, 'mp4 url', default=None, group='url'))
            if mp4_url:
                formats.append({
                    'url': mp4_url,
                    'format_id': 'http',
                    'ext': 'mp4',
                    'http_headers': headers,
                })

        if not formats:
            raise ExtractorError('No video sources found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title': (
                self._html_search_regex(
                    r'<h1[^>]*id=["\']videoTitle["\'][^>]*>([^<]+)',
                    webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': int_or_none(self._html_search_meta(
                'duration', webpage, default=None)),
            'upload_date': unified_strdate(self._og_search_property(
                'video:release_date', webpage, default=None)),
            'uploader': self._html_search_regex(
                r'<span[^>]+class=["\']creator-display-name["\'][^>]*>([^<]+)',
                webpage, 'uploader', default=None),
            'uploader_id': self._search_regex(
                r'/members/(\d+)/', webpage, 'uploader id', default=None),
            'view_count': int_or_none(self._search_regex(
                r'views_total"\s+content="(\d+)"', webpage, 'view count', default=None)),
            'tags': orderedSet(re.findall(r'/tags/([^/?#]+)/', webpage)) or None,
            'age_limit': 18,
            'formats': formats,
            'http_headers': headers,
        }, json_ld)
