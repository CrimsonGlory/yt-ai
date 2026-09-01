import base64
import random
import re
import string
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    determine_ext,
    float_or_none,
    join_nonempty,
    merge_dicts,
    orderedSet,
    parse_count,
    remove_end,
    unescapeHTML,
    url_or_none,
)


class JavGuruIE(InfoExtractor):
    IE_NAME = 'javguru'
    IE_DESC = 'jav.guru'
    _VALID_URL = r'https?://(?:www\.)?jav\.guru/(?P<id>\d+)/(?P<display_id>[^/?#]+)/?'
    _TESTS = [
        {
            'url': 'https://jav.guru/1046418/start-601-it-seems-that-rui-chan-from-miss-a-university-got-a-job-offer-as-a-female-announcer-through-her-pillow-talk/',
            'md5': '3eee6c43911407324302898dcd33b373',
            'info_dict': {
                'id': '1046418',
                'ext': 'mp4',
                'display_id': 'start-601-it-seems-that-rui-chan-from-miss-a-university-got-a-job-offer-as-a-female-announcer-through-her-pillow-talk',
                'title': '[START-601] It seems that Rui-chan from Miss A University got a job offer as a female announcer through her pillow talk.',
                'thumbnail': r're:https://cdn\.javmiku\.com/wp-content/uploads/.+\.jpg',
                'duration': 8165.21,
                'timestamp': 1788210448,
                'upload_date': '20260831',
                'view_count': int,
                'cast': ['Ichinomiya Rui'],
                'categories': ['1080p', 'HD', 'JAV'],
                'tags': ['Beautiful Girl', 'Facials', 'Female College Student', 'Humiliation', 'Slender'],
                'age_limit': 18,
            },
            'params': {'format': 'playmogo'},
        },
        {
            'url': 'https://jav.guru/224264/mond-237-longing-female-boss-mao-hamasaki/',
            'only_matching': True,
        },
        {
            'url': 'https://www.jav.guru/1046418/start-601-it-seems-that-rui-chan-from-miss-a-university-got-a-job-offer-as-a-female-announcer-through-her-pillow-talk/',
            'only_matching': True,
        },
    ]

    @staticmethod
    def _host_id(url):
        host = urllib.parse.urlparse(url).hostname or 'host'
        parts = host.split('.')
        return parts[-2] if len(parts) >= 2 else host

    def _decode_iframe_urls(self, webpage):
        urls = []
        for encoded in re.findall(r'"iframe_url"\s*:\s*"([^"]+)"', webpage):
            try:
                decoded = base64.b64decode(encoded).decode()
            except (OSError, TypeError, ValueError, UnicodeDecodeError):
                continue
            decoded = url_or_none(decoded)
            if decoded:
                urls.append(decoded)
        return orderedSet(urls)

    def _gateway_url(self, iframe_url):
        parsed = urllib.parse.urlparse(iframe_url)
        query = urllib.parse.parse_qs(parsed.query)
        for key, values in query.items():
            if not re.fullmatch(r'[a-z]d', key) or not values:
                continue
            token = values[0]
            if not token:
                continue
            return urllib.parse.urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, '', urllib.parse.urlencode({f'{key[0]}r': token[::-1]}), ''),
            )
        return None

    def _extract_dood_format(self, embed_url, webpage, video_id, format_id):
        token = self._search_regex(r"[?&]token=([a-z0-9]+)[&\']", webpage, 'dood token', default=None)
        pass_md5 = self._search_regex(r'(/pass_md5[^\'"]*)', webpage, 'dood pass_md5', default=None)
        if not token or not pass_md5:
            return None
        headers = {'Referer': embed_url}
        try:
            media_prefix = self._download_webpage(
                urllib.parse.urljoin(embed_url, pass_md5),
                video_id,
                'Downloading DoodStream URL',
                headers=headers,
                impersonate=True)
        except ExtractorError:
            return None
        media_prefix = media_prefix.strip()
        if not media_prefix.startswith('http'):
            media_prefix = urllib.parse.urljoin(embed_url, media_prefix)
        return {
            'url': ''.join(
                (
                    media_prefix,
                    *(random.choice(string.ascii_letters + string.digits) for _ in range(10)),
                    f'?token={token}&expiry={int(time.time() * 1000)}',
                ),
            ),
            'ext': 'mp4',
            'format_id': format_id,
            'http_headers': headers,
            'impersonate': True,
        }

    def _extract_packed_formats(self, webpage, embed_url, video_id, format_id):
        packed = self._search_regex(r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default=None)
        if not packed:
            return [], {}, None
        try:
            decoded = decode_packed_codes(packed)
        except (AttributeError, TypeError, ValueError):
            return [], {}, None

        formats, subtitles, seen = [], {}, set()
        headers = {'Referer': embed_url}
        for media_url in re.findall(r'https?://[^\'"\\\s<>]+', decoded):
            media_url = url_or_none(unescapeHTML(media_url.rstrip('\\,;')))
            if not media_url or media_url in seen:
                continue
            ext = determine_ext(media_url)
            is_hls = ext == 'm3u8' or '.m3u8' in media_url
            if not (is_hls or ext == 'mp4'):
                continue
            seen.add(media_url)
            if is_hls:
                try:
                    m3u8_doc = self._download_webpage(
                        media_url, video_id, 'Downloading m3u8 information',
                        headers=headers, impersonate=True)
                except ExtractorError:
                    continue
                hls_fmts, hls_subs = self._parse_m3u8_formats_and_subtitles(
                    m3u8_doc, media_url, 'mp4', m3u8_id=format_id,
                    headers=headers, video_id=video_id)
                for fmt in hls_fmts:
                    fmt.setdefault('http_headers', {}).update(headers)
                    fmt['impersonate'] = True
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
            else:
                formats.append(
                    {
                        'url': media_url,
                        'ext': 'mp4',
                        'format_id': format_id,
                        'http_headers': headers,
                        'impersonate': True,
                    },
                )

        duration = float_or_none(
            self._search_regex(r'\bduration["\']?\s*:\s*["\']?(\d+(?:\.\d+)?)', decoded, 'duration', default=None),
        )
        return formats, subtitles, duration

    def _extract_via_host_ie(self, embed_url, video_id):
        skipped = {self.ie_key(), 'Generic'}
        for ie in self._downloader._ies.values():
            ie_key = ie.ie_key()
            if ie_key in skipped or not ie.working() or not ie.suitable(embed_url):
                continue
            try:
                info = self._downloader.get_info_extractor(ie_key).extract(embed_url)
            except ExtractorError:
                continue
            if isinstance(info, dict) and (info.get('formats') or info.get('url')):
                return info
        return None

    def _formats_from_info(self, info, format_id):
        formats, subtitles = [], info.get('subtitles') or {}
        if info.get('formats'):
            for fmt in info['formats']:
                fmt = dict(fmt)
                fmt['format_id'] = join_nonempty(format_id, fmt.get('format_id'))
                formats.append(fmt)
        elif info.get('url'):
            formats.append(
                {
                    'url': info['url'],
                    'ext': info.get('ext') or determine_ext(info['url'], 'mp4'),
                    'format_id': format_id,
                    'http_headers': info.get('http_headers'),
                    'impersonate': info.get('impersonate'),
                },
            )
        return formats, subtitles

    def _extract_embed_formats(self, embed_url, webpage, video_id):
        format_id = self._host_id(embed_url)
        formats, subtitles, duration = [], {}, None

        dood = self._extract_dood_format(embed_url, webpage, video_id, format_id)
        if dood:
            formats.append(dood)

        packed_fmts, packed_subs, packed_duration = self._extract_packed_formats(
            webpage, embed_url, video_id, format_id,
        )
        formats.extend(packed_fmts)
        self._merge_subtitles(packed_subs, target=subtitles)
        duration = packed_duration

        if not formats:
            jw = self._find_jwplayer_data(webpage, video_id)
            if jw:
                try:
                    jw_info = self._parse_jwplayer_data(jw, video_id, require_title=False)
                except ExtractorError:
                    jw_info = None
                if isinstance(jw_info, dict):
                    jw_fmts, jw_subs = self._formats_from_info(jw_info, format_id)
                    formats.extend(jw_fmts)
                    self._merge_subtitles(jw_subs, target=subtitles)
                    duration = duration or float_or_none(jw_info.get('duration'))

        if not formats:
            for entry in self._parse_html5_media_entries(embed_url, webpage, video_id) or []:
                formats.extend(entry.get('formats') or [])
                self._merge_subtitles(entry.get('subtitles') or {}, target=subtitles)

        if not formats:
            host_info = self._extract_via_host_ie(embed_url, video_id)
            if host_info:
                host_fmts, host_subs = self._formats_from_info(host_info, format_id)
                formats.extend(host_fmts)
                self._merge_subtitles(host_subs, target=subtitles)
                duration = duration or float_or_none(host_info.get('duration'))

        return formats, subtitles, duration

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id, impersonate=True)

        if '<title>Just a moment...</title>' in webpage:
            raise ExtractorError('Cloudflare challenge; try again with impersonation (curl_cffi)', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)

        formats, subtitles, duration = [], {}, None
        for iframe_url in self._decode_iframe_urls(webpage):
            gateway = self._gateway_url(iframe_url)
            if not gateway:
                continue
            try:
                res = self._download_webpage_handle(
                    gateway,
                    video_id,
                    f'Downloading {self._host_id(iframe_url)} stream',
                    headers={'Referer': iframe_url},
                    impersonate=True)
            except ExtractorError:
                continue
            embed_page, urlh = res
            embed_url = urlh.url
            try:
                fmts, subs, dur = self._extract_embed_formats(embed_url, embed_page, video_id)
            except (ExtractorError, KeyError, TypeError, ValueError, IndexError, AttributeError):
                continue
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
            duration = duration or dur

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        title = (
            self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
            or json_ld.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage)
        )
        if title:
            title = re.split(r'\s*[⋅•*]\s*Jav Guru', title, maxsplit=1)[0].strip()
            title = remove_end(title, ' Japanese porn Tube').strip() or title

        info_html = (
            self._search_regex(r'(?s)<div class="infoleft">(.*?)</ul>', webpage, 'movie information', default='') or ''
        )

        def _meta_links(kind, html):
            return (
                orderedSet(
                    unescapeHTML(name.strip())
                    for name in re.findall(rf'href="https?://(?:www\.)?jav\.guru/{kind}/[^"]+"[^>]*>([^<]+)', html)
                    if name.strip()
                )
                or None
            )

        thumbnail = self._og_search_thumbnail(webpage, default=None) or url_or_none(
            self._html_search_regex(
                r'class="large-screenimg"\s*>\s*<img[^>]+src="([^"]+)"', webpage, 'thumbnail', default=None,
            ),
        )

        return merge_dicts(
            {
                'id': video_id,
                'display_id': display_id,
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'view_count': parse_count(self._search_regex(r'([\d,]+)\s*views', webpage, 'view count', default=None)),
                'cast': _meta_links('actress', info_html) or _meta_links('actor', info_html),
                'categories': _meta_links('category', info_html),
                'tags': _meta_links('tag', info_html),
                'age_limit': 18,
                'formats': formats,
                'subtitles': subtitles or None,
            },
            json_ld,
        )
