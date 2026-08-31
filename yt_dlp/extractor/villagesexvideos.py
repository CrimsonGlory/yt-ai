import base64
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    orderedSet,
    parse_count,
    parse_duration,
    parse_iso8601,
    remove_end,
    try_call,
    url_or_none,
)


class VillageSexVideosIE(InfoExtractor):
    IE_NAME = 'villagesexvideos'
    IE_DESC = 'villagesexvideos.com'
    _VALID_URL = [
        r'https?://(?:www\.)?villagesexvideos\d*\.com/(?!(?:category|categories|tag|tags|actors?|page|author|comments|feed|search|wp-(?:admin|content|includes|json))(?:/|$))(?P<id>[^/?#]+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?villagesexvideos\d*\.com/\?(?:[^#]*&)?p=(?P<id>\d+)',
    ]
    _TESTS = [{
        'url': 'https://www.villagesexvideos3.com/bhabhi-sucking-erect-dick-with-round/',
        'md5': '0eca62abff967664df78f25f5ac35151',
        'info_dict': {
            'id': '230731',
            'ext': 'mp4',
            'display_id': 'bhabhi-sucking-erect-dick-with-round',
            'title': 'Bhabhi sucking erect dick with round boobs of hers shown',
            'description': 'bhabhi sucking erect dick with round boobs of hers shown',
            'thumbnail': r're:https?://(?:www\.)?villagesexvideos\d*\.com/wp-content/uploads/.+\.(?:jpe?g|png)',
            'duration': 498,
            'timestamp': 1788190213,
            'upload_date': '20260831',
            'uploader': 'golden shower',
            'view_count': int,
            'age_limit': 18,
            'categories': ['Videos Indian Sex'],
            'tags': [
                'blowjob',
                'boobs sucking',
                'desi mms scandal Porn Videos',
                'desi sex scandal Indian Sex',
            ],
        },
    }, {
        'url': 'https://www.villagesexvideos.com/?p=230731',
        'only_matching': True,
    }, {
        'url': 'https://www.villagesexvideos.com/mallu-open-shirt-small-boobs-village-girl/',
        'only_matching': True,
    }, {
        'url': 'https://www.villagesexvideos2.com/bhabhi-sucking-erect-dick-with-round/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        url_id = urllib.parse.unquote(self._match_id(url))
        webpage = self._download_webpage(url, url_id, impersonate=True)
        video_id = self._search_regex(r'\bpostid-(\d+)', webpage, 'post id', default=url_id)
        display_id = urllib.parse.unquote(
            self._search_regex(
                r'villagesexvideos\d*\.com/([^/?#]+)',
                self._og_search_url(webpage, default='') or url,
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
                or remove_end(self._html_extract_title(webpage, default=''), ' | Village Sex Videos')
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
            'uploader': self._html_search_meta('author', webpage, default=None),
            'view_count': parse_count(self._search_regex(
                r'class="views">(?:<[^>]+>)*\s*([0-9][0-9.,KMB]*)',
                webpage, 'view count', default=None)),
            'age_limit': 18,
            'categories': orderedSet(
                t.strip() for t in re.findall(
                    r'href="[^"]*/category/[^"]*"[^>]*>(?:<[^>]+>)*([^<]+)', tags_html)
                if t.strip()) or None,
            'tags': orderedSet(
                t.strip() for t in re.findall(
                    r'href="[^"]*/tag/[^"]*"[^>]*>(?:<[^>]+>)*([^<]+)', tags_html)
                if t.strip()) or None,
            'formats': formats,
            'http_headers': headers,
        }
