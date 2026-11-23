import codecs
import re

from .common import InfoExtractor


class WebcameraplIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<id>[\w-]+)\.webcamera\.pl'
    _TESTS = [{
        'url': 'https://warszawa-plac-zamkowy.webcamera.pl',
        'info_dict': {
            'id': 'warszawa-plac-zamkowy',
            'ext': 'mp4',
            'title': r're:(?i)(?:WIDOK NA )?PLAC ZAMKOWY W WARSZAWIE \d{4}-\d{2}-\d{2} \d{2}:\d{2}$',
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://gdansk-stare-miasto.webcamera.pl/',
        'info_dict': {
            'id': 'gdansk-stare-miasto',
            'ext': 'mp4',
            'title': r're:(?i)GDAŃSK - widok na Stare Miasto(?: / Nowe ujęcia)? \d{4}-\d{2}-\d{2} \d{2}:\d{2}$',
            'live_status': 'is_live',
        },
    }]
    _STREAM_HOSTS = (
        'hoktastream2.webcamera.pl',
        'hoktastream1.webcamera.pl',
        'hoktastream3.webcamera.pl',
    )

    def _m3u8_candidates(self, m3u8_url, webpage):
        if re.match(r'https?://', m3u8_url):
            yield m3u8_url
            alt_url = m3u8_url.replace('/playlist.m3u8', '/chunks.m3u8')
            if alt_url != m3u8_url:
                yield alt_url
            return
        # Newer pages rot13 a relative ///playlist.m3u8 and put the Nimble
        # stream id on the poster thumbnail instead of an absolute HLS URL.
        stream_id = self._search_regex(
            r'/miniaturki/([^/?#]+)\.jpe?g', webpage, 'stream id', default=None)
        if not stream_id:
            return
        for host in self._STREAM_HOSTS:
            base = f'https://{host}/{stream_id}/{stream_id}.stream'
            yield f'{base}/playlist.m3u8'
            yield f'{base}/chunks.m3u8'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        rot13_m3u8_url = self._search_regex(
            r'data-src\s*=\s*"([^"]+\.z3h8)"', webpage, 'm3u8 url', default=None)
        if not rot13_m3u8_url:
            self.raise_no_formats('No video/audio found at the provided url', expected=True)

        m3u8_url = codecs.decode(rot13_m3u8_url, 'rot-13')
        headers = {'Referer': url}
        formats, subtitles = [], {}
        for candidate in self._m3u8_candidates(m3u8_url, webpage):
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                candidate, video_id, live=True, headers=headers, fatal=False, errnote=False)
            if formats:
                break
        if not formats:
            self.raise_no_formats('Failed to download m3u8 information', expected=True)

        return {
            'id': video_id,
            'title': self._html_search_regex(r'<h1\b[^>]*>([^>]+)</h1>', webpage, 'title'),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }
