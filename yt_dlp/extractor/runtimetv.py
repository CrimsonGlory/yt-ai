import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class RuntimeTVIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?runtime\.tv/
        (?:[a-z]{2}(?:-[a-z]+)?/)?
        (?:
            shows/(?P<show_slug>[^/?#]+)(?:/season/\d+/episode/(?P<episode>\d+))?
            |(?:linear|feature)/(?P<video_slug>[^/?#]+)
            |node/(?P<node_id>\d+)
        )
        /?(?:[?#]|$)
    '''
    _API_BASE = 'https://api-ott.runtime.tv'
    _TESTS = [{
        'url': 'https://www.runtime.tv/es/shows/jack-hunter/season/1/episode/3',
        'md5': 'f404875de75da3a31fa1b0a6e52017d7',
        'info_dict': {
            'id': '557',
            'ext': 'mp4',
            'title': 'Jack Hunter y la estrella del cielo',
            'description': 'Jack Hunter viaja a Constantinopla para evitar que una poderosa arma caiga en manos criminales.',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'timestamp': 1780300277,
            'upload_date': '20260601',
            'duration': 5906,
            'series': 'Jack Hunter',
            'series_id': '801',
            'season_number': 1,
            'season': 'Season 1',
            'episode_number': 3,
            'episode': 'Episode 3',
            'season_id': '212',
        },
    }, {
        'url': 'https://www.runtime.tv/es/shows/jack-hunter',
        'info_dict': {
            'id': '801',
            'title': 'Jack Hunter',
            'description': 'Un arqueologo trotamundos descubre el peligro y la intriga mientras busca un tesoro esquivo.',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'https://www.runtime.tv/es/feature/tornados-de-hielo-0',
        'only_matching': True,
    }, {
        'url': 'https://www.runtime.tv/es/linear/runtime-crimen-0',
        'only_matching': True,
    }, {
        'url': 'https://www.runtime.tv/es/node/5012',
        'only_matching': True,
    }]

    def _parse_site_settings(self, webpage, display_id):
        return self._search_json(
            r'<script[^>]+data-drupal-selector="drupal-settings-json"[^>]*>', webpage, 'drupal settings', display_id,
        )

    def _api_headers(self, url, cs_auth):
        return {
            'ottera-cs-auth': cs_auth,
            'ottera-referrer': url,
            'Origin': 'https://www.runtime.tv',
        }

    def _api_query(self, query, language='es', version='13'):
        return {
            'version': version,
            'platform': 'web',
            'device_type': 'desktop',
            'language': language,
            'timestamp': str(int(time.time())),
            **query,
        }

    def _call_api(self, action, video_id, query, url, cs_auth, language='es', version='13', note=None):
        return self._download_json(
            f'{self._API_BASE}/{action}',
            video_id,
            note=note or f'Downloading {action} JSON',
            query=self._api_query(query, language, version),
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
        version = traverse_obj(settings, ('codesbasePublic', 'options', 'version', {str})) or '13'
        api = traverse_obj(settings, ('codesbasePublic', 'options', 'api', {url_or_none}))
        if api:
            self._API_BASE = api.rstrip('/')
        return video_id, cs_auth, language, version

    def _extract_video(self, url, video_id, cs_auth, language, version):
        item = traverse_obj(
            self._call_api('search', video_id, {'id': video_id}, url, cs_auth, language, version),
            ('objects', 0, {dict}),
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
                version,
            ),
            headers=self._api_headers(url, cs_auth),
            note='Downloading player script',
        )

        if 'loadLoginForm' in player_js and 'playerSources.hls' not in player_js:
            self.raise_login_required()

        hls_url = self._search_regex(
            r'playerSources\.hls\s*=\s*\[\s*\{\s*url:\s*(["\'])(?P<url>(?:(?!\1).)+)\1',
            player_js, 'hls url', group='url',
        )

        if 'drmData:' in player_js:
            self.report_drm(video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls', live=is_live,
        )

        for caption in traverse_obj(item, ('captions', ..., {dict})):
            caption_url = url_or_none(caption.get('caption_url'))
            if caption_url:
                subtitles.setdefault(caption.get('language') or 'und', []).append({
                    'url': caption_url,
                    'ext': 'vtt',
                })

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            **traverse_obj(item, {
                'title': ('name', {str}),
                'description': (('long_description', 'short_description'), {str}, any),
                'thumbnail': (('widescreen_thumbnail_url', 'thumbnail_url'), {url_or_none}, any),
                'timestamp': ('published_on', {int_or_none}),
                'duration': ('duration', {int_or_none}),
                'series': ('show_info', 'show_name', {str}),
                'series_id': ('show_info', 'show_id', {str}),
                'season_number': ('show_info', 'season_num', {int_or_none}),
                'episode_number': ('show_info', 'episode_num', {int_or_none}),
                'season_id': ('show_info', 'season_id', {str}),
            }),
        }

    def _extract_show(self, url, show_id, cs_auth, language, version):
        show = traverse_obj(
            self._call_api('search', show_id, {'id': show_id}, url, cs_auth, language, version),
            ('objects', 0, {dict}),
        ) or {}

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
            version,
            note='Downloading episodes JSON',
        )

        entries = (
            self.url_result(urljoin(url, episode['url']), RuntimeTVIE, episode.get('id'), episode.get('name'))
            for episode in traverse_obj(episodes, ('objects', lambda _, v: v['url']))
        )

        return self.playlist_result(
            entries, show_id, show.get('name'),
            traverse_obj(show, (('long_description', 'short_description'), {str}, any)),
        )

    def _real_extract(self, url):
        url_m = self._match_valid_url(url)
        display_id = (
            url_m.group('episode') or url_m.group('video_slug')
            or url_m.group('show_slug') or url_m.group('node_id'))
        webpage = self._download_webpage(url, display_id)
        settings = self._parse_site_settings(webpage, display_id)
        object_id, cs_auth, language, version = self._extract_nid_and_auth(webpage, settings)

        if url_m.group('show_slug') and not url_m.group('episode'):
            return self._extract_show(url, object_id, cs_auth, language, version)
        return self._extract_video(url, object_id, cs_auth, language, version)
