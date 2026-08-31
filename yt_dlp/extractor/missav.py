import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    int_or_none,
    parse_iso8601,
    url_or_none,
)


class MissAVIE(InfoExtractor):
    IE_NAME = 'missav'
    IE_DESC = 'MissAV'
    _DOMAINS = r'(?:www\.)?missav\.(?:ai|ws|live|com|li)'
    _VALID_URL = (
        rf'https?://{_DOMAINS}/'
        r'(?:dm\d+/)?'
        r'(?:[a-z]{2,3}/)?'
        r'(?P<id>(?!actresses|makers|labels|genres|search|playlists|new|release|'
        r'saved|articles|ads|contact|history|directors|chinese-subtitle|'
        r'uncensored-leak|weekly-hot|monthly-hot|today-hot|ranking|clive|klive|'
        r'site|login|register|settings|favorites)[\w.-]+)/?(?:[?#]|$)'
    )
    _TESTS = [{
        'url': 'https://missav.ai/sw-950',
        'md5': '80db77ed889ff42dbdda5c086799d7f1',
        'info_dict': {
            'id': 'sw-950',
            'ext': 'mp4',
            'title': 'SW-950 邀請大胸勃起和臀前內褲拍攝的男士美容院。我受不了那種滿身油污、禁忌的私密按摩，就偷偷地塞進了她的體內。',
            'description': 'md5:16bb75baa83585da162ffb2290ad14d4',
            'thumbnail': r're:https?://fourhoi\.com/sw-950/.+',
            'duration': 12293,
            'timestamp': 1715220000,
            'upload_date': '20240509',
            'age_limit': 18,
        },
    }, {
        'url': 'https://missav.ai/dm39/en/sw-950',
        'only_matching': True,
    }, {
        'url': 'https://missav.ws/sw-950',
        'only_matching': True,
    }, {
        'url': 'https://missav.live/sw-950',
        'only_matching': True,
    }]

    def _enable_impersonate(self):
        # HLS native downloads do not copy format-level impersonate onto fragment
        # requests, so prefer curl_cffi for the rest of this YoutubeDL session.
        ydl = self._downloader
        available, requested = ydl._parse_impersonate_targets(True)
        if not available:
            raise ExtractorError(
                ydl._unavailable_targets_message(
                    requested, note='MissAV requires browser impersonation', is_error=True),
                expected=True)
        ydl.params['impersonate'] = ydl.params.get('impersonate') or available
        for rh in ydl._request_director.handlers.values():
            if getattr(rh, 'impersonate', False) is None:
                rh.impersonate = available

    def _extract_m3u8_url(self, webpage):
        packed = self._search_regex(
            r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default='')
        decoded = ''
        if packed:
            try:
                decoded = decode_packed_codes(packed)
            except (AttributeError, TypeError, ValueError):
                decoded = ''
        m3u8_url = url_or_none(self._search_regex(
            r'''(?x)\bsource\s*=\s*\\?['"](https?://[^\\'"]+\.m3u8)''',
            decoded, 'm3u8 URL', default=None))
        if m3u8_url:
            return m3u8_url

        video_uuid = self._search_regex(
            r'surrit\.com(?:/|\\+/)((?:[0-9a-f]{8}-){4}[0-9a-f]{12})',
            webpage, 'video uuid', default=None)
        if video_uuid:
            return f'https://surrit.com/{video_uuid}/playlist.m3u8'
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, video_id, impersonate=True)
        self._enable_impersonate()
        webpage_url = urlh.url

        if re.search(r'confiscat|ドメインの没収', webpage, re.I):
            raise ExtractorError(
                'missav.com was seized; use missav.ai, missav.ws, or missav.live',
                expected=True)
        if '<title>Just a moment...</title>' in webpage:
            raise ExtractorError(
                'Cloudflare challenge; try again with impersonation (curl_cffi)',
                expected=True)

        m3u8_url = self._extract_m3u8_url(webpage)
        if not m3u8_url:
            raise ExtractorError('No HLS source found; this URL may not be a video page', expected=True)

        parsed = urllib.parse.urlparse(webpage_url)
        origin = f'{parsed.scheme}://{parsed.hostname}'
        headers = {
            'Referer': f'{origin}/',
            'Origin': origin,
        }

        m3u8_doc = self._download_webpage(
            m3u8_url, video_id, 'Downloading m3u8 information',
            headers=headers, impersonate=True)
        formats, subtitles = self._parse_m3u8_formats_and_subtitles(
            m3u8_doc, m3u8_url, 'mp4', m3u8_id='hls', video_id=video_id, headers=headers)
        for f in formats:
            f.setdefault('http_headers', headers)
            f.setdefault('impersonate', True)

        return {
            'id': video_id,
            'title': (
                self._html_search_regex(
                    r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)
                or video_id),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': int_or_none(self._og_search_property(
                'video:duration', webpage, default=None)),
            'timestamp': parse_iso8601(self._html_search_regex(
                r'<time[^>]+datetime="([^"]+)"', webpage, 'timestamp', default=None)),
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
            'impersonate': True,
        }
