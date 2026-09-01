import re
import urllib.parse

from .common import InfoExtractor
from .voe import VoeIE
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    merge_dicts,
    orderedSet,
    parse_count,
    unescapeHTML,
    unified_strdate,
    url_or_none,
)


class GaystreamIE(InfoExtractor):
    IE_DESC = 'gaystream.pw'
    _VALID_URL = (
        r'https?://(?:www\.)?gaystream\.pw/video/(?P<id>\d+)'
        r'(?:/(?P<display_id>[^/?#]+))?(?:\.html)?'
    )
    _AD_HOSTS = (
        'magsrv.com',
        'exoclick.com',
        'pemsrv.com',
        'tsyndicate.com',
    )
    _TESTS = [
        {
            'url': 'https://gaystream.pw/video/69913/beau-mance-nicholas-michaels-fucking-the-baseball-jock',
            'md5': '1970099944c88e4212c82162be1b7ea0',
            'info_dict': {
                'id': '69913',
                'ext': 'mp4',
                'display_id': 'beau-mance-nicholas-michaels-fucking-the-baseball-jock',
                'title': 'Beau Mance & Nicholas Michaels – Fucking The Baseball Jock',
                'description': 'md5:bc06ed89d431ec497ecef1c633b092ae',
                'thumbnail': r're:https?://.+\.(?:webp|jpg|jpeg|png)',
                'age_limit': 18,
                'channel': 'CollegeBoyPhysicals',
                'cast': ['Beau Mance', 'Nicholas Michaels'],
                'categories': ['Bareback'],
                'upload_date': '20260901',
                'view_count': int,
                'like_count': int,
            },
            'add_ie': [VoeIE.ie_key()],
        },
        {
            'url': 'https://gaystream.pw/video/33195/jax-thirio-nico-coopa-flip-fuck.html',
            'only_matching': True,
        },
        {
            'url': 'https://www.gaystream.pw/video/69913/beau-mance-nicholas-michaels-fucking-the-baseball-jock',
            'only_matching': True,
        },
    ]

    def _is_ad_host(self, host):
        host = (host or '').lower()
        return any(host == domain or host.endswith(f'.{domain}') for domain in self._AD_HOSTS)

    def _is_host_embed(self, url):
        url = url_or_none(unescapeHTML(url))
        if not url:
            return False
        parsed = urllib.parse.urlparse(url)
        if self._is_ad_host(parsed.hostname):
            return False
        parts = [p for p in parsed.path.split('/') if p]
        # Require /e/<id>, /v/<id>, /d/<id>, etc. Skip dead hosts like https://host/e/
        return len(parts) >= 2

    def _extract_embed_urls(self, webpage):
        urls = []
        for regex in (
            r'document\.getElementById\("ifr"\)\.src="(https?://[^"]+)"',
            r'<iframe[^>]+src="(https?://[^"]+)"',
        ):
            urls.extend(re.findall(regex, webpage))
        return [u for u in orderedSet(urls) if self._is_host_embed(u)]

    def _extract_packed_embed(self, embed_url, video_id):
        webpage = self._download_webpage(
            embed_url, video_id, 'Downloading host embed', fatal=False, headers={'Referer': 'https://gaystream.pw/'},
        )
        if not webpage:
            return [], {}
        packed = self._search_regex(r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default=None)
        if not packed:
            return [], {}
        decoded = decode_packed_codes(packed)
        m3u8_url = url_or_none(
            self._search_regex(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', decoded, 'm3u8 URL', default=None),
        )
        if not m3u8_url:
            return [], {}
        return self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False, headers={'Referer': embed_url},
        )

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        embed_urls = self._extract_embed_urls(webpage)
        if not embed_urls:
            raise ExtractorError('No video hosts found; the file host may have been removed', expected=True)

        title = (
            self._html_search_regex(r'<h1[^>]*class="entry-title"[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or display_id
            or video_id
        )
        description = self._html_search_regex(
            r'<div class="expandit readmore">(.*?)</div>', webpage, 'description', default=None, flags=re.DOTALL,
        ) or self._og_search_description(webpage, default=None)
        footer = self._search_regex(
            r'<footer class="entry-footer">(.*?)</footer>', webpage, 'entry footer', default='', flags=re.DOTALL,
        )
        meta = self._search_regex(
            r'<div class="entry-meta">(.*?)</div>', webpage, 'entry meta', default='', flags=re.DOTALL,
        )

        info = {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'age_limit': 18,
            'channel': self._html_search_regex(
                r'<span class="entry-channel">\s*<a[^>]*>([^<]+)', webpage, 'channel', default=None,
            ),
            'cast': orderedSet(re.findall(r'<a class="entry-tag"[^>]*>([^<]+)', footer)) or None,
            'categories': orderedSet(re.findall(r'<a class="entry-category"[^>]*>([^<]+)', footer)) or None,
            'upload_date': unified_strdate(
                self._html_search_regex(r'<span class="entry-date">([^<]+)', webpage, 'upload date', default=None),
            ),
            'view_count': parse_count(
                self._search_regex(r'([\d.,]+(?:\.\d+)?\s*[KMBkmb]?)\s*views', meta, 'view count', default=None),
            ),
            'like_count': parse_count(
                self._search_regex(r'([\d.,]+(?:\.\d+)?\s*[KMBkmb]?)\s*likes', meta, 'like count', default=None),
            ),
        }

        voe_url = next((embed for embed in embed_urls if VoeIE.suitable(embed)), None)
        if voe_url:
            try:
                host_info = self._downloader.get_info_extractor(VoeIE.ie_key()).extract(voe_url)
            except ExtractorError as e:
                self.report_warning(f'VOE extraction failed: {e}')
            else:
                if isinstance(host_info, dict) and (host_info.get('formats') or host_info.get('url')):
                    return merge_dicts(info, host_info)

        formats, subtitles = [], {}
        for embed_url in embed_urls:
            if VoeIE.suitable(embed_url):
                continue
            fmts, subs = self._extract_packed_embed(embed_url, video_id)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if not formats:
            raise ExtractorError('No working video hosts found; the file host may have been removed', expected=True)

        return {
            **info,
            'formats': formats,
            'subtitles': subtitles,
        }
