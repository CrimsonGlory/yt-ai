from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    clean_html,
    extract_attributes,
    get_element_html_by_class,
    int_or_none,
    parse_age_limit,
    parse_duration,
    str_or_none,
    unified_timestamp,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class TFOBaseIE(InfoExtractor):
    _BASE_URL = 'https://www.tfo.org'
    _GEO_COUNTRIES = ['CA']
    # JWPlayer CloudFront geo-blocks by real client IP; X-Forwarded-For is ignored
    _GEO_BYPASS = False


class TFOIE(TFOBaseIE):
    IE_NAME = 'tfo'
    IE_DESC = 'Télévision française de l\'Ontario'

    _VALID_URL = (
        r'https?://(?:www\.)?tfo\.org/(?:bande-annonce|episode|film|regarder|titre)(?:/[\w-]+)+/(?P<id>(?:GP|P)?\d+)')
    _TESTS = [{
        'url': 'https://www.tfo.org/regarder/pouletosaure-rex-partie-1-2/GP639511',
        'skip': 'geo-restricted to Canada; JWPlayer CDN returns HTTP 403 Unauthorized request location (X-Forwarded-For is ignored)',
        'info_dict': {
            'id': 'GP639511',
            'ext': 'mp4',
            'title': 'Pouletosaure Rex - Partie 1 & 2',
            'age_limit': 0,
            'alt_title': 'pouletosaure-rex-partie-1-2',
            'description': 'md5:15b91dc31a5ebd91c2baf6e69c88e268',
            'duration': 1320,
            'episode': 'Pouletosaure Rex - Partie 1 & 2',
            'episode_id': 'episode-1',
            'episode_number': 1,
            'genres': ['6 à 9 ans'],
            'release_date': '20250406',
            'release_timestamp': 1743897600,
            'release_year': 2023,
            'season': 'Saison 1',
            'season_id': 'saison-1',
            'season_number': 1,
            'series': 'Dino Dex',
            'series_id': '003051136',
            'tags': ['G'],
            'thumbnail': r're:https?://.+\.(?:jpg|png|webp)',
        },
    }, {
        'url': 'https://www.tfo.org/episode/passeport-pour-le-monde/saison-2/episode-1/vietnam-dans-loeil-du-dragon/GP938523',
        'only_matching': True,
    }, {
        'url': 'https://www.tfo.org/titre/entre-les-lignes/GP704192',
        'only_matching': True,
    }, {
        'url': 'https://www.tfo.org/film/a-nous-la-liberte/852897',
        'only_matching': True,
    }, {
        'url': 'https://www.tfo.org/bande-annonce/dino-dex/P3052261',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        product = self._download_json(
            f'{self._BASE_URL}/endpoints/episode/{video_id}', video_id)

        if traverse_obj(product, ('type', {str})) == 'Collection':
            slug = traverse_obj(product, ('slug', {str})) or video_id
            return self.url_result(
                f'{self._BASE_URL}/serie/{slug}/{video_id}', TFOSeriesIE, video_id)

        m3u8_url = traverse_obj(product, ('playlist_url', {url_or_none}))
        if not m3u8_url:
            webpage = self._download_webpage(
                urljoin(self._BASE_URL, traverse_obj(product, ('videoUrl', {str})) or url),
                video_id)
            m3u8_url = url_or_none(extract_attributes(
                get_element_html_by_class('full-screen-video-player', webpage) or '',
            ).get('data-video-playlist'))
        if not m3u8_url:
            raise ExtractorError('Unable to extract m3u8 URL', expected=True)

        try:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
            raise

        def season_label(prefix):
            return lambda x: f'{prefix}{x}' if x else None

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(product, {
                'title': ('name', {clean_html}, filter),
                'age_limit': (
                    'rating', {lambda x: x[0] if isinstance(x, list) and x else x},
                    {parse_age_limit}),
                'alt_title': ('slug', {str_or_none}),
                'description': (('longDescription', 'description'), {clean_html}, filter, any),
                'duration': ('duration', {parse_duration}),
                'episode': ('episodeName', {clean_html}, filter),
                'episode_id': ('episodeNumber', {int_or_none}, {season_label('episode-')}),
                'episode_number': ('episodeNumber', {int_or_none}),
                'genres': ('genres', ..., {clean_html}, {lambda x: x if x and x != '-' else None}, filter),
                'release_timestamp': ('state', 'begin', {unified_timestamp}),
                'release_year': ('production_year', -1, {int_or_none}),
                'season': ('seasonNumber', {int_or_none}, {season_label('Saison ')}),
                'season_id': ('seasonNumber', {int_or_none}, {season_label('saison-')}),
                'season_number': ('seasonNumber', {int_or_none}),
                'series': ((('collection', 'name'), ('serie', 'name'), 'name'), {clean_html}, filter, any),
                'series_id': ('collection', 'id', {str_or_none}),
                'tags': (
                    'rating', {lambda x: [x] if isinstance(x, str) else x},
                    ..., {clean_html}, filter),
                'thumbnail': (('bannerUrl', 'imageUrl'), {url_or_none}, any),
            }),
        }


class TFOSeriesIE(TFOBaseIE):
    IE_NAME = 'tfo:series'

    _VALID_URL = r'https?://(?:www\.)?tfo\.org/series?/[\w-]+(?:/saison-(?P<season>\d+))?/(?P<id>(?:GP)?\d+)'
    _TESTS = [{
        'url': 'https://www.tfo.org/serie/super-mini-monstres/002748228',
        'info_dict': {
            'id': '002748228',
            'title': 'Super mini monstres',
        },
        'playlist_count': 44,
    }, {
        'url': 'https://www.tfo.org/series/super-mini-monstres/002748228',
        'only_matching': True,
    }, {
        'url': 'https://www.tfo.org/serie/chacun-son-ile/saison-2/002981471',
        'skip': 'video gone',
        'info_dict': {
            'id': '002981471',
            'title': 'Chacun son île | Saison 2',
        },
        'playlist_mincount': 13,
    }]

    def _real_extract(self, url):
        season_number, series_id = self._match_valid_url(url).group('season', 'id')
        webpage = self._download_webpage(url, series_id)
        series = self._parse_json(extract_attributes(
            get_element_html_by_class('episode-listing-container', webpage) or '',
        ).get('data-series') or '{}', series_id)

        season_path = (
            lambda _, v: str(v.get('season_name')) == season_number
        ) if season_number else ...
        entries = [
            self.url_result(x, TFOIE)
            for x in traverse_obj(series, (
                'seasons', season_path, 'products', ...,
                'videoUrl', {urljoin(f'{self._BASE_URL}/')},
            ))
        ]

        title = traverse_obj(series, ('name', {clean_html}))
        if season_number and title:
            title = f'{title} | Saison {season_number}'

        return self.playlist_result(entries, series_id, title)
