import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    float_or_none,
    remove_end,
    remove_start,
    str_to_int,
    unified_strdate,
    url_or_none,
)


class StreamrubyIE(InfoExtractor):
    IE_NAME = 'streamruby'
    IE_DESC = 'Streamruby'
    _DOMAINS = r'(?:www\.)?(?:rubyvidhub|streamruby)\.com'
    _VALID_URL = rf'https?://{_DOMAINS}/(?:embed-|e/|d/)?(?P<id>[0-9a-z]{{12}})(?:\.html)?(?:[/?#]|$)'
    _EMBED_REGEX = [rf'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://{_DOMAINS}/embed-[0-9a-z]+\.html[^"\']*)\1']
    _TESTS = [
        {
            'url': 'https://rubyvidhub.com/embed-hofsdrqkiqf3.html',
            'md5': '7c6c87f7d291330a330a0bf26a571a02',
            'info_dict': {
                'id': 'hofsdrqkiqf3',
                'ext': 'mp4',
                'title': 'pokoli2.32',
                'thumbnail': r're:https?://img\.streamruby\.com/.+',
                'duration': 2784,
                'upload_date': '20260203',
                'view_count': int,
            },
        },
        {
            'url': 'https://rubyvidhub.com/hofsdrqkiqf3.html',
            'only_matching': True,
        },
        {
            'url': 'https://streamruby.com/embed-hofsdrqkiqf3.html',
            'only_matching': True,
        },
        {
            'url': 'https://streamruby.com/hofsdrqkiqf3.html',
            'only_matching': True,
        },
        {
            'url': 'https://rubyvidhub.com/e/hofsdrqkiqf3.html',
            'only_matching': True,
        },
        {
            'url': 'https://www.streamruby.com/d/hofsdrqkiqf3',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = urllib.parse.urlparse(url).hostname or 'rubyvidhub.com'
        webpage = self._download_webpage(f'https://{host}/embed-{video_id}.html', video_id)

        if 'File is no longer available' in webpage:
            raise ExtractorError('Video expired or has been deleted', expected=True)

        packed = self._search_regex(r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player')
        decoded = decode_packed_codes(packed)
        m3u8_url = self._search_regex(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', decoded, 'm3u8 URL')
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(m3u8_url, video_id, 'mp4', m3u8_id='hls')

        watch_page = (
            self._download_webpage(
                f'https://{host}/{video_id}.html', video_id, 'Downloading video metadata', fatal=False,
            )
            or ''
        )
        title = (
            self._html_search_regex(
                r'<h1[^>]*class="[^"]*download-title[^"]*"[^>]*>\s*<span[^>]*>([^<]+)',
                watch_page,
                'title',
                default=None,
            )
            or remove_end(self._html_extract_title(watch_page, default=''), ' - Streamruby')
            or video_id
        )
        title = remove_start(title, 'Watch ').strip() or video_id

        return {
            'id': video_id,
            'title': title,
            'thumbnail': url_or_none(
                self._search_regex(r'image\s*:\s*["\']([^"\']+)["\']', decoded, 'thumbnail', default=None),
            ),
            'duration': float_or_none(
                self._search_regex(r'duration\s*:\s*["\']([^"\']+)["\']', decoded, 'duration', default=None),
            ),
            'upload_date': unified_strdate(
                self._search_regex(r'\bon\s+(\w+\s+\d{1,2},\s+\d{4})', watch_page, 'upload date', default=None),
            ),
            'view_count': str_to_int(self._search_regex(r'>(\d+)\s+views<', watch_page, 'view count', default=None)),
            'formats': formats,
            'subtitles': subtitles,
        }
