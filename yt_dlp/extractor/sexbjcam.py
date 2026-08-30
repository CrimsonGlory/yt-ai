import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    determine_ext,
    extract_attributes,
    orderedSet,
    parse_duration,
    parse_iso8601,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class SexBJCamIE(InfoExtractor):
    IE_NAME = 'sexbjcam'
    IE_DESC = 'sexbjcam.com'
    _VALID_URL = r'https?://(?:www\.)?sexbjcam\.com/\d{4}/\d{2}/\d{2}/(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'https://sexbjcam.com/2026/08/26/kbj26082661_pandaclass_20260820/',
        'md5': '2e8b79c233b3a6ff2530429974f0cb63',
        'info_dict': {
            'id': 'kbj26082661_pandaclass_20260820',
            'ext': 'mp4',
            'title': 'kbj26082661_pandaclass_20260820',
            'description': 'kbj26082661_pandaclass_20260820',
            'thumbnail': r're:https?://sexbjcam\.com/wp-content/uploads/.+\.jpg',
            'duration': 2141,
            'timestamp': 1787705416,
            'upload_date': '20260826',
            'cast': ['pandaclass'],
            'categories': ['KOREAN BJ'],
            'tags': ['PandaTV'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://sexbjcam.com/2025/12/16/kbj25121646_loveu22_20250830/',
        'only_matching': True,
    }, {
        'url': 'https://www.sexbjcam.com/2025/12/16/kbj25121646_loveu22_20250830',
        'only_matching': True,
    }]

    def _extract_embed_url(self, webpage, page_url):
        embed_url = url_or_none(self._html_search_meta('embedUrl', webpage, default=None))
        if embed_url:
            return embed_url

        player_html = self._search_regex(
            r'<div[^>]+class=["\']responsive-player["\'][^>]*>(.*?)</div>',
            webpage, 'player', default='', flags=re.DOTALL | re.I)
        for iframe in re.finditer(r'<iframe\b[^>]*>', player_html, re.I):
            src = url_or_none(unescapeHTML(
                extract_attributes(iframe.group(0)).get('src')))
            if src:
                return urljoin(page_url, src)
        return None

    def _extract_player_formats(self, embed_url, video_id):
        headers = {'Referer': embed_url}
        webpage = self._download_webpage(
            embed_url, video_id, 'Downloading embed player',
            headers=headers, impersonate=True)

        if 'File is no longer available' in webpage:
            raise ExtractorError('Video expired or has been deleted', expected=True)

        packed = self._search_regex(
            r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default=None)
        decoded = decode_packed_codes(packed) if packed else webpage
        links = self._search_json(
            r'var\s+links\s*=', decoded, 'player links', video_id, default={})

        candidates, seen = [], set()
        for key in ('hls2', 'hls4', 'hls3'):
            media_url = url_or_none(urljoin(embed_url, links.get(key)))
            if media_url and media_url not in seen:
                seen.add(media_url)
                candidates.append(media_url)
        for media_url in re.findall(r'https?://[^\'"\\\s<>]+', decoded):
            media_url = url_or_none(unescapeHTML(media_url.rstrip('\\,;')))
            if not media_url or media_url in seen:
                continue
            ext = determine_ext(media_url)
            if ext in ('m3u8', 'mp4') or '.m3u8' in media_url:
                seen.add(media_url)
                candidates.append(media_url)

        if any('.m3u8' in media_url for media_url in candidates):
            candidates = [u for u in candidates if '.m3u8' in u or determine_ext(u) == 'mp4']

        formats, subtitles = [], {}
        for media_url in candidates:
            ext = determine_ext(media_url)
            if ext == 'mp4' and '.m3u8' not in media_url:
                formats.append({
                    'url': media_url,
                    'ext': 'mp4',
                    'http_headers': headers,
                    'impersonate': True,
                })
                continue
            m3u8_doc = self._download_webpage(
                media_url, video_id, 'Downloading m3u8 information',
                headers=headers, impersonate=True, fatal=False)
            if not m3u8_doc or not m3u8_doc.lstrip().startswith('#EXTM3U'):
                continue
            hls_fmts, hls_subs = self._parse_m3u8_formats_and_subtitles(
                m3u8_doc, media_url, ext='mp4', m3u8_id='hls',
                video_id=video_id, headers=headers)
            for f in hls_fmts:
                f.setdefault('http_headers', headers)
                f.setdefault('impersonate', True)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
            if formats:
                break

        duration = parse_duration(self._search_regex(
            r'\bduration\s*:\s*["\']([^"\']+)["\']', decoded, 'duration', default=None))
        thumbnail = url_or_none(self._search_regex(
            r'\bimage\s*:\s*["\']([^"\']+)["\']', decoded, 'thumbnail', default=None))
        return formats, subtitles, duration, thumbnail

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        embed_url = self._extract_embed_url(webpage, url)
        if not embed_url:
            raise ExtractorError('No player embed found', expected=True)

        formats, subtitles, duration, thumbnail = self._extract_player_formats(
            embed_url, video_id)
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'title': (
                self._html_search_regex(
                    r'<h1[^>]+class=["\']entry-title["\'][^>]*>([^<]+)',
                    webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)
                or video_id),
            'description': (
                self._og_search_description(webpage, default=None)
                or self._html_search_meta('description', webpage, default=None)),
            'thumbnail': (
                url_or_none(self._html_search_meta('thumbnailUrl', webpage, default=None))
                or self._og_search_thumbnail(webpage, default=None)
                or thumbnail),
            'duration': parse_duration(
                self._html_search_meta('duration', webpage, default=None)) or duration,
            'timestamp': parse_iso8601(
                self._html_search_meta('uploadDate', webpage, default=None)),
            'cast': orderedSet(re.findall(
                r'https?://(?:www\.)?sexbjcam\.com/actor/[^"\']+"[^>]*>([^<]+)', webpage)) or None,
            'categories': orderedSet(re.findall(
                r'https?://(?:www\.)?sexbjcam\.com/category/[^"\']+"[^>]*title=["\']([^"\']+)', webpage)) or None,
            'tags': orderedSet(re.findall(
                r'https?://(?:www\.)?sexbjcam\.com/tag/[^"\']+"[^>]*title=["\']([^"\']+)', webpage)) or None,
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': {'Referer': embed_url},
            'impersonate': True,
        }
