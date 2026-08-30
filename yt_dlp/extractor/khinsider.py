import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    get_element_html_by_id,
    int_or_none,
    qualities,
    unescapeHTML,
    unified_strdate,
    url_or_none,
    urljoin,
)


class KHInsiderBaseIE(InfoExtractor):
    _HOME = 'https://downloads.khinsider.com'
    _AUDIO_EXTS = ('mp3', 'ogg', 'm4a', 'wav', 'flac')

    def _extract_formats(self, webpage, page_url):
        quality = qualities(self._AUDIO_EXTS)
        formats, seen = [], set()
        for m in re.finditer(
                r'''(?is)(?:href|src)\s*=\s*(["'])(?P<url>(?:https?:)?[^"']+\.(?:mp3|flac|ogg|wav|m4a)(?:\?[^"']*)?)\1''',
                webpage):
            media_url = url_or_none(urljoin(page_url, unescapeHTML(m.group('url'))))
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)
            ext = determine_ext(media_url)
            formats.append({
                'url': media_url,
                'ext': ext,
                'format_id': ext,
                'vcodec': 'none',
                'quality': quality(ext),
            })
        return formats


class KHInsiderIE(KHInsiderBaseIE):
    IE_NAME = 'khinsider'
    IE_DESC = 'KHInsider'
    _VALID_URL = r'https?://(?:www\.)?downloads\.khinsider\.com/game-soundtracks/album/(?P<album>[^/?#]+)/(?P<id>[^/?#]+\.(?:mp3|flac|ogg|wav|m4a))'
    _TESTS = [{
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/super-mario-bros/01.%2520Ground%2520Theme.mp3',
        'md5': '8b65ec4e69dd939f272b8cc1243d5071',
        'info_dict': {
            'id': '01. Ground Theme',
            'ext': 'flac',
            'title': 'Ground Theme',
            'track': 'Ground Theme',
            'track_number': 1,
            'album': 'Super Mario Bros. (Family Computer, NES) (gamerip) (1985)',
        },
    }, {
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/super-mario-bros/02.%2520Underground%2520Theme.mp3',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        raw_id = urllib.parse.unquote(urllib.parse.unquote(self._match_valid_url(url).group('id')))
        display_id = re.sub(r'\.(?:mp3|flac|ogg|wav|m4a)$', '', raw_id, flags=re.I)

        webpage = self._download_webpage(url, display_id)
        formats = self._extract_formats(webpage, url)
        if not formats:
            self.raise_no_formats('No MP3 or FLAC download found', expected=True, video_id=display_id)

        title = self._html_search_regex(
            r'Song name:\s*<b>([^<]+)', webpage, 'title', default=None) or display_id

        return {
            'id': display_id,
            'title': title,
            'track': title,
            'track_number': int_or_none(self._search_regex(
                r'^(\d+)', display_id, 'track number', default=None)),
            'album': self._html_search_regex(
                r'Album name:\s*<b>([^<]+)', webpage, 'album', default=None),
            'formats': formats,
        }


class KHInsiderAlbumIE(KHInsiderBaseIE):
    IE_NAME = 'khinsider:album'
    IE_DESC = 'KHInsider albums'
    _VALID_URL = r'https?://(?:www\.)?downloads\.khinsider\.com/game-soundtracks/album/(?P<id>[^/?#]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/super-mario-bros',
        'info_dict': {
            'id': 'super-mario-bros',
            'title': 'Super Mario Bros.',
            'description': 'md5:dba2a4afdd264797c9466176d34be09d',
            'thumbnail': r're:https?://.+\.(?:png|jpe?g)',
            'release_year': 1985,
            'uploader': 'Blushock',
            'upload_date': '20230315',
        },
        'playlist_mincount': 21,
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://downloads.khinsider.com/game-soundtracks/album/super-mario-bros/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        album_id = self._match_id(url)
        webpage = self._download_webpage(url, album_id)

        title = self._html_search_regex(
            r'<h2>([^<]+)</h2>', webpage, 'title', default=None) or album_id.replace('-', ' ').title()
        description = clean_html(self._search_regex(
            r'<h2>\s*Description\s*</h2>\s*<p>(.*?)</p>',
            webpage, 'description', default=None, flags=re.DOTALL))
        thumbnail = url_or_none(self._search_regex(
            r'<div class="albumImage">\s*<a href="([^"]+)"',
            webpage, 'thumbnail', default=None))
        upload_date = unified_strdate(re.sub(
            r'(\d+)(?:st|nd|rd|th)', r'\1',
            self._html_search_regex(
                r'Date Added:\s*<b>([^<]+)', webpage, 'upload date', default='') or ''))

        songlist = get_element_html_by_id('songlist', webpage) or ''
        entries, seen = [], set()
        for href, raw_title in re.findall(
                r'<a[^>]+href="(/game-soundtracks/album/[^"]+)"[^>]*>(.*?)</a>',
                songlist, flags=re.DOTALL):
            href = unescapeHTML(href)
            if href in seen:
                continue
            seen.add(href)
            slug = urllib.parse.unquote(href.rstrip('/').rsplit('/', 1)[-1]).lower()
            if slug in ('change_log', 'get_app') or href.rstrip('/').endswith(f'/album/{album_id}'):
                continue
            track_title = re.sub(r'\s+', ' ', clean_html(raw_title) or '').strip()
            if re.fullmatch(r'\d+:\d{2}(?::\d{2})?', track_title) or re.search(r'[\d.]+\s*MB\s*$', track_title):
                track_title = None
            entries.append(self.url_result(
                urljoin(self._HOME, href), KHInsiderIE, video_title=track_title))

        if not entries:
            self.raise_no_formats('No tracks found', expected=True, video_id=album_id)

        return self.playlist_result(
            entries, album_id, title, description,
            thumbnail=thumbnail,
            release_year=int_or_none(self._html_search_regex(
                r'Year:\s*<b>(\d{4})</b>', webpage, 'year', default=None)),
            uploader=self._html_search_regex(
                r'Uploaded by:\s*<a[^>]+>([^<]+)', webpage, 'uploader', default=None),
            upload_date=upload_date)
