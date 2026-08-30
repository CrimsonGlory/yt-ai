import base64
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    orderedSet,
    parse_duration,
    parse_iso8601,
    smuggle_url,
    unescapeHTML,
    unsmuggle_url,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class CloseLoadIE(InfoExtractor):
    IE_NAME = 'closeload'
    IE_DESC = 'Closeload'
    _VALID_URL = r'https?://(?:www\.)?closeload\.top/video/embed/(?P<id>[\w-]+)'
    _EMBED_REGEX = [
        r'<iframe[^>]+(?:\bsrc|\bdata-src)=(["\'])(?P<url>https?://(?:www\.)?closeload\.top/video/embed/[^"\']+)\1',
    ]
    _TESTS = [
        {
            'url': 'https://closeload.top/video/embed/Am35Tr7zon1/',
            'only_matching': True,
        },
        {
            'url': 'https://closeload.top/video/embed/mERcz1kID6Z/?imdb_id=tt15203646',
            'only_matching': True,
        },
    ]
    _HEADERS = {
        'Referer': 'https://closeload.top/',
        'Origin': 'https://closeload.top',
    }

    @staticmethod
    def _atob(value):
        pad = '=' * ((4 - len(value) % 4) % 4)
        return base64.b64decode(value + pad).decode('latin-1')

    @staticmethod
    def _rot_letters(value, shift):
        chars = []
        for char in value:
            code = ord(char)
            if 65 <= code <= 90:
                chars.append(chr((code - 65 + shift) % 26 + 65))
            elif 97 <= code <= 122:
                chars.append(chr((code - 97 + shift) % 26 + 97))
            else:
                chars.append(char)
        return ''.join(chars)

    def _decode_hls_url(self, webpage, video_id):
        source_var = self._search_regex(
            r'sources\s*:\s*\[\s*\{\s*file\s*:\s*(\w+)', webpage, 'jwplayer source variable',
        )
        func_name, packed = self._search_regex(
            rf'var\s+{re.escape(source_var)}\s*=\s*(\w+)\s*\((\[.*?\])\)\s*;', webpage, 'encoded source', group=(1, 2),
        )
        parts = self._parse_json(packed, video_id, transform_source=js_to_json)
        if not isinstance(parts, list) or not parts:
            raise ExtractorError('Unable to parse encoded HLS source')

        func_body = self._search_regex(
            rf'function\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{(.*?)\breturn\s+\w+\s*;',
            webpage,
            'source decoder',
            flags=re.DOTALL,
        )
        value = ''.join(str(part) for part in parts)
        for op in re.finditer(
            r'result\s*=\s*atob\(\s*result\s*\)'
            r'|result\s*=\s*result\.split\([^)]*\)\.reverse\(\)\.join\([^)]*\)'
            r'|result\s*=\s*result\.replace\(/\[a-zA-Z\]/g,\s*function\s*\(\w+\)\s*\{[^}]+?\+\s*(\d+)\s*\)\s*%\s*26',
            func_body,
        ):
            token = op.group(0)
            if 'atob' in token:
                value = self._atob(value)
            elif 'reverse' in token:
                value = value[::-1]
            else:
                value = self._rot_letters(value, int(op.group(1)))

        acc = int(self._search_regex(r'\bacc\s*=\s*(\d+)', func_body, 'decoder seed'))
        add = int(self._search_regex(r'acc\s*=\s*\(\s*acc\s*\+\s*(\d+)\s*\)\s*%\s*256', func_body, 'decoder increment'))
        decoded = bytearray()
        for byte in value.encode('latin-1'):
            acc = (acc + add) % 256
            decoded.append(byte ^ acc)
            acc = (acc + byte) % 256
        try:
            hls_url = decoded.decode()
        except UnicodeDecodeError:
            raise ExtractorError('Unable to decode Closeload HLS URL')
        return url_or_none(hls_url)

    def _real_extract(self, url):
        url, smuggled = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, impersonate=True, headers={'Referer': smuggled.get('referer') or self._HEADERS['Referer']},
        )

        hls_url = self._decode_hls_url(webpage, video_id)
        if not hls_url:
            raise ExtractorError('Unable to decode Closeload HLS URL')

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls', headers=self._HEADERS,
        )
        for fmt in formats:
            fmt.setdefault('http_headers', {}).update(self._HEADERS)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        tracks = (
            self._parse_json(
                self._search_regex(r'\btracks\s*:\s*(\[.*?])', webpage, 'subtitles', default='[]'),
                video_id,
                fatal=False,
            )
            or []
        )
        lang_map = {
            'english': 'en',
            'portuguese': 'pt',
            'spanish': 'es',
            'turkish': 'tr',
            'french': 'fr',
            'german': 'de',
            'arabic': 'ar',
            'russian': 'ru',
            'japanese': 'ja',
            'korean': 'ko',
            'chinese': 'zh',
            'hindi': 'hi',
        }
        for track in traverse_obj(tracks, lambda _, v: v.get('kind') == 'captions' and url_or_none(v.get('file'))):
            lang = lang_map.get((track.get('label') or '').lower()) or track.get('label') or 'und'
            subtitles.setdefault(lang, []).append({'url': track['file']})

        title = json_ld.get('title') or self._html_extract_title(webpage, default=None) or video_id
        thumbnail = url_or_none(
            self._search_regex(
                r'\bimage\s*:\s*(["\'])(?P<url>https?://.+?)\1', webpage, 'thumbnail', default=None, group='url',
            ),
        ) or json_ld.get('thumbnail')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': json_ld.get('duration')
            or parse_duration(self._search_regex(r'"duration"\s*:\s*"([^"]+)"', webpage, 'duration', default=None)),
            'timestamp': json_ld.get('timestamp')
            or parse_iso8601(self._search_regex(r'"uploadDate"\s*:\s*"([^"]+)"', webpage, 'upload date', default=None)),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': self._HEADERS,
        }


