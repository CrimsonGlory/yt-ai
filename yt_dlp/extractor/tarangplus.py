import functools

from .common import InfoExtractor
from ..utils import (
    OnDemandPagedList,
    clean_html,
    int_or_none,
    parse_duration,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class TarangPlusBaseIE(InfoExtractor):
    _BASE_URL = 'https://tarangplus.in'
    _API_BASE = 'https://api.tarangplus.in'
    # from https://tarangplus.in/main.*.js environment config
    _AUTH_TOKEN = '3zZmzoHg8z6SM3wpDoyw'

    def _call_api(self, path, video_id, note='Downloading JSON metadata', fatal=True, query=None):
        return self._download_json(
            f'{self._API_BASE}/{path}', video_id, note, fatal=fatal,
            headers={'Accept': 'application/json'}, query={
                'auth_token': self._AUTH_TOKEN,
                'region': 'IN',
                **(query or {}),
            })

    def _extract_item_info(self, metadata, display_id):
        return {
            'display_id': display_id,
            **traverse_obj(metadata, {
                'id': ('content_id', {str}),
                'title': (('display_title', 'title'), {str}, filter, any),
                'description': (('description', 'short_description'), {clean_html}, filter, any),
                'thumbnail': ('thumbnails', (
                    'xl_image_16_9', 'large_16_9', 'medium_16_9', 'xl_image_16_7', 'l_large',
                ), 'url', {url_or_none}, any),
                'timestamp': (('release_date_uts', 'publish_date_uts'), {int_or_none}, any),
                'media_type': (('media_type', 'theme'), {str}, filter, any),
                'categories': ('display_genres', ..., {str}),
            }),
            'duration': int_or_none(traverse_obj(metadata, 'duration')) or parse_duration(
                traverse_obj(metadata, ('duration_string', {str}))),
        }

    def _item_url(self, item, catalog=None, show=None):
        seo = traverse_obj(item, ('seo_web_url', {str}))
        if seo:
            return urljoin(self._BASE_URL, seo)
        item_id = traverse_obj(item, ('friendly_id', {str}))
        show = show or traverse_obj(item, ('show_object', 'friendly_id', {str}))
        catalog = catalog or traverse_obj(item, ('catalog_object', 'friendly_id', {str}))
        if catalog and show and item_id:
            return f'{self._BASE_URL}/{catalog}/{show}/{item_id}'
        if catalog and item_id:
            return f'{self._BASE_URL}/{catalog}/{item_id}'
        return urljoin(self._BASE_URL, item_id)


class TarangPlusVideoIE(TarangPlusBaseIE):
    IE_NAME = 'tarangplus:video'
    _VALID_URL = r'https?://(?:www\.)?tarangplus\.in/(?:(?P<catalog>movies)|(?P<type>[^#?/]+)/(?P<show>[^#?/]+))/(?!episodes)(?P<id>[^#?/]+)'
    _TESTS = [{
        'url': 'https://tarangplus.in/movies/swayambara',
        'md5': 'bb0a52996321b2eba22e910c58880a8e',
        'info_dict': {
            'id': '67e7e1fd19521d054c006b42',
            'display_id': 'swayambara',
            'ext': 'mp4',
            'title': 'Swayambara',
            'description': 'md5:48b08d17887dacc6ffbc071ff417d2ce',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 9420,
            'timestamp': 1753263078,
            'upload_date': '20250723',
            'media_type': 'movie',
            'categories': ['Familydrama'],
        },
    }, {
        'url': 'https://tarangplus.in/tarangaplus-originals/khitpit/khitpit-ep-10',
        'skip': 'This video is no longer available',
        'info_dict': {
            'id': '67b8206719521d054c0059b7',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://tarangplus.in/tarang-serials/bada-bohu/bada-bohu-ep-233',
        'skip': 'Login required to resolve playback URL',
        'info_dict': {
            'id': '680b9d6c19521d054c007782',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://tarangplus.in/tarangaplus-originals/ichha/ichha-teaser-1',
        'skip': 'This video is no longer available',
        'info_dict': {
            'id': '5f0f252d3326af0720000342',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://tarangplus.in/short/ai-maa/ai-maa',
        'only_matching': True,
    }, {
        'url': 'https://tarangplus.in/shows/tarang-cine-utsav-2024/tarang-cine-utsav-2024-seg-1',
        'only_matching': True,
    }, {
        'url': 'https://tarangplus.in/music-videos/chori-chori-bohu-chori-songs/nijara-laguchu-dhire-dhire',
        'only_matching': True,
    }, {
        'url': 'https://tarangplus.in/kids-shows/chhota-jaga/chhota-jaga-ep-33-jamidar-ra-khajana-adaya',
        'only_matching': True,
    }]

    def _fetch_metadata(self, display_id, catalog, url_type, show):
        if show:
            data = self._call_api(
                f'catalogs/shows/{show}/episodes/{display_id}.gzip',
                display_id, query={'item_language': ''}, fatal=False)
            if traverse_obj(data, 'data'):
                return data['data']
            if url_type:
                data = self._call_api(
                    f'catalogs/{url_type}/items/{show}/episodes/{display_id}.gzip',
                    display_id, query={'item_language': ''}, fatal=False)
                if traverse_obj(data, 'data'):
                    return data['data']
        catalog = catalog or url_type or 'movies'
        return self._call_api(
            f'catalogs/{catalog}/items/{display_id}.gzip',
            display_id, query={'item_language': ''})['data']

    def _extract_public_m3u8_url(self, metadata, display_id):
        m3u8_url = traverse_obj(metadata, (
            (('preview', 'preview_url'), 'preview_url'), {url_or_none}, any))
        if m3u8_url and self._is_valid_url(m3u8_url, display_id, 'm3u8'):
            return m3u8_url
        return None

    def _real_extract(self, url):
        catalog, url_type, show, display_id = self._match_valid_url(url).group(
            'catalog', 'type', 'show', 'id')
        metadata = self._fetch_metadata(display_id, catalog, url_type, show)

        m3u8_url = self._extract_public_m3u8_url(metadata, display_id)
        if not m3u8_url:
            self.raise_login_required(
                'Login required to resolve the full playback URL; public preview HLS is not available',
                method=None)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(m3u8_url, display_id, 'mp4')
        return {
            'id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            **self._extract_item_info(metadata, display_id),
        }


class TarangPlusEpisodesIE(TarangPlusBaseIE):
    IE_NAME = 'tarangplus:episodes'
    _VALID_URL = r'https?://(?:www\.)?tarangplus\.in/(?P<type>[^#?/]+)/(?P<id>[^#?/]+)/episodes/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://tarangplus.in/tarangaplus-originals/balijatra/episodes',
        'info_dict': {
            'id': 'balijatra',
            'title': 'Balijatra',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://tarangplus.in/tarang-serials/bada-bohu/episodes',
        'info_dict': {
            'id': 'bada-bohu',
            'title': 'Bada Bohu',
        },
        'playlist_mincount': 236,
    }, {
        'url': 'https://tarangplus.in/shows/dr-nonsense/episodes',
        'info_dict': {
            'id': 'dr-nonsense',
            'title': 'Dr. Nonsense',
        },
        'playlist_mincount': 15,
    }]

    def _real_extract(self, url):
        url_type, display_id = self._match_valid_url(url).group('type', 'id')
        data = self._call_api(
            f'catalogs/{url_type}/items/{display_id}/episodes.gzip',
            display_id, query={
                'order_by': 'desc',
                'item_language': '',
                'status': 'published',
            })['data']
        entries = [
            self.url_result(
                self._item_url(ep, catalog=url_type, show=display_id),
                TarangPlusVideoIE, **self._extract_item_info(ep, ep['friendly_id']))
            for ep in traverse_obj(data, ('items', lambda _, v: v['friendly_id']))
        ]
        return self.playlist_result(
            entries, display_id,
            traverse_obj(data, (('display_title', 'title'), {str}, filter, any)))


class TarangPlusPlaylistIE(TarangPlusBaseIE):
    IE_NAME = 'tarangplus:playlist'
    _VALID_URL = r'https?://(?:www\.)?tarangplus\.in/(?P<id>[^#?/]+)/all/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://tarangplus.in/chhota-jaga/all',
        'info_dict': {
            'id': 'chhota-jaga',
            'title': 'Chhota Jaga',
        },
        'playlist_mincount': 33,
    }, {
        'url': 'https://tarangplus.in/kids-yali-show/all',
        'info_dict': {
            'id': 'kids-yali-show',
            'title': 'Yali',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://tarangplus.in/trailer/all',
        'info_dict': {
            'id': 'trailer',
            'title': 'Trailer',
        },
        'playlist_mincount': 50,
    }, {
        'url': 'https://tarangplus.in/latest-songs/all',
        'info_dict': {
            'id': 'latest-songs',
            'title': 'Latest Songs',
        },
        'playlist_mincount': 46,
    }, {
        'url': 'https://tarangplus.in/premium-serials-episodes/all',
        'info_dict': {
            'id': 'premium-serials-episodes',
            'title': 'Primetime Latest Episodes',
        },
        'playlist_mincount': 100,
    }]
    _PAGE_SIZE = 100

    def _entries(self, playlist_id, page):
        data = self._call_api(
            f'catalog_lists/{playlist_id}.gzip', playlist_id,
            note=f'Downloading playlist JSON page {page + 1}', query={
                'page': 0,
                'page_size': self._PAGE_SIZE,
                'start_count': page * self._PAGE_SIZE,
                'pagination': 'true',
                'item_language': '',
            })
        for item in traverse_obj(data, ('data', 'catalog_list_items', lambda _, v: v['friendly_id'])):
            yield self.url_result(
                self._item_url(item), TarangPlusVideoIE,
                **self._extract_item_info(item, item['friendly_id']))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        data = self._call_api(
            f'catalog_lists/{display_id}.gzip', display_id, query={
                'page': 0,
                'page_size': 1,
                'start_count': 0,
                'pagination': 'true',
                'item_language': '',
            })['data']
        entries = OnDemandPagedList(
            functools.partial(self._entries, display_id), self._PAGE_SIZE)
        return self.playlist_result(
            entries, display_id,
            traverse_obj(data, (('display_title', 'title'), {str}, filter, any)))
