import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class FreeTvBaseIE(InfoExtractor):
    _API_BASE = 'https://api-ott.freetv.com'

    def _parse_site_settings(self, webpage, display_id):
        return self._search_json(
            r'<script[^>]+data-drupal-selector="drupal-settings-json"[^>]*>', webpage, 'drupal settings', display_id,
        )

    def _api_headers(self, url, cs_auth):
        return {
            'ottera-cs-auth': cs_auth,
            'ottera-referrer': url,
            'Origin': 'https://www.freetv.com',
        }

    def _api_query(self, query, language='es'):
        return {
            'version': '14.0',
            'platform': 'web',
            'partner': 'internal',
            'device_type': 'desktop',
            'language': language,
            'timestamp': str(int(time.time())),
            **query,
        }

    def _call_api(self, action, video_id, query, url, cs_auth, language='es', note=None):
        return self._download_json(
            f'{self._API_BASE}/{action}',
            video_id,
            note=note or f'Downloading {action} JSON',
            query=self._api_query(query, language),
            headers=self._api_headers(url, cs_auth),
        )

    def _extract_nid_and_auth(self, webpage, settings):
        video_id = traverse_obj(settings, ('codesbasePublic', 'nid', {str}))
        if not video_id:
            video_id = self._search_regex(r'"currentPath"\s*:\s*"node/(\d+)"', webpage, 'video id')
        cs_auth = traverse_obj(settings, ('codesbasePublic', 'options', 'cs_auth_token', {str}))
        if not cs_auth:
            cs_auth = self._search_regex(r'"cs_auth_token"\s*:\s*"([^"]+)"', webpage, 'auth token')
        language = traverse_obj(settings, ('path', 'currentLanguage', {str})) or 'es'
        return video_id, cs_auth, language


class FreeTvMoviesIE(FreeTvBaseIE):
    _VALID_URL = r'''(?x)
        https?://(?:www\.|video\.)?freetv\.com/
        (?:[a-z]{2}(?:-[a-z]+)?/)?
        (?:
            (?:linear|feature|peliculas)/(?P<id>[^/?#]+)
            |shows/[^/?#]+/season/\d+/episode/(?P<episode>\d+)
        )
    '''
    _TESTS = [
        {
            'url': 'https://www.freetv.com/es/linear/freetv-familia-0',
            'info_dict': {
                'id': '19355',
                'ext': 'mp4',
                'title': r're:FreeTV Familia',
                'description': 'md5:76ea2b8f4a693caff751f8f01738dd55',
                'thumbnail': r're:https?://.+\.(?:jpg|png)',
                'timestamp': 1751500800,
                'upload_date': '20250703',
                'live_status': 'is_live',
            },
        },
        {
            'url': 'https://www.freetv.com/es/feature/bodo-0',
            'only_matching': True,
        },
        {
            'url': 'https://www.freetv.com/es/shows/cuidados-prenatales-la-importancia-de-nacer/season/2/episode/37',
            'only_matching': True,
        },
        {
            'url': 'https://www.freetv.com/peliculas/atrapame-si-puedes/',
            'skip': 'Old WordPress URLs are gone',
            'md5': 'dc62d5abf0514726640077cd1591aa92',
            'info_dict': {
                'id': '428021',
                'title': 'Atrápame Si Puedes',
                'description': 'md5:ca63bc00898aeb2f64ec87c6d3a5b982',
                'ext': 'mp4',
            },
        },
        {
            'url': 'https://www.freetv.com/peliculas/monstruoso/',
            'skip': 'Old WordPress URLs are gone',
            'md5': '509c15c68de41cb708d1f92d071f20aa',
            'info_dict': {
                'id': '377652',
                'title': 'Monstruoso',
                'description': 'md5:333fc19ee327b457b980e54a911ea4a3',
                'ext': 'mp4',
            },
        },
    ]

    def _real_extract(self, url):
        url_m = self._match_valid_url(url)
        display_id = url_m.group('id') or url_m.group('episode')
        webpage = self._download_webpage(url, display_id)
        settings = self._parse_site_settings(webpage, display_id)
        video_id, cs_auth, language = self._extract_nid_and_auth(webpage, settings)

        item = traverse_obj(
            self._call_api('search', video_id, {'id': video_id}, url, cs_auth, language), ('objects', 0, {dict}),
        )
        if not item:
            raise ExtractorError('Unable to extract video metadata', expected=True)

        video_id = str(item.get('id') or video_id)
        is_live = item.get('video_type') == 'linear'

        if item.get('drm') == 'true':
            self.report_drm(video_id)

        player_js = self._download_webpage(
            f'{self._API_BASE}/embeddedVideoPlayer',
            video_id,
            query=self._api_query(
                {
                    'id': video_id,
                    'div_id': 'video_player',
                    'device_type': 'desktop',
                    'content_page_url': url,
                },
                language,
            ),
            headers=self._api_headers(url, cs_auth),
            note='Downloading player script',
        )

        if 'loadLoginForm' in player_js and 'playerSources.hls' not in player_js:
            self.raise_login_required()

        hls_url = self._search_regex(
            r'playerSources\.hls\s*=\s*\[\s*\{\s*url:\s*(["\'])(?P<url>(?:(?!\1).)+)\1',
            player_js,
            'hls url',
            group='url',
        )

        if 'drmData:' in player_js:
            self.report_drm(video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls', live=is_live,
        )

        for caption in traverse_obj(item, ('captions', ..., {dict})):
            caption_url = url_or_none(caption.get('caption_url'))
            if caption_url:
                subtitles.setdefault(caption.get('language') or 'und', []).append(
                    {
                        'url': caption_url,
                        'ext': 'vtt',
                    },
                )

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            **traverse_obj(
                item,
                {
                    'title': ('name', {str}),
                    'description': (('long_description', 'short_description'), {str}, any),
                    'thumbnail': (('widescreen_thumbnail_url', 'thumbnail_url'), {url_or_none}, any),
                    'timestamp': ('published_on', {int_or_none}),
                    'series': ('show_info', 'show_name', {str}),
                    'series_id': ('show_info', 'show_id', {str}),
                    'season_number': ('show_info', 'season_num', {int_or_none}),
                    'episode_number': ('show_info', 'episode_num', {int_or_none}),
                    'season_id': ('show_info', 'season_id', {str}),
                },
            ),
        }


