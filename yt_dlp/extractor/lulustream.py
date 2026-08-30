import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    float_or_none,
    parse_filesize,
    remove_end,
    unified_strdate,
    url_or_none,
)


class LuluStreamIE(InfoExtractor):
    IE_NAME = 'lulustream'
    IE_DESC = 'LuluStream'
    _DOMAINS = r'(?:www\.)?(?:luluvid|luluvdoo|luluvdo|lulustream)\.com'
    _VALID_URL = rf'https?://{_DOMAINS}/(?:[ed]/)?(?P<id>[0-9a-z]{{10,15}})(?:_h)?(?:[/?#]|$)'
    _EMBED_REGEX = [rf'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://{_DOMAINS}/e/[0-9a-z]+)\1']
    _TESTS = [
        {
            'url': 'https://luluvid.com/d/yzip3nvuot20',
            'md5': 'fd1d9a84998514ffdb68bd635eee2799',
            'info_dict': {
                'id': 'yzip3nvuot20',
                'ext': 'mp4',
                'title': 'Big Buck Bunny',
                'thumbnail': r're:https?://img\.lulucdn\.com/.+\.jpg',
                'duration': 634.6,
                'upload_date': '20260507',
                'filesize_approx': 247100000,
                'age_limit': 18,
            },
        },
        {
            'url': 'https://luluvid.com/e/yzip3nvuot20',
            'only_matching': True,
        },
        {
            'url': 'https://luluvdo.com/yzip3nvuot20',
            'only_matching': True,
        },
        {
            'url': 'https://luluvdo.com/e/yzip3nvuot20',
            'only_matching': True,
        },
        {
            'url': 'https://lulustream.com/d/yzip3nvuot20',
            'only_matching': True,
        },
        {
            'url': 'https://luluvdoo.com/d/yzip3nvuot20',
            'only_matching': True,
        },
        {
            'url': 'https://www.luluvdo.com/d/yzip3nvuot20',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = urllib.parse.urlparse(url).hostname or 'luluvdo.com'
        webpage = self._download_webpage(f'https://{host}/e/{video_id}', video_id)

        if 'File is no longer available' in webpage:
            raise ExtractorError('Video expired or has been deleted', expected=True)

        packed = self._search_regex(r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player')
        decoded = decode_packed_codes(packed)
        m3u8_url = self._search_regex(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', decoded, 'm3u8 URL')
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(m3u8_url, video_id, 'mp4', m3u8_id='hls')

        dl_page = (
            self._download_webpage(f'https://{host}/d/{video_id}', video_id, 'Downloading video metadata', fatal=False)
            or ''
        )
        title = (
            self._html_search_regex(r'<h1[^>]*>([^<]+)', dl_page, 'title', default=None)
            or remove_end(self._html_extract_title(webpage, default=''), ' - LuluStream')
            or video_id
        ).strip()

        return {
            'id': video_id,
            'title': title,
            'thumbnail': url_or_none(
                self._search_regex(r'image\s*:\s*["\']([^"\']+)["\']', decoded, 'thumbnail', default=None),
            )
            or self._html_search_meta('og:image', webpage, default=None),
            'duration': float_or_none(
                self._search_regex(r'duration\s*:\s*["\']([^"\']+)["\']', decoded, 'duration', default=None),
            ),
            'upload_date': unified_strdate(
                self._search_regex(r'\bon\s+(\w+\s+\d{1,2},\s+\d{4})', dl_page, 'upload date', default=None),
            ),
            'filesize_approx': parse_filesize(
                self._search_regex(r'(\d+(?:\.\d+)?\s*[KMGT]B)', dl_page, 'filesize', default=None),
            ),
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
        }
