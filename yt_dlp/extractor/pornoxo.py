from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_to_int,
    url_or_none,
)


class PornoXOIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?pornoxo\.com/videos/(?P<id>\d+)/(?P<display_id>[^/?#.]+)(?:\.html)?/?'
    _TESTS = [{
        'url': 'https://www.pornoxo.com/videos/2937311/lesbian-jav-aunt-part-2/',
        'md5': 'd72232fe98d6818c35bed694cc623f6b',
        'info_dict': {
            'id': '2937311',
            'ext': 'mp4',
            'title': 'Lesbian Jav Aunt Part 2',
            'display_id': 'lesbian-jav-aunt-part-2',
            'description': 'Lesbian Jav Aunt Part 2 featuring Asian, Lesbian, Brunette, Masturbation, Big Ass, Japanese, HD Porn 1080p',
            'categories': list,  # NSFW
            'thumbnail': r're:https?://.*\.jpg$',
            'duration': 4990,
            'view_count': int,
            'age_limit': 18,
        },
    }, {
        'url': 'http://www.pornoxo.com/videos/7564/striptease-from-sexy-secretary.html',
        'skip': 'video gone',
        'md5': '582f28ecbaa9e6e24cb90f50f524ce87',
        'info_dict': {
            'id': '7564',
            'ext': 'flv',
            'title': 'Striptease From Sexy Secretary!',
            'display_id': 'striptease-from-sexy-secretary',
            'description': 'md5:0ee35252b685b3883f4a1d38332f9980',
            'categories': list,  # NSFW
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id, impersonate=True)

        sources = self._search_json(
            r'sources\s*:', webpage, 'player sources', video_id)
        if not isinstance(sources, dict):
            sources = {}
        hls_url = url_or_none(sources.get('hlsAuto'))
        if hls_url:
            formats = self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats = [{
                'url': src,
                'format_id': format_id,
            } for format_id, src in sources.items() if url_or_none(src)]

        title = self._html_search_regex(
            (r'<h1>([^<]+)</h1>',
             r'<title>([^<]+?)\s*[|\-]\s*PornoXO'),
            webpage, 'title')

        view_count = str_to_int(self._html_search_regex(
            r'([\d,]+)\s*Views', webpage, 'view count', fatal=False))
        duration = int_or_none(self._search_regex(
            r'videoDuration:\s*(\d+)', webpage, 'duration', default=None))

        categories_str = self._html_search_regex(
            r'<meta name="description" content=".*featuring\s*([^"]+)"',
            webpage, 'categories', fatal=False)
        categories = None if categories_str is None else [
            c.strip() for c in categories_str.split(',') if c.strip()]

        return {
            'id': video_id,
            'title': title,
            'display_id': display_id,
            'description': self._html_search_meta('description', webpage),
            'categories': categories,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'view_count': view_count,
            'duration': duration,
            'age_limit': 18,
            'formats': formats,
        }