class FreeTvIE(FreeTvBaseIE):
    IE_NAME = 'freetv:series'
    _VALID_URL = (
        r'https?://(?:www\.|video\.)?freetv\.com/(?:[a-z]{2}(?:-[a-z]+)?/)?(?:shows|series)/(?P<id>[^/?#]+)/?(?:$|[?#])'
    )
    _TESTS = [
        {
            'url': 'https://www.freetv.com/es/shows/cuidados-prenatales-la-importancia-de-nacer',
            'only_matching': True,
        },
        {
            'url': 'https://www.freetv.com/series/el-detective-l/',
            'skip': 'Old WordPress URLs are gone',
            'info_dict': {
                'id': 'el-detective-l',
                'title': 'El Detective L',
                'description': 'md5:f9f1143bc33e9856ecbfcbfb97a759be',
            },
            'playlist_count': 24,
        },
        {
            'url': 'https://www.freetv.com/series/esmeraldas/',
            'skip': 'Old WordPress URLs are gone',
            'info_dict': {
                'id': 'esmeraldas',
                'title': 'Esmeraldas',
                'description': 'md5:43d7ec45bd931d8268a4f5afaf4c77bf',
            },
            'playlist_count': 62,
        },
        {
            'url': 'https://www.freetv.com/series/las-aventuras-de-leonardo/',
            'skip': 'Old WordPress URLs are gone',
            'info_dict': {
                'id': 'las-aventuras-de-leonardo',
                'title': 'Las Aventuras de Leonardo',
                'description': 'md5:0c47130846c141120a382aca059288f6',
            },
            'playlist_count': 13,
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        settings = self._parse_site_settings(webpage, display_id)
        show_id, cs_auth, language = self._extract_nid_and_auth(webpage, settings)

        show = (
            traverse_obj(
                self._call_api('search', show_id, {'id': show_id}, url, cs_auth, language), ('objects', 0, {dict}),
            )
            or {}
        )

        episodes = self._call_api(
            'getreferencedobjects',
            show_id,
            {
                'parent_id': show_id,
                'parent_type': 'show',
                'max': '1000',
            },
            url,
            cs_auth,
            language,
            note='Downloading episodes JSON',
        )

        entries = (
            self.url_result(urljoin(url, episode['url']), FreeTvMoviesIE, episode.get('id'), episode.get('name'))
            for episode in traverse_obj(episodes, ('objects', lambda _, v: v['url']))
        )

        return self.playlist_result(
            entries,
            show_id,
            show.get('name'),
            traverse_obj(show, (('long_description', 'short_description'), {str}, any)),
        )
