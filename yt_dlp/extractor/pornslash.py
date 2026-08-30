import base64
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    merge_dicts,
    orderedSet,
    try_call,
    update_url,
    url_or_none,
    urljoin,
)


class PornSlashIE(InfoExtractor):
    IE_DESC = 'pornslash.com'
    _VALID_URL = r'https?://(?:www\.)?pornslash\.com/(?:watch|embed)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.pornslash.com/watch/Q0mQbzEJbj2',
        'md5': 'ec0514f747709f52203b588f592631e7',
        'info_dict': {
            'id': 'Q0mQbzEJbj2',
            'ext': 'mp4',
            'title': 'fucked a slutty maid',
            'description': 'fucked a slutty maid',
            'thumbnail': r're:https?://.+\.(?:jpe?g|png|webp)',
            'duration': 1139,
            'timestamp': 1761250081,
            'upload_date': '20251023',
            'view_count': int,
            'like_count': int,
            'tags': ['fucked slutty maid', 'slutty maid', 'fucked slutty', 'slutty', 'maid', 'fucked'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.pornslash.com/embed/Q0mQbzEJbj2',
        'only_matching': True,
    }, {
        'url': 'https://pornslash.com/watch/Q0mQbzEJbj2',
        'only_matching': True,
    }]

    def _extract_hls(self, hls_url, video_id):
        return self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
            headers={'Referer': 'https://www.pornslash.com/'})

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        hls_url = self._search_regex(
            r'\.loadSource\(\s*(["\'])(?P<url>https?://[^"\']+)\1',
            webpage, 'HLS URL', group='url')
        formats, subtitles = self._extract_hls(hls_url, video_id)

        if not formats:
            report = self._download_json(
                urljoin(url, '/media/report'), video_id,
                'Downloading alternate media host', fatal=False) or {}
            alt_base = try_call(
                lambda: url_or_none(base64.b64decode(report['msg']).decode()))
            if alt_base:
                parsed = urllib.parse.urlparse(alt_base)
                hls_url = update_url(hls_url, scheme=parsed.scheme, netloc=parsed.netloc)
                formats, subtitles = self._extract_hls(hls_url, video_id)

        if not formats:
            self.raise_no_formats('Unable to extract HLS formats', expected=True, video_id=video_id)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)

        return merge_dicts({
            'id': video_id,
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
            'title': self._og_search_title(webpage, default=None),
            'duration': int_or_none(self._og_search_property('duration', webpage, default=None)),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'view_count': int_or_none(self._search_regex(
                r'class="video-views">\s*([\d,]+)\s*views',
                webpage, 'view count', default=None)),
            'tags': orderedSet(re.findall(
                r'<a[^>]+class="video-tag"[^>]*>([^<]+)', webpage)) or None,
        }, json_ld)
