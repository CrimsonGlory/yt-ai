import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    join_nonempty,
    orderedSet,
    parse_duration,
    parse_iso8601,
    remove_end,
    unescapeHTML,
    url_or_none,
)


class JavSubbedIE(InfoExtractor):
    IE_NAME = 'javsubbed'
    IE_DESC = 'javsubbed.net'
    _VALID_URL = (
        r'https?://(?:www\.)?javsubbed\.net/'
        r'(?!(?:categor(?:y|ies)|tags?|page|search|actors?|studios|'
        r'feed|comments|wp-(?:json|content|admin|includes))(?:/|$|[?#]))'
        r'(?P<id>[^/?#]+)/?(?:[?#]|$)'
    )
    _TESTS = [
        {
            'url': 'https://javsubbed.net/yuj-073-eng-sub-the-day-i-taught-my-sons-classmate-what-a-grown-up-date-is-like/',
            'md5': 'd927a6ac73b76ab4182e81e40078045b',
            'info_dict': {
                'id': 'yuj-073-eng-sub-the-day-i-taught-my-sons-classmate-what-a-grown-up-date-is-like',
                'ext': 'mp4',
                'title': 'YUJ-073 Eng Sub. The Day I Taught My Son’s Classmate What a Grown-Up Date Is Like.',
                'description': 'YUJ-073 English Sub. A woman is approached again by her son’s longtime friend, now an adult, and agrees to spend a day together as their feelings resurface.',
                'thumbnail': r're:https://bunny-wp-pullzone-jbuqyeg20y\.b-cdn\.net/wp-content/uploads/.+\.jpg',
                'timestamp': 1788112560,
                'upload_date': '20260830',
                'uploader': 'kimochi',
                'cast': ['Ono Rinka'],
                'categories': ['Attackers', 'English Subbed', 'Hardsub'],
                'tags': ['Date', 'Drama', 'Married Woman', 'Mature Woman', 'Sale items', 'Single work', 'Slut'],
                'age_limit': 18,
            },
            'params': {
                'format': 'best[format_id^=emturbovid]',
                'fixup': 'never',
            },
        },
        {
            'url': 'http://javsubbed.net/ipx-850-there-was-a-record-breaking-downpour-during-the-business-trip-so-i-ended-up-sharing-a-room-with-my-subordinate/',
            'only_matching': True,
        },
        {
            'url': 'https://www.javsubbed.net/yuj-073-eng-sub-the-day-i-taught-my-sons-classmate-what-a-grown-up-date-is-like/',
            'only_matching': True,
        },
    ]

    @staticmethod
    def _host_id(url):
        host = urllib.parse.urlparse(url).hostname or 'host'
        parts = host.split('.')
        return parts[-2] if len(parts) >= 2 else host

    def _source_urls(self, webpage):
        urls = []
        for attrs in re.findall(r'<a\b([^>]+)>', webpage):
            if 'no-link' not in attrs and 'myLink' not in attrs:
                continue
            href = url_or_none(
                unescapeHTML(
                    self._search_regex(r'\bhref=["\'](https?://[^"\']+)', attrs, 'source href', default='') or None,
                ),
            )
            if not href:
                continue
            host = (urllib.parse.urlparse(href).hostname or '').lower()
            if host == 'javsubbed.net' or host.endswith('.javsubbed.net'):
                continue
            urls.append(href)
        return orderedSet(urls)

    def _meta_links(self, html, kind):
        names = []
        for attrs, inner in re.findall(
            rf'<a\b([^>]*href="https?://(?:www\.)?javsubbed\.net/{kind}/[^"]+"[^>]*)>(.*?)</a>', html,
        ):
            name = unescapeHTML(
                self._search_regex(r'\btitle="([^"]+)"', attrs, 'name', default='') or '',
            ).strip() or clean_html(inner)
            if name:
                names.append(name)
        return orderedSet(names) or None

    def _extract_via_host_ie(self, embed_url):
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

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        formats, subtitles, duration = [], {}, None
        for embed_url in self._source_urls(webpage):
            format_id = self._host_id(embed_url)
            try:
                host_info = self._extract_via_host_ie(embed_url)
            except (ExtractorError, KeyError, TypeError, ValueError, IndexError, AttributeError):
                continue
            if not host_info:
                continue
            fmts, subs = self._formats_from_info(host_info, format_id)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
            duration = duration or float_or_none(host_info.get('duration'))

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        title = (
            self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage)
        )
        if title:
            title = remove_end(remove_end(title, ' – JAVSUBBED.net'), ' - JAVSUBBED.net').strip() or title

        about = (
            self._search_regex(r'(?s)id="video-about"[^>]*>(.*)class="under-video-block"', webpage, 'about', default='')
            or ''
        )
        iso_duration = parse_duration(self._html_search_meta('duration', webpage, default=None))

        return {
            'id': video_id,
            'title': title,
            'description': (
                self._html_search_regex(
                    r'(?s)class="desc\s*"[^>]*>\s*(?:<p>)?(.+?)</(?:p|div)>', about, 'description', default=None,
                )
                or self._html_search_meta('description', webpage, default=None)
                or self._og_search_description(webpage, default=None)
            ),
            'thumbnail': (
                self._og_search_thumbnail(webpage, default=None)
                or self._html_search_meta('thumbnailUrl', webpage, default=None)
            ),
            'duration': duration or iso_duration or None,
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage, default=None)),
            'uploader': self._html_search_meta('author', webpage, default=None),
            'cast': self._meta_links(about, 'actor'),
            'categories': self._meta_links(about, 'category'),
            'tags': self._meta_links(about, 'tag'),
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles or None,
        }