class RidoMoviesIE(InfoExtractor):
    IE_NAME = 'ridomovies'
    IE_DESC = 'RidoMovies'
    _VALID_URL = (
        r'https?://(?:www\.)?ridomovies\.(?:tv|su)/(?:[a-z]{2}/)?'
        r'(?:movies?|tv|film[ei]?|pelicula|dianying|eiga)/'
        r'(?P<id>[^/?#]+)(?:/season-(?P<season>\d+)/episode-(?P<episode>\d+))?'
    )
    _TESTS = [
        {
            'url': 'https://ridomovies.tv/movie/boss-2025',
            'md5': 'c6803aad1ae8865b2e507e7832d19577',
            'info_dict': {
                'id': 'Am35Tr7zon1',
                'ext': 'mp4',
                'display_id': 'boss-2025',
                'title': 'Boss',
                'description': 'md5:c4ba6c032e29f737a351852c52504b7b',
                'thumbnail': r're:https?://ridomovies\.su/uploads/movies/.+',
                'duration': 5940,
                'timestamp': 1787999748,
                'upload_date': '20260829',
                'subtitles': {
                    'en': 'count:1',
                    'pt': 'count:1',
                },
            },
        },
        {
            'url': 'https://ridomovies.su/movie/boss-2025',
            'only_matching': True,
        },
        {
            'url': 'https://ridomovies.tv/movies/extinction-2023',
            'only_matching': True,
        },
        {
            'url': 'https://ridomovies.su/tv/bad-monkey-2024/season-1/episode-1',
            'only_matching': True,
        },
        {
            'url': 'https://ridomovies.su/tv/bad-monkey-2024',
            'only_matching': True,
        },
        {
            'url': 'https://ridomovies.su/es/pelicula/boss-2025',
            'only_matching': True,
        },
    ]

    def _extract_embed_ids(self, webpage):
        videos = (
            self._parse_json(
                unescapeHTML(
                    self._search_regex(
                        r'''\bdata-videos=(["'])(?P<json>\[.*?])\1''', webpage, 'videos', default='[]', group='json',
                    ),
                ),
                None,
                fatal=False,
            )
            or []
        )
        embed_ids = orderedSet(traverse_obj(videos, (..., ('video_id', 'video'), {str})))
        embed_ids.extend(re.findall(r'closeload\.top/video/embed/([\w-]+)', unescapeHTML(webpage)))
        return orderedSet(embed_ids)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        slug, season, episode = mobj.group('id', 'season', 'episode')
        season_number, episode_number = int_or_none(season), int_or_none(episode)
        display_id = slug if episode_number is None else f'{slug}-s{season_number}e{episode_number}'

        webpage, urlh = self._download_webpage_handle(url, display_id, impersonate=True)
        url = urlh.url

        json_ld = self._search_json_ld(webpage, display_id, default={})
        title = (
            json_ld.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage, default=None)
            or display_id
        )
        info = {
            'display_id': display_id,
            'title': re.sub(r'^Watch\s+', '', title).strip() or display_id,
            'description': json_ld.get('description') or self._og_search_description(webpage),
            'thumbnail': json_ld.get('thumbnail') or self._og_search_thumbnail(webpage),
            'duration': json_ld.get('duration'),
            'timestamp': json_ld.get('timestamp'),
            'season_number': season_number,
            'episode_number': episode_number,
        }

        embed_ids = self._extract_embed_ids(webpage)
        if embed_ids:
            return self.url_result(
                smuggle_url(f'https://closeload.top/video/embed/{embed_ids[0]}/', {'referer': url}),
                CloseLoadIE,
                embed_ids[0],
                url_transparent=True,
                **info,
            )

        if episode_number is None:
            episode_paths = orderedSet(
                path for path in re.findall(r'href="([^"]+/season-\d+/episode-\d+)"', webpage) if slug in path
            )
            if episode_paths:
                return self.playlist_from_matches(
                    episode_paths, display_id, info['title'], getter=lambda path: urljoin(url, path), ie=self,
                )

        self.raise_no_formats('No Closeload embed found', expected=True, video_id=display_id)
