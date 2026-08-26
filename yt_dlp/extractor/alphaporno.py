from .common import InfoExtractor
from ..utils import (
    int_or_none,
    merge_dicts,
    parse_duration,
    parse_iso8601,
    remove_end,
    unified_timestamp,
)


class AlphaPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?alphaporno\.com/videos/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.alphaporno.com/videos/sensual-striptease-porn-with-samantha-alexandra/',
        'md5': '7e6a1cdd48fa67362a5a11d7039164e7',
        'info_dict': {
            'id': '258807',
            'display_id': 'sensual-striptease-porn-with-samantha-alexandra',
            'ext': 'mp4',
            'title': 'Sensual striptease porn with Samantha Alexandra',
            'thumbnail': r're:https?://.*\.jpg$',
            'timestamp': 1418701811,
            'upload_date': '20141216',
            'duration': 387,
            'view_count': int,
            'categories': list,
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            (r'chs_object\s*=\s*[\'"](\d+)',
             r'params\[[\'"]video_id[\'"]\]\s*=\s*(\d+)',
             r'video_id\s*[:=]\s*[\'"]?(\d+)'),
            webpage, 'video id', default=display_id)

        title = remove_end(self._html_extract_title(webpage), ' - Alpha Porno')

        media = self._parse_html5_media_entries(url, webpage, display_id)
        info = media[0] if media else {}
        if not info.get('formats') and not info.get('url'):
            info['url'] = self._search_regex(
                r"video_url\s*:\s*'([^']+)'", webpage, 'video url')

        categories = [
            c.strip()
            for c in self._html_search_meta(
                'keywords', webpage, 'categories', default='').split(',')
            if c.strip()]
        duration = int_or_none(self._og_search_property(
            'video:duration', webpage, default=None)) or parse_duration(
            self._html_search_meta('duration', webpage, default=None))
        timestamp = unified_timestamp(self._og_search_property(
            'video:release_date', webpage, default=None)) or parse_iso8601(
            self._html_search_meta('uploadDate', webpage, default=None))
        view_count = int_or_none(self._search_regex(
            r'<span[^>]+class=["\']views["\'][^>]*>(\d+)', webpage,
            'view count', default=None))

        return merge_dicts(info, {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'categories': categories,
            'duration': duration,
            'timestamp': timestamp,
            'view_count': view_count,
            'age_limit': self._rta_search(webpage) or 18,
        })
