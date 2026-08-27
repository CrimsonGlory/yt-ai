import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class HBOIE(InfoExtractor):
    IE_NAME = 'hbo'
    _VALID_URL = (
        r'https?://(?:www\.)?hbo\.com/(?:video|embed|content)'
        r'(?:/[^/?#]+)*/(?P<id>[^/?#]+)/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://www.hbo.com/content/lanterns',
        'md5': '62f54f87ac62e4d334c66ea1805ebcd7',
        'info_dict': {
            'id': 'me517d9dc51bbc7a2d6bbec453837451815d65db26',
            'ext': 'mp4',
            'display_id': 'lanterns',
            'title': 'Lanterns - Watch the Teaser',
            'alt_title': 'Lanterns',
            'description': 'md5:8d1530405339d84a584c61911ff82ef4',
            'thumbnail': r're:https://.+\.(?:jpe?g|png)',
            'duration': 107.940956,
        },
        # Native HLS --test only fetches the CMAF init segment (~1KB)
        'params': {'downloader': 'ffmpeg'},
    }, {
        'url': 'https://www.hbo.com/video/game-of-thrones/seasons/season-8/videos/trailer',
        'skip': 'video gone',
        'md5': '8126210656f433c452a21367f9ad85b3',
        'info_dict': {
            'id': '22113301',
            'ext': 'mp4',
            'title': 'Game of Thrones - Trailer',
        },
        'expected_warnings': ['Unknown MIME type application/mp4 in DASH manifest'],
    }]

    def _extract_page_sources(self, webpage, url, display_id):
        sources = [webpage]
        for src in re.findall(r'<script[^>]+\bsrc=["\']([^"\']+)["\']', webpage):
            if '/chunks/pages/' not in src or '/pages/_' in src:
                continue
            js = self._download_webpage(
                urljoin(url, src), display_id,
                note='Downloading page script', fatal=False)
            if js:
                sources.append(js)
        return sources

    def _player_meta(self, source, media_id):
        idx = source.find(media_id)
        if idx < 0:
            return {}
        window = source[max(0, idx - 1200):idx + 80]
        cover = self._search_regex(
            r'coverImage:\w+\(\'({[^\']+})\'', window, 'cover', default=None)
        title = self._search_regex(
            r'\btitle:\w+\("([^"]+)"', window, 'title', default=None)
        alt_title = self._search_regex(
            r'\baltText:\w+\("([^"]*)"', window, 'alt title', default=None)
        thumbnail = traverse_obj(
            self._parse_json(
                cover.replace('\\/', '/'), media_id, fatal=False) if cover else None,
            ('large', {url_or_none}))
        return {
            'title': ' - '.join(filter(None, (alt_title, title))) or None,
            'alt_title': alt_title or None,
            'thumbnail': thumbnail,
            'duration': float_or_none(self._search_regex(
                r'"duration"\s*:\s*"([^"]+)"', window, 'duration', default=None)),
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        next_data = self._search_nextjs_data(webpage, display_id, default={})
        app_id = traverse_obj(next_data, (
            'props', 'pageProps', 'siteConfig', 'VIDEOPLAYER', 'mediaAppId', {str}))

        media_id, player_meta = None, {}
        for source in self._extract_page_sources(webpage, url, display_id):
            media_id = self._search_regex(
                r'["\']?mediaId["\']?\s*[:=]\s*["\'](me[0-9a-f]+)["\']',
                source, 'media id', default=None)
            if media_id:
                player_meta = self._player_meta(source, media_id)
                break

        if not media_id:
            raise ExtractorError('No video found', expected=True)
        if not app_id:
            raise ExtractorError('Unable to extract media app id')

        media_data = self._download_json(
            f'https://medium.ngtv.io/v2/media/{media_id}/desktop',
            media_id, query={'appId': app_id})
        m3u8_url = traverse_obj(media_data, (
            'media', 'desktop', 'unprotected', 'unencrypted', 'url', {url_or_none}))
        if not m3u8_url:
            raise ExtractorError('No unprotected media formats available', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, media_id, 'mp4', 'm3u8', m3u8_id='hls')

        return {
            'id': media_id,
            'display_id': display_id,
            'title': player_meta.get('title') or self._og_search_title(webpage),
            'alt_title': player_meta.get('alt_title'),
            'description': self._og_search_description(webpage),
            'thumbnail': player_meta.get('thumbnail'),
            'duration': traverse_obj(media_data, (
                'media', 'desktop', 'unprotected', 'unencrypted',
                'totalRuntime', {float_or_none})) or player_meta.get('duration'),
            'formats': formats,
            'subtitles': subtitles,
        }
