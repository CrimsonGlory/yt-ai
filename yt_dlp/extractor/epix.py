import json
import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    traverse_obj,
    url_or_none,
)


class EpixIE(InfoExtractor):
    IE_NAME = 'epix'
    IE_DESC = 'EPIX / MGM+'
    _VALID_URL = (
        r'https?://(?:www\.)?(?:epix|mgmplus)\.com/'
        r'(?P<kind>series|movies?)/(?P<slug>[^/?#]+)'
        r'(?:/season/\d+/episode/\d+/[^/?#]+)?'
        r'(?:/extra/(?P<id>\d+)|[?#](?:[^#]*[?&])?(?:extra=(?P<extra_id>\d+)|trailer=))'
    )
    _API_BASE = 'https://api.mgmplus.com'
    _API_KEY = '53e208a9bbaee479903f43b39d7301f7'
    _SESSION_TOKEN = None
    _TRAILER_QUERY = {
        'series': ('query SeriesTrailer($id: ID!) { series(id: $id) { trailer { underlyingId title } } }'),
        'movie': ('query MovieTrailer($id: ID!) { movie(id: $id) { trailer { underlyingId title } } }'),
    }
    _TESTS = [
        {
            'url': 'https://www.epix.com/series/from/extra/13596',
            'md5': 'e3be4c92d7c80368ea94ae807ffc5192',
            'info_dict': {
                'id': '13596',
                'ext': 'mp4',
                'title': 'From S1 Overview',
                'description': "Check out what's in store for From Season 1!",
                'duration': 120.171,
            },
            'params': {'format': 'http'},
        },
        {
            'url': 'https://www.mgmplus.com/series/from?extra=13596',
            'only_matching': True,
        },
        {
            'url': 'https://www.epix.com/series/from/season/1/episode/3/from-s1-e3?trailer=true',
            'only_matching': True,
        },
        {
            'url': 'https://www.mgmplus.com/series/from?trailer=true',
            'only_matching': True,
        },
        {
            'url': 'https://www.mgmplus.com/movie/chaplin-1992?trailer=true',
            'only_matching': True,
        },
    ]

    def _api_headers(self, video_id):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Session-Token': self._get_session_token(video_id),
        }

    def _get_session_token(self, video_id):
        if self._SESSION_TOKEN:
            return self._SESSION_TOKEN
        session = self._download_json(
            f'{self._API_BASE}/v2/sessions',
            video_id,
            'Downloading anonymous session',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            data=json.dumps(
                {
                    'apikey': self._API_KEY,
                    'device': {
                        'guid': str(uuid.uuid4()),
                        'format': 'console',
                        'os': 'web',
                        'display_width': 1920,
                        'display_height': 1080,
                        'app_version': '1.0.2',
                        'model': 'browser',
                        'manufacturer': 'google',
                        'device_interface_type': 'desktop',
                    },
                },
            ).encode(),
        )
        token = traverse_obj(session, ('device_session', 'session_token', {str}))
        if not token:
            raise ExtractorError('Unable to start an MGM+ session')
        EpixIE._SESSION_TOKEN = token
        return token

    def _call_api(self, path, video_id, note=None):
        return self._download_json(
            f'{self._API_BASE}/v2/{path}', video_id, note or 'Downloading API JSON', headers=self._api_headers(video_id),
        )

    def _trailer_video_id(self, kind, slug, display_id):
        field = 'movie' if kind.startswith('movie') else 'series'
        data = self._download_json(
            f'{self._API_BASE}/graphql',
            display_id,
            f'Downloading {field} trailer',
            headers=self._api_headers(display_id),
            data=json.dumps(
                {
                    'query': self._TRAILER_QUERY[field],
                    'variables': {'id': slug},
                },
            ).encode(),
        )
        trailer_id = traverse_obj(data, ('data', field, 'trailer', 'underlyingId', {int_or_none}))
        if not trailer_id:
            raise ExtractorError(f'This {field} has no public trailer', expected=True)
        return str(trailer_id)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        kind, slug = mobj.group('kind', 'slug')
        video_id = mobj.group('id') or mobj.group('extra_id') or self._trailer_video_id(kind, slug, slug)

        video = self._call_api(f'videos/{video_id}', video_id, 'Downloading video JSON')
        video = traverse_obj(video, ('video', {dict})) or video
        video_id = str(traverse_obj(video, ('id', {int_or_none})) or video_id)

        formats, subtitles = [], {}
        hls_url = url_or_none(video.get('hlspath'))
        if hls_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
            )
        http_url = url_or_none(self._proto_relative_url(video.get('url')))
        if http_url:
            formats.append(
                {
                    'url': http_url,
                    'format_id': 'http',
                },
            )
        if not formats:
            raise ExtractorError('No public trailer/extra formats', expected=True)

        return {
            'id': video_id,
            'title': traverse_obj(video, ('title', {str})),
            'description': traverse_obj(video, ('description', {str})) or None,
            'duration': traverse_obj(video, ('duration', {float_or_none})),
            'formats': formats,
            'subtitles': subtitles,
        }
