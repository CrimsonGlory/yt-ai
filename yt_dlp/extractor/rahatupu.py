import base64
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    orderedSet,
    parse_duration,
    parse_iso8601,
    remove_end,
    try_call,
    url_or_none,
)


class RahatupuIE(InfoExtractor):
    IE_NAME = 'rahatupu'
    IE_DESC = 'rahatupu.net'
    _VALID_URL = [
        r'https?://(?:www\.)?rahatupu\.net/(?!(?:category|categories|tag|actors?|page|author|comments|feed|search|wp-(?:admin|content|includes|json))(?:/|$))(?P<id>[^/?#]+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?rahatupu\.net/\?(?:[^#]*&)?p=(?P<id>\d+)',
    ]
    _TESTS = [{
        'url': 'https://rahatupu.net/aunty-wa-harrier-kujifira-na-vidole-zake-kwa-kuma-yake/',
        'md5': '9316035944bcd6089c888a9465a8e6be',
        'info_dict': {
            'id': '1448',
            'ext': 'mp4',
            'display_id': 'aunty-wa-harrier-kujifira-na-vidole-zake-kwa-kuma-yake',
            'title': 'Aunty wa Harrier kujifira na vidole zake kwa kuma yake',
            'description': 'Aunty wa Harrier kujifira na vidole zake kwa kuma yake...KUMA za kenya ni tamu na ni rahatupu kutomba',
            'thumbnail': r're:https?://rahatupu\.net/wp-content/uploads/.+\.(?:png|jpe?g)',
            'duration': 75,
            'timestamp': 1629279617,
            'upload_date': '20210818',
            'uploader': 'RTupu',
            'age_limit': 18,
            'categories': ['Granny'],
            'tags': ['bbw', 'ebony pussy', 'granny xxx', 'kenyan-porn', 'kumatamu', 'kutombana-kenya', 'sugar mummy'],
        },
    }, {
        'url': 'https://rahatupu.net/?p=1448',
        'only_matching': True,
    }, {
        'url': 'https://www.rahatupu.net/aunty-wa-harrier-kujifira-na-vidole-zake-kwa-kuma-yake/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        url_id = urllib.parse.unquote(self._match_id(url))
        webpage = self._download_webpage(url, url_id)
        video_id = self._search_regex(r'\bpostid-(\d+)', webpage, 'post id', default=url_id)
        display_id = urllib.parse.unquote(
            self._search_regex(
                r'rahatupu\.net/([^/?#]+)', self._og_search_url(webpage, default='') or url,
                'slug', default=url_id))

        headers = {'Referer': url}
        formats = []
        video_url = url_or_none(self._html_search_meta('contentURL', webpage, default=None))
        if video_url:
            formats.append({
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
                'http_headers': headers,
            })
        if not formats:
            for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
                formats.extend(entry.get('formats') or [])
        if not formats:
            player_q = self._search_regex(
                r'player-x\.php\?q=([A-Za-z0-9+/=]+)', webpage, 'player payload', default=None)
            player_html = try_call(
                lambda: urllib.parse.unquote(base64.b64decode(f'{player_q}===').decode()),
            ) if player_q else None
            if player_html:
                for entry in self._parse_html5_media_entries(url, player_html, video_id) or []:
                    formats.extend(entry.get('formats') or [])
        if not formats:
            raise ExtractorError('No video source found', expected=True)
        for f in formats:
            f.setdefault('http_headers', headers)

        tags_html = self._search_regex(
            r'<div class="tags-list">([\s\S]*?)</div>', webpage, 'tags list', default='')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': (
                self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)
                or remove_end(self._html_extract_title(webpage, default=''), ' – Rahatupu Blog')
                or None
            ),
            'description': (
                self._html_search_meta('description', webpage, default=None)
                or self._og_search_description(webpage, default=None)
            ),
            'thumbnail': (
                url_or_none(self._html_search_meta('thumbnailUrl', webpage, default=None))
                or self._og_search_thumbnail(webpage, default=None)
            ),
            'duration': parse_duration(self._html_search_meta('duration', webpage, default=None)),
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage, default=None)),
            'uploader': self._html_search_regex(
                r'itemprop="author"[^>]*>\s*<meta[^>]+itemprop="name"[^>]+content="([^"]+)"',
                webpage, 'uploader', default=None),
            'age_limit': 18,
            'categories': orderedSet(re.findall(
                r'href="[^"]*/category/[^"]*"[^>]*>(?:<[^>]+>)*([^<]+)', tags_html)) or None,
            'tags': orderedSet(re.findall(
                r'href="[^"]*/tag/[^"]*"[^>]*>(?:<[^>]+>)*([^<]+)', tags_html)) or None,
            'formats': formats,
            'http_headers': headers,
        }
