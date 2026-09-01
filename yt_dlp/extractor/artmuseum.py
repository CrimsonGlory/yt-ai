import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    clean_html,
    extract_attributes,
    int_or_none,
    join_nonempty,
    parse_duration,
    remove_end,
    unescapeHTML,
    update_url,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class ArtMuseumIE(InfoExtractor):
    IE_NAME = 'artmuseum'
    IE_DESC = 'Museum of Modern Art in Warsaw (MSN) / Filmoteka Muzeum'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?(?:archiwum\.)?artmuseum\.pl/
        (?:(?:en|pl|de)/)?
        (?:prace|artworks|filmoteka/praca)/
        (?P<id>[\w.-]+)/?(?:$|[?#])
    '''
    _TESTS = [{
        'url': 'https://artmuseum.pl/prace/msn-f-dep-470',
        'md5': '35d17aa92b0b2baed155ac77f673f4e0',
        'info_dict': {
            'id': 'msn-f-dep-470',
            'ext': 'mp4',
            'title': 'Ojej, boli mnie noga',
            'thumbnail': r're:https://api-sf\.artmuseum\.pl/uploads/files/.+',
            'duration': 152,
            'release_year': 1990,
            'creators': ['Józef Robakowski'],
            'artists': ['Józef Robakowski'],
            'artist': 'Józef Robakowski',
        },
    }, {
        'url': 'https://archiwum.artmuseum.pl/en/filmoteka/praca/robakowski-jozef-test',
        'info_dict': {
            'id': 'robakowski-jozef-test',
            'ext': 'mp4',
            'title': 'Test',
            'description': 'md5:bb57f96b1c78633a5cc2db2a21c25666',
            'thumbnail': r're:https://archiwum\.artmuseum\.pl/public/upload/filmoteka/.+',
            'duration': 344,
            'release_year': 1971,
            'creators': ['Józef Robakowski'],
            'artists': ['Józef Robakowski'],
            'artist': 'Józef Robakowski',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://artmuseum.pl/en/artworks/msn-f-dep-470',
        'only_matching': True,
    }, {
        'url': 'https://artmuseum.pl/pl/prace/msn-f-dep-470',
        'only_matching': True,
    }, {
        'url': 'https://artmuseum.pl/en/filmoteka/praca/robakowski-jozef-test',
        'only_matching': True,
    }, {
        'url': 'https://artmuseum.pl/pl/filmoteka/praca/robakowski-jozef-test',
        'only_matching': True,
    }]
    _MEDIA_URL_RE = re.compile(
        r'https?://media\d+\.artmuseum\.pl/video/(?P<height>\d+)p(?:_webM)?/(?P<hash>[0-9a-f]{32})\.(?P<ext>mp4|webm)')
    _FILM_LINK_KEY_RE = re.compile(r'h(?P<height>\d+)_(?P<ext>mp4|webm)')

    @staticmethod
    def _https_url(url):
        url = url_or_none(url)
        if not url:
            return None
        if urllib.parse.urlparse(url).scheme == 'http':
            return update_url(url, scheme='https')
        return url

    @staticmethod
    def _decode_shifted_url(encoded):
        if not encoded or not isinstance(encoded, str):
            return None
        return url_or_none(''.join(chr(ord(c) - 1) for c in encoded))

    @staticmethod
    def _parse_runtime(value):
        if value is None:
            return None
        value = re.sub(r'\\(.)', r'\1', unescapeHTML(str(value))).strip()
        mobj = re.fullmatch(r"(\d+)'(\d{1,2})\"", value)
        if mobj:
            return int(mobj.group(1)) * 60 + int(mobj.group(2))
        return parse_duration(value)

    def _formats_from_film_links(self, film_links):
        formats = []
        for key, entries in (film_links or {}).items():
            mobj = self._FILM_LINK_KEY_RE.fullmatch(key)
            if not mobj:
                continue
            height, ext = int(mobj.group('height')), mobj.group('ext')
            for media_url in traverse_obj(entries, (..., 'url', {self._https_url})):
                formats.append({
                    'url': media_url,
                    'format_id': f'{height}p-{ext}',
                    'height': height,
                    'ext': ext,
                })
        return formats

    def _formats_from_media_hash(self, webpage, media_hash):
        formats, seen = [], set()
        for mobj in self._MEDIA_URL_RE.finditer(webpage):
            if mobj.group('hash') != media_hash:
                continue
            media_url = self._https_url(mobj.group(0))
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)
            height, ext = int(mobj.group('height')), mobj.group('ext')
            formats.append({
                'url': media_url,
                'format_id': f'{height}p-{ext}',
                'height': height,
                'ext': ext,
            })
        return formats

    def _formats_from_html5(self, url, webpage, video_id):
        formats, media_hash = [], None
        for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
            for fmt in entry.get('formats') or []:
                media_url = self._https_url(fmt.get('url'))
                if not media_url:
                    continue
                fmt = {**fmt, 'url': media_url}
                mobj = self._MEDIA_URL_RE.search(media_url)
                if mobj:
                    media_hash = mobj.group('hash')
                    fmt.setdefault('format_id', f'{mobj.group("height")}p-{mobj.group("ext")}')
                    fmt.setdefault('height', int(mobj.group('height')))
                    fmt.setdefault('ext', mobj.group('ext'))
                formats.append(fmt)
        if media_hash:
            formats.extend(self._formats_from_media_hash(webpage, media_hash))
        return formats

    def _extract_exhibit_page(self, url, webpage, video_id):
        exhibit = traverse_obj(
            self._search_nextjs_v13_data(webpage, video_id, fatal=False),
            (..., {dict}, lambda k, v: k == 'exhibit' and isinstance(v, dict) and v.get('slug') == video_id),
            get_all=False) or {}

        formats = self._formats_from_film_links(exhibit.get('filmLinks'))
        if not formats:
            formats = self._formats_from_html5(url, webpage, video_id)
        if not formats:
            self.raise_no_formats(
                'No video is available for this artwork', expected=True, video_id=video_id)

        lang = 'en' if '/artworks/' in urllib.parse.urlparse(url).path or '/en/' in url else 'pl'
        tr = (
            traverse_obj(exhibit, ('translations', lang, {dict}))
            or traverse_obj(exhibit, ('translations', ..., {dict}), get_all=False)
            or {})
        creators = traverse_obj(exhibit, ('artists', ..., 'title', {str}))
        thumbnail = self._https_url(urljoin(
            'https://api-sf.artmuseum.pl',
            traverse_obj(exhibit, ('mainResource', 'media', 'url', {str}))))

        return {
            'id': video_id,
            'title': (
                traverse_obj(tr, ('title', {str}))
                or traverse_obj(exhibit, ('title', {str}))
                or self._og_search_title(webpage, default=None)),
            'alt_title': clean_html(traverse_obj(tr, ('titles', 0, {str}))) or None,
            'description': join_nonempty(
                *traverse_obj(tr, ('descriptions', ..., {clean_html})), delim='\n') or None,
            'thumbnail': thumbnail or self._og_search_thumbnail(webpage, default=None),
            'duration': self._parse_runtime(tr.get('dimensions')),
            'release_year': int_or_none(exhibit.get('dateFrom')) or int_or_none(tr.get('date')),
            'creators': creators or None,
            'artist': join_nonempty(*creators, delim=', ') or None,
            'formats': formats,
        }

    def _extract_filmoteka(self, url, video_id):
        if 'archiwum.artmuseum.pl' not in urllib.parse.urlparse(url).netloc:
            url = re.sub(r'://(?:www\.)?artmuseum\.pl/', '://archiwum.artmuseum.pl/', url, count=1)
        webpage = self._download_webpage(url, video_id)

        player = self._search_regex(
            r'<div[^>]+id=["\']video-player["\'][^>]*>', webpage, 'player', default='', group=0)
        attrs = extract_attributes(player) if player else {}
        sources = self._parse_json(attrs.get('data-sources') or '{}', video_id, fatal=False) or {}

        formats = []
        for quality, files in sources.items() if isinstance(sources, dict) else ():
            if not isinstance(files, dict):
                continue
            height = int_or_none(str(quality).rstrip('pP'))
            for fmt_key, encoded in files.items():
                media_url = self._https_url(self._decode_shifted_url(encoded))
                if not media_url:
                    continue
                ext = 'webm' if 'webm' in fmt_key else 'mp4'
                formats.append({
                    'url': media_url,
                    'format_id': join_nonempty(quality, ext, delim='-'),
                    'height': height,
                    'ext': ext,
                })

        if not formats:
            self.raise_no_formats(
                'No video is available for this artwork', expected=True, video_id=video_id)

        title = (
            self._html_search_regex(r'<h4>([^<]+)</h4>', webpage, 'title', default=None)
            or remove_end(self._og_search_title(webpage, default=''), ' - Museum of Modern Art in Warsaw')
            or None)
        artist = self._html_search_regex(
            r'<h2>\s*<a[^>]+>([^<]+)', webpage, 'artist', default=None)

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': url_or_none(urljoin(url, attrs.get('data-poster'))) or self._og_search_thumbnail(
                webpage, default=None),
            'duration': self._parse_runtime(self._search_regex(
                r'Duration:\s*([^<]+)', webpage, 'duration', default=None)),
            'release_year': int_or_none(self._search_regex(
                r'Year:\s*(\d{4})', webpage, 'year', default=None)),
            'creators': [artist] if artist else None,
            'artist': artist,
            'formats': formats,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if '/filmoteka/praca/' in urllib.parse.urlparse(url).path:
            return self._extract_filmoteka(url, video_id)
        webpage = self._download_webpage(url, video_id)
        return self._extract_exhibit_page(url, webpage, video_id)
