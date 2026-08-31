from .common import InfoExtractor
from ..networking import Request
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
    urljoin,
)


class EmturbovidIE(InfoExtractor):
    IE_NAME = 'emturbovid'
    IE_DESC = 'emturbovid.com'
    _VALID_URL = r'https?://(?:www\.)?(?:emturbovid|turbovidhls)\.com/t/(?P<id>[\w-]+)'
    _EMBED_REGEX = [
        r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?(?:emturbovid|turbovidhls)\.com/t/[^"\']+)',
    ]
    _TESTS = [{
        'url': 'https://emturbovid.com/t/68b737d26c659',
        'md5': 'd9b4e52e2120afcd73d07c59c1598671',
        'info_dict': {
            'id': '68b737d26c659',
            'ext': 'mp4',
            'title': 'SABA-878',
            'thumbnail': 'https://ver1.sptvp.com/poster/A/E0/68b737d26c659.png',
            'age_limit': 18,
        },
        'params': {'format': 'best[height=480]'},
    }, {
        'url': 'https://emturbovid.com/t/U7VLMd4rErMZmp2FHkeF#supjav.com@avop-127-ub.mp4',
        'only_matching': True,
    }, {
        'url': 'https://emturbovid.com/t/EvmJWYQ7B3IGZyauvXs9',
        'only_matching': True,
    }, {
        'url': 'https://turbovidhls.com/t/68b737d26c659',
        'only_matching': True,
    }]

    @staticmethod
    def _png_payload_offset(data):
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            return None
        offset = 8
        while offset + 8 <= len(data):
            length = int.from_bytes(data[offset:offset + 4], 'big')
            chunk_type = data[offset + 4:offset + 8]
            offset += 12 + length
            if chunk_type == b'IEND':
                return offset
        return None

    def _rewrite_png_wrapped_playlist(self, playlist, playlist_url, video_id):
        """Skip the dummy PNG header on the first Google Drive HLS fragment.

        Newer TurboVID playlists store MPEG-TS inside a PNG file. The native
        HLS downloader can Range-skip that prefix via EXT-X-BYTERANGE; ffmpeg
        then sees MPEG-TS and remuxes the rest of the stream.
        """
        lines = playlist.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            segment_url = urljoin(playlist_url, stripped)
            urlh = self._request_webpage(
                Request(segment_url, headers={'Range': 'bytes=0-2047'}),
                video_id, 'Checking HLS segment wrapper', fatal=False)
            if not urlh:
                break
            data = urlh.read()
            png_offset = self._png_payload_offset(data)
            if not png_offset:
                break
            content_range = urlh.headers.get('Content-Range') or ''
            total = int_or_none(
                content_range.rsplit('/', 1)[-1] if '/' in content_range else None,
            ) or int_or_none(urlh.headers.get('Content-Length'))
            if not total or total <= png_offset:
                break
            lines.insert(i, f'#EXT-X-BYTERANGE:{total - png_offset}@{png_offset}')
            break
        return '\n'.join(lines) + '\n'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        m3u8_url = url_or_none(self._search_regex(
            (r'\burlPlay\s*=\s*(["\'])(?P<url>https?://(?:(?!\1).)+)\1',
             r'data-hash=(["\'])(?P<url>https?://[^"\']+\.m3u8[^"\']*)\1'),
            webpage, 'm3u8 URL', default=None, group='url'))
        if not m3u8_url:
            raise ExtractorError('No video source found', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls')
        for fmt in formats:
            media_url = fmt.get('url')
            if not media_url:
                continue
            playlist = self._download_webpage(
                media_url, video_id, 'Downloading m3u8 playlist', fatal=False)
            if not playlist or not playlist.lstrip().startswith('#EXTM3U'):
                continue
            fmt['hls_media_playlist_data'] = self._rewrite_png_wrapped_playlist(
                playlist, media_url, video_id)

        title = self._html_extract_title(webpage, default=None) or video_id
        thumbnail = url_or_none(self._search_regex(
            r'''['"](https?://[^'"]+/poster/[^'"]+)['"]''',
            webpage, 'thumbnail', default=None))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 18,
        }
