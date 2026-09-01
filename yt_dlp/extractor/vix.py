from .anvato import AnvatoIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    jwt_decode_hs256,
    parse_age_limit,
    parse_iso8601,
    smuggle_url,
    try_call,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class VixIE(InfoExtractor):
    IE_NAME = 'vix'
    IE_DESC = 'ViX'
    _VALID_URL = r'https?://(?:www\.)?vix\.com/(?:[a-z]{2}-[a-z]{2}/)?(?:video|detail)/video-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.vix.com/es-es/video/video-4158939',
        'md5': '0a8540e3492d48fe2a3e2138170d0854',
        'info_dict': {
            'id': '4158939',
            'ext': 'mp4',
            'title': 'La Escuelita VIP - Regreso a clase',
            'description': 'Jorgito regresa a clases con muchas ganas de estudiar porque no quiere ser un vago. El director Virolo felicita a Jorge por permanecer 5 años en tercero de primaria y le dice que Canuta será de nuevo su maestra.',
            'thumbnail': r're:https://images\.vix\.com/.+',
            'timestamp': 1646802000,
            'upload_date': '20220309',
            'release_timestamp': 1646802000,
            'release_date': '20220309',
            'uploader': 'UNIVISON',
            'duration': 1454,
            'series': 'La Escuelita VIP',
            'season': 'Temporada 1',
            'episode': 'Regreso a clase',
            'episode_number': 1,
            'language': 'es',
            'age_limit': 14,
            'tags': [
                'La Escuelita VIP',
                'serie',
                'Jorge Ortiz de Pinedo',
                'comedy',
                'David Villalpando',
                'Luis de Alba',
                'Polo Polo',
                'Roxana Martínez',
                'Martha Ofelia Galindo',
                'Jorge Muñiz',
                'capitulo completo',
            ],
            'categories': ['Comedy', 'Sitcom'],
        },
        'add_ie': [AnvatoIE.ie_key()],
    }, {
        'url': 'https://vix.com/es-es/video/video-4158939',
        'only_matching': True,
    }, {
        'url': 'https://vix.com/video/video-4158939',
        'only_matching': True,
    }, {
        'url': 'https://www.vix.com/detail/video-4158939',
        'only_matching': True,
    }, {
        'url': 'https://vix.com/es-es/detail/video-2746714',
        'only_matching': True,
    }]

    def _extract_player_data(self, webpage, video_id):
        return traverse_obj(self._search_nextjs_v13_data(webpage, video_id, fatal=False), (
            lambda _, v: isinstance(v, dict) and str(v.get('videoId') or '') == video_id and v.get('videoToken'),
            any,
        ))

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if '/video/video-' not in url:
            url = f'https://vix.com/video/video-{video_id}'
        webpage = self._download_webpage(url, video_id)
        page = self._extract_player_data(webpage, video_id)
        token = traverse_obj(page, ('videoToken', {str})) or self._search_regex(
            r'\\"videoToken\\":\\"(eyJ[^"\\]+)', webpage, 'video token', default=None)
        video_data = traverse_obj(page, ('videoData', {dict})) or {}

        availability = traverse_obj(video_data, ('vodAvailability', {dict})) or {}
        if availability.get('isBlocked'):
            reason = availability.get('reason') or ''
            if 'REGISTRATION' in reason:
                self.raise_login_required('This video requires a free ViX account', method='any')
            if reason in ('REQUIRES_SUBSCRIPTION', 'REQUIRES_PREMIUM'):
                self.raise_login_required(
                    'This video is only available for ViX Premium subscribers', method='any')
            raise ExtractorError(
                f'This video is not available{f" ({reason})" if reason else ""}', expected=True)

        if not token:
            raise ExtractorError('Unable to extract ViX video token', expected=True)

        payload = try_call(jwt_decode_hs256, args=(token,)) or {}
        access_key = traverse_obj(payload, ('iss', {str}))
        anvato_id = traverse_obj(payload, ('vid', {str})) or video_id
        if not access_key:
            raise ExtractorError('Unable to extract Anvato access key', expected=True)

        return self.url_result(
            smuggle_url(f'anvato:{access_key}:{anvato_id}', {'token': token}),
            AnvatoIE, video_id=anvato_id, url_transparent=True,
            **traverse_obj(video_data, {
                'description': ('description', {str}),
                'episode': ('title', {str}),
                'episode_number': ('videoTypeData', 'episodeNumber', {int_or_none}),
                'series': ('videoTypeData', 'series', 'title', {str}),
                'season': ('videoTypeData', 'season', 'title', {str}),
                'language': ('language', {str}),
                'tags': ('keywords', ..., {str}, filter, all),
                'age_limit': ('ratings', 0, 'ratingValue', {parse_age_limit}),
                'release_timestamp': ('dateReleased', {parse_iso8601}),
                'duration': ('videoTypeData', 'playbackData', 'streamMetadata', 'duration', {int_or_none}),
                'thumbnail': ('imageAssets', ..., 'link', {url_or_none}, any),
            }))
