import re

from .common import InfoExtractor
from ..utils import (
    decode_packed_codes,
    determine_ext,
    url_or_none,
)


class FilemoonIE(InfoExtractor):
    IE_NAME = 'filemoon'
    IE_DESC = 'filemoon.sx'
    _VALID_URL = r'https?://(?:www\.)?filemoon\.sx/(?:e|d)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://filemoon.sx/e/abcd1234efgh',
        'only_matching': True,
    }, {
        'url': 'https://filemoon.sx/d/abcd1234efgh',
        'only_matching': True,
    }, {
        'url': 'https://www.filemoon.sx/e/abcd1234efgh',
        'only_matching': True,
    }]

    def _extract_player_urls(self, webpage):
        packed = self._search_regex(
            r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default=None)
        if packed:
            webpage += decode_packed_codes(packed)

        urls = []
        for regex in (
            r'(?:file|src)\s*:\s*(["\'])(?P<url>https?://(?:(?!\1).)+\.(?:m3u8|mp4|flv)(?:(?!\1).)*)\1',
            r'<source[^>]+src=(["\'])(?P<url>https?://(?:(?!\1).)+)\1',
        ):
            for mobj in re.finditer(regex, webpage):
                video_url = url_or_none(mobj.group('url'))
                if video_url and video_url not in urls:
                    urls.append(video_url)
        return urls

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = (self._og_search_title(webpage, default=None)
                 or self._html_extract_title(webpage, default=None)
                 or video_id)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        formats = []
        for video_url in self._extract_player_urls(webpage):
            if determine_ext(video_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': video_url,
                    'format_id': 'http',
                })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'http_headers': {'Referer': url},
        }
