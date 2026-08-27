import re

from .common import InfoExtractor
from ..networking import Request
from ..utils import (
    get_element_by_class,
    int_or_none,
    parse_http_range,
    try_call,
    url_or_none,
    urlhandle_detect_ext,
)
from ..utils.traversal import traverse_obj


class Mx3BaseIE(InfoExtractor):
    _VALID_URL_TMPL = r'https?://(?:www\.)?%s/t/(?P<id>\w+)'
    _FORMATS = [{
        'url': 'player_asset',
        'format_id': 'default',
        'quality': 0,
    }, {
        'url': 'player_asset?quality=hd',
        'format_id': 'hd',
        'quality': 1,
    }, {
        'url': 'download',
        'format_id': 'download',
        'quality': 2,
    }, {
        'url': 'player_asset?quality=source',
        'format_id': 'source',
        'quality': 2,
    }]

    def _extract_formats(self, track_id):
        formats = []
        for fmt in self._FORMATS:
            format_url = f'https://{self._DOMAIN}/tracks/{track_id}/{fmt["url"]}'
            # Site rejects HEAD (HTTP 403) but serves media on ranged GET
            urlh = self._request_webpage(
                Request(format_url, headers={'Range': 'bytes=0-0'}),
                track_id, fatal=False, expected_status=404,
                note=f'Checking for format {fmt["format_id"]}')
            if urlh and urlh.status in (200, 206):
                _, _, filesize = parse_http_range(urlh.headers.get('Content-Range'))
                formats.append({
                    **fmt,
                    'url': format_url,
                    'ext': urlhandle_detect_ext(urlh),
                    'filesize': filesize or int_or_none(urlh.headers.get('Content-Length')),
                })
        return formats

    def _real_extract(self, url):
        track_id = self._match_id(url)
        webpage = self._download_webpage(url, track_id)
        more_info = get_element_by_class('single-more-info', webpage) or webpage
        data = self._download_json(f'https://{self._DOMAIN}/t/{track_id}.json', track_id, fatal=False)

        def get_info_field(name):
            return self._html_search_regex(
                rf'<dt[^>]*>\s*{name}\s*</dt>\s*<dd[^>]*>(.*?)</dd>',
                more_info, name, default=None, flags=re.DOTALL) or self._html_search_regex(
                rf'<span[^>]*>\s*{re.escape(name)}\s*</span>\s*([^<]+)',
                more_info, name, default=None)

        return {
            'id': track_id,
            'formats': self._extract_formats(track_id),
            'genre': self._html_search_regex(
                r'<div\b[^>]+class="single-band-genre"[^>]*>([^<]+)</div>', webpage, 'genre', default=None)
            or self._html_search_regex(
                r'plays\s*[—-]\s*([^<]+?)\s*,\s*\d{4}', webpage, 'genre', default=None),
            'release_year': int_or_none(get_info_field('Year of creation')),
            'description': get_info_field('Description'),
            'tags': try_call(lambda: (get_info_field('Tags') or get_info_field('Tag')).split(', '), list) or [],
            **traverse_obj(data, {
                'title': ('title', {str}),
                'artist': (('performer_name', 'performerships', 'artist'), {str}, filter),
                'album_artist': ('artist', {str}),
                'composer': ('composer_name', {str}),
                'thumbnail': (('picture_url_xlarge', 'picture_url'), {url_or_none}),
            }, get_all=False),
        }


