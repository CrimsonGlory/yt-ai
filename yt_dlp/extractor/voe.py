import base64
import binascii
import codecs
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    js_to_json,
    parse_duration,
    parse_filesize,
    remove_end,
    traverse_obj,
    url_or_none,
    urljoin,
)


class VoeIE(InfoExtractor):
    IE_NAME = 'voe'
    IE_DESC = 'voe.sx'
    _VALID_URL = r'https?://(?:www\.)?voe\.sx/(?:e/)?(?P<id>[a-z0-9]{12})(?:[/?#]|$)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?voe\.sx/e/[a-z0-9]{12})']
    _TESTS = [
        {
            'url': 'https://voe.sx/fi3fqtyh7932',
            'md5': 'a56d72d21b000516f2b172e33fa78e3a',
            'info_dict': {
                'id': 'fi3fqtyh7932',
                'ext': 'mp4',
                'title': 'Slayers S02E02 German DVDRip x264-AST4u',
                'thumbnail': r're:https?://[^/]+/cache/fi3fqtyh7932_storyboard_L2\.jpg',
                'duration': 1332,
            },
        },
        {
            'url': 'https://voe.sx/e/fi3fqtyh7932',
            'only_matching': True,
        },
        {
            'url': 'https://www.voe.sx/e/fi3fqtyh7932',
            'only_matching': True,
        },
    ]
    _OBFUSCATION_MARKERS = ('@$', '^^', '~@', '%?', '*~', '!!', '#&')
    _BAIT_HINTS = (
        'test-videos.co.uk',
        'sample-videos.com',
        'bigbuckbunny',
        'big_buck_bunny',
    )

    @staticmethod
    def _is_bait(url):
        if not url:
            return True
        lowered = url.lower()
        return any(hint in lowered for hint in VoeIE._BAIT_HINTS)

    @staticmethod
    def _b64decode_text(value):
        if not value:
            return None
        cleaned = re.sub(r'\\+', '', value)
        padded = cleaned + '=' * (-len(cleaned) % 4)
        try:
            return base64.b64decode(padded).decode()
        except (ValueError, TypeError, binascii.Error, UnicodeDecodeError):
            return None

    @classmethod
    def _shift_chars(cls, text, shift=3):
        try:
            return ''.join(chr(ord(c) - shift) for c in text)
        except ValueError:
            return None

    @classmethod
    def _deobfuscate_shifted(cls, obfuscated, *, strip_underscores=False):
        step = codecs.decode(obfuscated, 'rot_13')
        if strip_underscores:
            step = step.replace('_', '')
        else:
            for marker in cls._OBFUSCATION_MARKERS:
                step = step.replace(marker, '')
        decoded = cls._b64decode_text(step)
        if not decoded:
            return None
        shifted = cls._shift_chars(decoded)
        if not shifted:
            return None
        text = cls._b64decode_text(shifted[::-1])
        if not text:
            return None
        return text

    def _payload_to_config(self, payload, video_id):
        if isinstance(payload, str):
            parsed = self._parse_json(payload, video_id, fatal=False)
            if isinstance(parsed, dict):
                payload = parsed
            else:
                mp4_url = self._search_regex(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', payload, 'mp4 url', default=None)
                hls_url = self._search_regex(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', payload, 'hls url', default=None)
                payload = {'direct_access_url': mp4_url, 'source': hls_url}
        if not isinstance(payload, dict):
            return None
        return payload

    def _extract_player_config(self, webpage, video_id):
        for mobj in re.finditer(r'<script[^>]+type=["\']application/json["\'][^>]*>([^<]+)</script>', webpage):
            parsed = self._parse_json(mobj.group(1).strip(), video_id, fatal=False)
            if not (isinstance(parsed, list) and parsed and isinstance(parsed[0], str)):
                continue
            decoded = self._deobfuscate_shifted(parsed[0])
            config = self._payload_to_config(decoded, video_id)
            if config:
                return config

        mkgma = self._search_regex(r'MKGMa\s*=\s*["\']([^"\']+)["\']', webpage, 'MKGMa payload', default=None)
        if mkgma:
            config = self._payload_to_config(self._deobfuscate_shifted(mkgma, strip_underscores=True), video_id)
            if config:
                return config

        a168c = self._search_regex(r'a168c\s*=\s*["\']([^"\']+)["\']', webpage, 'a168c payload', default=None)
        if a168c:
            reversed_text = (self._b64decode_text(a168c) or '')[::-1]
            config = self._payload_to_config(reversed_text, video_id)
            if config:
                return config

        sources = self._search_json(
            r'var\s+sources\s*=', webpage, 'sources', video_id, transform_source=js_to_json, fatal=False, default=None,
        )
        if isinstance(sources, dict):
            return sources
        return None

    def _download_player_webpage(self, url, video_id):
        webpage, urlh = self._download_webpage_handle(url, video_id)
        player_url = urlh.url
        for _ in range(5):
            if self._extract_player_config(webpage, video_id):
                return webpage, player_url
            redirect = self._search_regex(
                r'''window\.location\.href\s*=\s*(["\'])(?P<url>https?://.+?)\1''',
                webpage,
                'js redirect',
                default=None,
                group='url',
            )
            if not redirect:
                break
            redirect = urljoin(player_url, redirect)
            webpage, urlh = self._download_webpage_handle(redirect, video_id, 'Following player redirect')
            player_url = urlh.url
        return webpage, player_url

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, player_url = self._download_player_webpage(url, video_id)

        if re.search(r'(?i)404\s*-\s*not found|file not found|video not found', webpage):
            raise ExtractorError('Video not found', expected=True)

        config = self._extract_player_config(webpage, video_id) or {}
        headers = {'Referer': player_url}
        formats, subtitles = [], {}

        hls_url = url_or_none(traverse_obj(config, 'source', 'hls'))
        if self._is_bait(hls_url):
            hls_url = None
        if hls_url:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False, headers=headers,
            )
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)

        mp4_url = url_or_none(traverse_obj(config, 'direct_access_url', 'mp4'))
        if self._is_bait(mp4_url):
            mp4_url = None
        if mp4_url:
            formats.append(
                {
                    'url': mp4_url,
                    'format_id': 'http',
                    'ext': determine_ext(mp4_url, 'mp4'),
                    'http_headers': headers,
                    # Progressive MP4 is the same encode as the HLS ladder and avoids MPEG-TS fixup.
                    'preference': 1,
                },
            )

        if not formats:
            raise ExtractorError('Unable to extract video URL', expected=True)

        title = (
            traverse_obj(config, 'title', expected_type=str)
            or self._og_search_title(webpage, default=None)
            or self._html_search_meta(('og:title', 'twitter:title'), webpage, default=None)
            or remove_end(
                self._html_extract_title(webpage, default=''), ' - VOE | Content Delivery Network (CDN) & Video Cloud',
            )
            or video_id
        )
        title = re.sub(r'^Watch\s+', '', title).strip() or video_id

        return {
            'id': video_id,
            'title': title,
            'thumbnail': (url_or_none(traverse_obj(config, 'thumbnail')) or self._og_search_thumbnail(webpage)),
            'duration': parse_duration(
                self._search_regex(r'>Length</div>\s*<div[^>]*>\s*([0-9:]+)', webpage, 'duration', default=None),
            ),
            'filesize_approx': parse_filesize(
                self._search_regex(
                    r'<b>\s*\d+p\s*</b>\s*-\s*(\d+(?:\.\d+)?\s*[KMGT]B)', webpage, 'filesize', default=None,
                ),
            ),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
        }
