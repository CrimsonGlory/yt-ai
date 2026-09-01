import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    extract_attributes,
    int_or_none,
    parse_duration,
    remove_end,
    unescapeHTML,
    unified_strdate,
    unified_timestamp,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class DeutscheKinemathekIE(InfoExtractor):
    IE_NAME = 'deutschekinemathek'
    IE_DESC = 'Deutsche Kinemathek'
    _VALID_URL = r'https?://(?:www\.)?deutsche-kinemathek\.de/[a-z]{2}/online/streaming/(?P<id>[^/?#]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://www.deutsche-kinemathek.de/de/online/streaming/zaertlichkeiten',
        'md5': '57e9c471ac575494ea958ff8985ca0f1',
        'info_dict': {
            'id': 'zaertlichkeiten',
            'ext': 'mp4',
            'title': 'Zärtlichkeiten',
            'description': 'md5:a1c4facf4a748ada561439153fdc8458',
            'thumbnail': r're:https://player\.syecontentdelivery\.de/content/.+\.jpg',
            'duration': 1740,
            'release_year': 1985,
            'timestamp': 1778803200,
            'upload_date': '20260515',
            'creators': ['Maria Lang'],
            'cast': ['Verena Rudolph', 'Renate Kretschmar'],
        },
    }, {
        'url': 'https://www.deutsche-kinemathek.de/en/online/streaming/tendernesses',
        'only_matching': True,
    }, {
        'url': 'https://www.deutsche-kinemathek.de/en/online/streaming/darling-berlin',
        'only_matching': True,
    }]

    def _extract_itemprops(self, webpage):
        props = {}
        for tag in re.findall(r'<meta\b[^>]*>', webpage):
            attrs = extract_attributes(tag)
            prop = attrs.get('itemprop')
            if not prop:
                continue
            value = unescapeHTML(attrs.get('content') or '') or None
            props.setdefault(prop, []).append(value)
        return props

    def _extract_player_url(self, webpage):
        for tag in re.findall(r'<iframe\b[^>]*>', webpage):
            attrs = extract_attributes(tag)
            src = url_or_none(attrs.get('data-src') or attrs.get('src'))
            if src and 'syecontentdelivery.de' in src:
                return src
        return None

    def _extract_player_subtitles(self, player_page, player_url):
        subtitles = {}
        for tag in re.findall(r'<track\b[^>]*>', player_page):
            attrs = extract_attributes(tag)
            kind = attrs.get('kind')
            if kind and kind not in ('subtitles', 'captions'):
                continue
            src = attrs.get('src')
            if not src:
                continue
            src = url_or_none(urljoin(player_url, src))
            if not src:
                continue
            lang = attrs.get('srclang') or attrs.get('lang') or attrs.get('label') or 'und'
            subtitles.setdefault(lang, []).append({'url': src})
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        itemprops = self._extract_itemprops(webpage)

        content_url = traverse_obj(itemprops, ('contentUrl', 0, {url_or_none})) or url_or_none(
            self._search_regex(
                r'(https?://vod\d+\.syecontentdelivery\.de/videos/[^"\']+\.m3u8)',
                webpage, 'm3u8 URL', default=None))
        player_url = self._extract_player_url(webpage)

        formats, subtitles = [], {}
        if content_url and determine_ext(content_url) == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                content_url, video_id, 'mp4', m3u8_id='hls')
        elif content_url:
            formats = [{'url': content_url, 'ext': determine_ext(content_url, 'mp4')}]

        if player_url:
            player_page = self._download_webpage(
                player_url, video_id, note='Downloading player page', fatal=False)
            if player_page:
                self._merge_subtitles(
                    self._extract_player_subtitles(player_page, player_url),
                    target=subtitles)
                if not formats:
                    for entry in self._parse_html5_media_entries(
                            player_url, player_page, video_id, m3u8_id='hls') or []:
                        formats.extend(entry.get('formats') or [])
                        self._merge_subtitles(entry.get('subtitles') or {}, target=subtitles)

        if not formats:
            raise ExtractorError(
                'No video available; this film may have left the streaming program',
                expected=True)

        title = traverse_obj(itemprops, ('name', 0, {str})) or remove_end(
            self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
            ' | Deutsche Kinemathek')

        return {
            'id': video_id,
            'title': title,
            'description': traverse_obj(itemprops, ('description', 0, {str})),
            'thumbnail': traverse_obj(itemprops, ('thumbnailUrl', 0, {url_or_none})),
            'duration': parse_duration(traverse_obj(itemprops, ('duration', 0, {str}))),
            'release_year': int_or_none(traverse_obj(itemprops, ('copyrightyear', 0))),
            'timestamp': unified_timestamp(traverse_obj(itemprops, ('datepublished', 0, {str}))),
            'upload_date': unified_strdate(traverse_obj(itemprops, ('datepublished', 0, {str}))),
            'creators': traverse_obj(itemprops, ('director', ..., {str}, filter)) or None,
            'cast': traverse_obj(itemprops, ('actor', ..., {str}, filter)) or None,
            'formats': formats,
            'subtitles': subtitles or None,
        }


class DeutscheKinemathekPlaylistIE(InfoExtractor):
    IE_NAME = 'deutschekinemathek:playlist'
    IE_DESC = 'Deutsche Kinemathek streaming program'
    _VALID_URL = r'https?://(?:www\.)?deutsche-kinemathek\.de/(?:(?P<lang>[a-z]{2})/)?(?:online/)?streaming/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://www.deutsche-kinemathek.de/en/online/streaming',
        'info_dict': {
            'id': 'en-streaming',
            'title': 'Selects – the streaming program of the Kinemathek',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://www.deutsche-kinemathek.de/de/online/streaming',
        'only_matching': True,
    }, {
        'url': 'https://www.deutsche-kinemathek.de/en/streaming',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        lang = self._match_valid_url(url).group('lang') or 'de'
        playlist_id = f'{lang}-streaming'
        webpage = self._download_webpage(url, playlist_id)
        title = remove_end(
            self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
            ' | Deutsche Kinemathek')
        return self.playlist_from_matches(
            re.findall(r'href="(/[a-z]{2}/online/streaming/[^"/?#]+)"', webpage),
            playlist_id, title, getter=lambda path: urljoin(url, path),
            ie=DeutscheKinemathekIE)