class Mx3IE(Mx3BaseIE):
    _DOMAIN = 'mx3.ch'
    _VALID_URL = Mx3BaseIE._VALID_URL_TMPL % re.escape(_DOMAIN)
    _TESTS = [{
        'url': 'https://mx3.ch/t/1Cru',
        'md5': '7ba09e9826b4447d4e1ce9d69e0e295f',
        'info_dict': {
            'id': '1Cru',
            'ext': 'wav',
            'artist': 'Godina',
            'artists': ['Godina'],
            'album_artist': 'Tortue Tortue',
            'album_artists': ['Tortue Tortue'],
            'genre': 'Rock',
            'genres': ['Rock'],
            'thumbnail': r're:https?://mx3\.ch/.+1-s-envoler-1\.jpg',
            'title': "S'envoler",
            'release_year': 2021,
            'tags': [],
        },
    }, {
        'url': 'https://mx3.ch/t/1LIY',
        'md5': '48293cb908342547827f963a5a2e9118',
        'info_dict': {
            'id': '1LIY',
            'ext': 'mov',
            'artist': 'Tania Kimfumu',
            'artists': ['Tania Kimfumu'],
            'album_artist': 'The Broots',
            'album_artists': ['The Broots'],
            'genre': 'Electro',
            'genres': ['Electro'],
            'thumbnail': r're:https?://mx3\.ch/.+frame_0000\.png',
            'title': 'The Broots-Larytta remix "Begging For Help"',
            'release_year': 2023,
            'tags': ['the broots', 'cassata records', 'larytta'],
        },
    }, {
        'url': 'https://mx3.ch/t/1C6E',
        'md5': '1afcd578493ddb8e5008e94bb6d97e25',
        'info_dict': {
            'id': '1C6E',
            'ext': 'wav',
            'artist': 'Alien Bubblegum',
            'artists': ['Alien Bubblegum'],
            'album_artist': 'Alien Bubblegum',
            'album_artists': ['Alien Bubblegum'],
            'genre': 'Punk',
            'genres': ['Punk'],
            'thumbnail': r're:https?://mx3\.ch/.+pandora-s-box-cover-with-title\.png',
            'title': 'Wide Awake',
            'release_year': 2021,
            'tags': ['alien bubblegum', 'bubblegum', 'alien', 'pop punk', 'poppunk'],
        },
    }]


class Mx3NeoIE(Mx3BaseIE):
    _DOMAIN = 'neo.mx3.ch'
    _VALID_URL = Mx3BaseIE._VALID_URL_TMPL % re.escape(_DOMAIN)
    _TESTS = [{
        'url': 'https://neo.mx3.ch/t/1hpd',
        'md5': '6d9986bbae5cac3296ec8813bf965eb2',
        'info_dict': {
            'id': '1hpd',
            'ext': 'wav',
            'artist': 'Kammerorchester Basel +1',
            'artists': ['Kammerorchester Basel +1'],
            'album_artist': 'Kammerorchester Basel',
            'album_artists': ['Kammerorchester Basel'],
            'composer': 'Jannik Giger',
            'composers': ['Jannik Giger'],
            'genre': 'Composition, Orchestra',
            'genres': ['Composition', 'Orchestra'],
            'title': 'Troisième œil. Für Kammerorchester (2023)',
            'thumbnail': r're:https?://neo\.mx3\.ch/.+kammerorchester-basel-group-photo-2_c_-lukasz-rajchert\.jpg',
            'release_year': 2023,
            'tags': [],
        },
    }]


class Mx3VolksmusikIE(Mx3BaseIE):
    _DOMAIN = 'volksmusik.mx3.ch'
    _VALID_URL = Mx3BaseIE._VALID_URL_TMPL % re.escape(_DOMAIN)
    _TESTS = [{
        'url': 'https://volksmusik.mx3.ch/t/Zx',
        'md5': 'dd967a7b0c1ef898f3e072cf9c2eae3c',
        'info_dict': {
            'id': 'Zx',
            'ext': 'mp3',
            'artist': 'Ländlerkapelle GrischArt',
            'artists': ['Ländlerkapelle GrischArt'],
            'album_artist': 'Ländlerkapelle GrischArt',
            'album_artists': ['Ländlerkapelle GrischArt'],
            'composer': 'Urs Glauser',
            'composers': ['Urs Glauser'],
            'genre': 'Instrumental, Graubünden',
            'genres': ['Instrumental', 'Graubünden'],
            'title': 'Chämilouf',
            'thumbnail': r're:https?://volksmusik\.mx3\.ch/.+grischart1\.jpg',
            'release_year': 2012,
            'tags': [],
        },
    }]
