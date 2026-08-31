import json
import time
import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    qualities,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class NutsonBaseIE(InfoExtractor):
    _API_V2 = 'https://api.nutson.us/api/v2'
    _API_V3 = 'https://api.nutson.us/api/v3'
    _MEDIA_HEADERS = {
        'Origin': 'https://nutson.us',
        'Referer': 'https://nutson.us/',
    }
    _APP = {
        'app_name': 'NUTSon',
        'app_version': '3.6.6',
        'app_build': 3,
        'app_type': 'challenges',
    }

    def _real_initialize(self):
        self._device_id = uuid.uuid4().hex
        self._access_token = None

    def _api_headers(self, auth=True):
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'X-Nuts-Device-Id': self._device_id,
            'X-Nuts-Request-Id': str(uuid.uuid4()),
            **self._MEDIA_HEADERS,
        }
        if auth and self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        return headers

    def _ensure_session(self, video_id):
        if self._access_token:
            return
        session = self._download_json(
            f'{self._API_V3}/auth/session', video_id, 'Downloading guest session',
            data=json.dumps({
                'installation_token': self._device_id,
                'device': {
                    'platform': 'WEB',
                    'platform_version': 'Firefox',
                },
                'application': self._APP,
            }).encode(),
            headers={
                **self._api_headers(auth=False),
                'Content-Type': 'application/json',
            })
        self._access_token = traverse_obj(session, ('data', 'access_token', {str}))
        if not self._access_token:
            raise ExtractorError('Unable to obtain NUTSon guest session', expected=True)

    def _call_api(self, path, video_id, note='Downloading JSON metadata', query=None, fatal=True):
        self._ensure_session(video_id)
        query = {
            'device_time': str(int(time.time())),
            **(query or {}),
        }
        return self._download_json(
            f'{self._API_V2}/{path}', video_id, note,
            fatal=fatal, headers=self._api_headers(), query=query)


class NutsonIE(NutsonBaseIE):
    IE_NAME = 'nutson'
    IE_DESC = 'NUTSon'
    _VALID_URL = r'https?://(?:www\.)?nutson\.us/media/(?P<id>[0-9a-fA-F]+:[0-9a-fA-F]+)'
    _TESTS = [{
        'url': 'https://nutson.us/media/6446953bf9718fb00cc29ffe:630fc1a519f4b86b8ba76d44',
        'md5': '442fd0a52ff36004168bd4273716394e',
        'info_dict': {
            'id': '6446953bf9718fb00cc29ffe:630fc1a519f4b86b8ba76d44',
            'ext': 'mp4',
            'title': '6446953bf9718fb00cc29ffe:630fc1a519f4b86b8ba76d44',
            'description': '',
            'thumbnail': r're:https://cdn\.nutson\.us/.+',
            'duration': 27.49,
            'timestamp': 1682347323,
            'upload_date': '20230424',
            'uploader': 'Lerchi',
            'uploader_id': '630fc1a519f4b86b8ba76d44',
            'uploader_url': 'https://nutson.us/users/630fc1a519f4b86b8ba76d44',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://www.nutson.us/media/6446953bf9718fb00cc29ffe:630fc1a519f4b86b8ba76d44',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media = traverse_obj(
            self._call_api(f'media/{video_id}', video_id), ('data', {dict}))
        if not media:
            raise ExtractorError('Unable to extract media data', expected=True)
        if traverse_obj(media, 'is_deleted') or traverse_obj(media, 'deleted_at'):
            raise ExtractorError('This video has been deleted', expected=True)

        quality = qualities(('h264_low', 'h264_medium', 'h264_high'))
        formats, seen_urls = [], set()
        media_urls = dict(traverse_obj(media, ('media_urls', {dict})) or {})
        fallback_url = traverse_obj(media, ('media_url', {url_or_none}))
        if fallback_url and fallback_url not in media_urls.values():
            media_urls.setdefault('http', fallback_url)
        for format_id, format_url in media_urls.items():
            format_url = url_or_none(format_url)
            if not format_url or format_url in seen_urls:
                continue
            seen_urls.add(format_url)
            formats.append({
                'url': format_url,
                'format_id': format_id,
                'ext': 'mp4',
                'vcodec': 'h264' if 'h264' in str(format_id) else None,
                'quality': quality(format_id),
            })
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        uploader_id = traverse_obj(media, ('author', 'user_id', {str_or_none}))
        title = (
            traverse_obj(media, ('media_name', {str}))
            or traverse_obj(media, ('media_description', {str}))
            or video_id)
        return {
            'id': traverse_obj(media, ('media_id', {str})) or video_id,
            'title': title,
            'formats': formats,
            **traverse_obj(media, {
                'description': ('media_description', {str}),
                'thumbnail': (('thumbnail_url', 'preview_url'), {url_or_none}, any),
                'duration': ('media_duration', {float_or_none}),
                'timestamp': ('created_at', {int_or_none}),
                'view_count': ('counters', 'views', {int_or_none}),
                'like_count': ('counters', 'likes', {int_or_none}),
                'comment_count': ('counters', 'comments', {int_or_none}),
                'uploader': ('author', ('person_name', 'user_name'), {str}, any),
                'uploader_id': ('author', 'user_id', {str_or_none}),
            }),
            'uploader_url': f'https://nutson.us/users/{uploader_id}' if uploader_id else None,
        }


class NutsonUserIE(NutsonBaseIE):
    IE_NAME = 'nutson:user'
    IE_DESC = 'NUTSon user'
    _VALID_URL = r'https?://(?:www\.)?nutson\.us/users/(?P<id>[0-9a-fA-F]+)(?:/all)?/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://nutson.us/users/6201867a749f9779a56fde2a',
        'info_dict': {
            'id': '6201867a749f9779a56fde2a',
            'title': 'trusting_euclid',
            'description': str,
        },
        'playlist_mincount': 10,
        'params': {
            'extract_flat': True,
            'skip_download': True,
        },
    }, {
        'url': 'https://nutson.us/users/6201867a749f9779a56fde2a/all',
        'only_matching': True,
    }]

    def _entries(self, user_id):
        page_token, seen, page = None, set(), 1
        while True:
            query = {}
            if page_token:
                query['page_token'] = page_token
            data = traverse_obj(self._call_api(
                f'media/users/{user_id}/all', user_id,
                f'Downloading user media page {page}', query=query), ('data', {dict})) or {}
            new_count = 0
            for media in traverse_obj(data, ('media', ..., {dict})):
                media_id = traverse_obj(media, ('media_id', {str}))
                if not media_id or media_id in seen:
                    continue
                seen.add(media_id)
                new_count += 1
                yield self.url_result(
                    f'https://nutson.us/media/{media_id}', NutsonIE, media_id)
            page_token = traverse_obj(data, ('next_page_token', {str}))
            if not page_token or not new_count:
                break
            page += 1

    def _real_extract(self, url):
        user_id = self._match_id(url)
        profile = traverse_obj(self._call_api(
            f'users/{user_id}', user_id, 'Downloading user profile',
            fatal=False), ('data', {dict})) or {}
        return self.playlist_result(
            self._entries(user_id), user_id,
            traverse_obj(profile, (('user_name', 'person_name'), {str}, any)) or user_id,
            traverse_obj(profile, ('user_bio', {str})))
