import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class KinoPoiskIE(InfoExtractor):
    _GEO_COUNTRIES = ['RU']
    _VALID_URL = r'https?://(?:(?:www\.)?kinopoisk\.ru/film/|widgets\.kinopoisk\.ru/discovery/film/)(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.kinopoisk.ru/film/81041/watch/',
        'md5': 'e935791dbe0fcce557778e2a5cbc148d',
        'info_dict': {
            'id': '81041',
            'ext': 'mp4',
            'title': 'Алеша Попович и Тугарин Змей',
            'thumbnail': r're:https?://avatars\.mds\.yandex\.net/.*',
            'view_count': int,
            'release_year': 2004,
        },
    }, {
        'url': 'https://www.kinopoisk.ru/film/81041',
        'only_matching': True,
    }, {
        'url': 'https://widgets.kinopoisk.ru/discovery/film/81041',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            f'https://widgets.kinopoisk.ru/discovery/film/{video_id}', video_id)

        data = self._parse_json(
            self._search_regex(
                r'<script[^>]+\btype=["\']application/json[^>]*>([^<]+)',
                webpage, 'data'),
            video_id, transform_source=urllib.parse.unquote)

        trailers = traverse_obj(data, ('models', 'trailers', {dict})) or {}
        preferred_id = str(traverse_obj(data, ('page', 'trailerId')) or '')
        trailer = trailers.get(preferred_id) or {}
        if str(trailer.get('filmId')) != video_id or not url_or_none(trailer.get('streamUrl')):
            trailer = next((
                t for t in trailers.values()
                if str(t.get('filmId')) == video_id and url_or_none(t.get('streamUrl'))
            ), None) or {}

        stream_url = url_or_none(trailer.get('streamUrl'))
        if not stream_url:
            raise ExtractorError('Unable to extract trailer stream', expected=True)

        formats = [
            fmt for fmt in self._extract_m3u8_formats(
                stream_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls')
            if 'redundant=' not in (fmt.get('url') or '')
        ]

        film = trailer.get('film') or {}
        thumbnail = self._proto_relative_url(traverse_obj(
            trailer,
            ('img', 'bigPreviewUrl', 'x2', {url_or_none}),
            ('img', 'bigPreviewUrl', 'x1', {url_or_none}),
            ('img', 'mediumPreviewUrl', 'x2', {url_or_none}),
            ('film', 'img', 'posterMedium', 'x2', {url_or_none}),
            ('film', 'img', 'poster', 'x2', {url_or_none}),
        ))

        return {
            'id': video_id,
            'title': film.get('title') or film.get('displayTitle') or film.get('originalTitle'),
            'thumbnail': thumbnail,
            'view_count': int_or_none(trailer.get('views')),
            'release_year': int_or_none(film.get('year')),
            'formats': formats,
        }
