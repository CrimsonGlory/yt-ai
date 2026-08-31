from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    qualities,
    str_or_none,
    traverse_obj,
    url_or_none,
)

_VERSION_QUALITY = qualities((
    'Sting', '30 Seconds', '60 Seconds',
    'Underscore', 'Instrumental', 'Full Version',
))


class ExtremeMusicBaseIE(InfoExtractor):
    _API_HOST = 'https://snapi.extrememusic.com'
    _API_SITE_ID = '4'
    _API_TOKEN = None

    def _api_headers(self, video_id):
        if not ExtremeMusicBaseIE._API_TOKEN:
            token = traverse_obj(self._download_json(
                'https://www.extrememusic.com/env', video_id,
                'Downloading API token'), ('token', {str}))
            if not token:
                raise ExtractorError('Unable to obtain API token', expected=True)
            ExtremeMusicBaseIE._API_TOKEN = token
        return {
            'Accept': 'application/json',
            'Referer': 'https://www.extrememusic.com/',
            'X-API-Auth': ExtremeMusicBaseIE._API_TOKEN,
            'X-Site-Id': self._API_SITE_ID,
        }

    def _call_api(self, path, video_id, note=None):
        return self._download_json(
            f'{self._API_HOST}/{path}', video_id,
            note or 'Downloading API JSON',
            headers=self._api_headers(video_id))

    def _extract_track_formats(self, track_sounds, default_sound_id=None):
        formats = []
        for sound in traverse_obj(track_sounds, (..., {dict})):
            mp3_url = traverse_obj(sound, ('assets', 'audio', 'preview_url', {url_or_none}))
            if not mp3_url:
                continue
            sound_id = str_or_none(sound.get('id'))
            version_type = traverse_obj(sound, ('version_type', {str})) or 'preview'
            quality = _VERSION_QUALITY(version_type)
            if default_sound_id and sound_id == str(default_sound_id):
                quality += 1
            formats.append({
                'url': mp3_url,
                'format_id': f'http-mp3-{sound_id or version_type}',
                'format_note': traverse_obj(sound, ('version_name', {str})) or version_type,
                'ext': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
                'quality': quality,
                'duration': int_or_none(sound.get('duration')),
            })
        return formats

    def _parse_track(self, track, track_sounds, fatal=True):
        track_id = str_or_none(traverse_obj(track, ('id', {int_or_none})))
        formats = self._extract_track_formats(
            track_sounds, traverse_obj(track, ('default_track_sound_id', {int_or_none})))
        if not formats:
            if fatal:
                self.raise_no_formats(
                    'No public preview is available for this track',
                    expected=True, video_id=track_id)
            return None

        default_id = str_or_none(track.get('default_track_sound_id'))
        default_sound = traverse_obj(track_sounds, (
            lambda _, v: str_or_none(v.get('id')) == default_id, any)) or traverse_obj(
            track_sounds, (0, {dict}))

        return {
            'id': track_id,
            'vcodec': 'none',
            'formats': formats,
            'extractor_key': ExtremeMusicIE.ie_key(),
            'extractor': ExtremeMusicIE.IE_NAME,
            'webpage_url': f'https://www.extrememusic.com/tracks/{track_id}',
            **traverse_obj(track, {
                'title': ('title', {str}),
                'track': ('title', {str}),
                'track_id': ('track_no', {str}),
                'track_number': ('track_no', {lambda x: int_or_none((x or '').rsplit('_', 1)[-1])}),
                'album': ('album_title', {str}),
                'description': ('description', {str}, filter),
                'thumbnail': (('image_large_url', 'image_detail_url', 'image_small_url'), {url_or_none}, any),
                'timestamp': ('release_date', {parse_iso8601}),
                'genres': ('genre', ..., 'label', {str}),
                'tags': (('keywords', 'moods'), ..., 'label', {str}),
                'artists': ('composers', ..., 'name', {str}),
                'composers': ('composers', ..., 'name', {str}),
            }),
            'duration': traverse_obj(default_sound, ('duration', {int_or_none})),
            'age_limit': 18 if traverse_obj(track_sounds, (
                ..., 'explicit_lyrics', {bool}, any)) else None,
        }

    def _entries_from_api(self, data, id_order=None):
        tracks = traverse_obj(data, ('tracks', ..., {dict}))
        sounds_by_track = {}
        for sound in traverse_obj(data, ('track_sounds', ..., {dict})):
            sounds_by_track.setdefault(sound.get('track_id'), []).append(sound)
        track_map = {t.get('id'): t for t in tracks}
        ordered_ids = id_order or [t.get('id') for t in tracks]
        for tid in ordered_ids:
            track = track_map.get(tid)
            if not track:
                continue
            entry = self._parse_track(track, sounds_by_track.get(tid) or [], fatal=False)
            if entry:
                yield entry


class ExtremeMusicIE(ExtremeMusicBaseIE):
    IE_NAME = 'extrememusic'
    IE_DESC = 'Extreme Music'
    _VALID_URL = r'https?://(?:www\.)?extrememusic\.com/tracks/(?P<id>\d+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.extrememusic.com/tracks/111618',
        'md5': 'a7f888591be8f147f96e73569bc64272',
        'info_dict': {
            'id': '111618',
            'ext': 'mp3',
            'title': 'Isle of the Oaks',
            'track': 'Isle of the Oaks',
            'track_id': 'JCE0264_01',
            'track_number': 1,
            'album': 'Ethereal Voices',
            'description': 'md5:df2f31cb6450044343c43d1e5314921e',
            'duration': 232,
            'timestamp': 1601540014,
            'upload_date': '20201001',
            'thumbnail': r're:https://.+\.jpg',
            'genres': ['FOLK'],
            'artists': [
                'Knightstown',
                'Thomas Alfeu Macmagha Aston',
                'Edward John Campbell Ashcroft',
                'Paul Jonathan Ivan Vials',
            ],
            'composers': [
                'Knightstown',
                'Thomas Alfeu Macmagha Aston',
                'Edward John Campbell Ashcroft',
                'Paul Jonathan Ivan Vials',
            ],
            'tags': ['MEDITATION', 'MELANCHOLY', 'CHILL', 'REFLECTIVE', 'SAD'],
        },
    }, {
        'url': 'https://www.extrememusic.com/tracks/111618/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        track_id = self._match_id(url)
        data = self._call_api(f'tracks/{track_id}', track_id, 'Downloading track JSON')
        return self._parse_track(
            traverse_obj(data, ('track', {dict})) or {},
            traverse_obj(data, ('track_sounds', ..., {dict})))


class ExtremeMusicAlbumIE(ExtremeMusicBaseIE):
    IE_NAME = 'extrememusic:album'
    IE_DESC = 'Extreme Music albums'
    _VALID_URL = r'https?://(?:www\.)?extrememusic\.com/albums/(?P<id>\d+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.extrememusic.com/albums/6778',
        'info_dict': {
            'id': '6778',
            'title': 'Ethereal Voices',
            'thumbnail': r're:https://.+\.jpg',
            'timestamp': 1598960334,
            'upload_date': '20200901',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://www.extrememusic.com/albums/6778/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        album_id = self._match_id(url)
        data = self._call_api(f'albums/{album_id}', album_id, 'Downloading album JSON')
        album = traverse_obj(data, ('album', {dict})) or {}
        return self.playlist_result(
            self._entries_from_api(data, traverse_obj(album, ('track_ids', ...))),
            playlist_id=album_id, **traverse_obj(album, {
                'title': ('title', {str}),
                'description': ('description', {str}, filter),
                'thumbnail': (('image_large_url', 'image_detail_url', 'image_small_url'), {url_or_none}, any),
                'timestamp': ('created', {parse_iso8601}),
            }))


class ExtremeMusicPlaylistIE(ExtremeMusicBaseIE):
    IE_NAME = 'extrememusic:playlist'
    IE_DESC = 'Extreme Music playlists'
    _VALID_URL = r'https?://(?:www\.)?extrememusic\.com/playlists/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.extrememusic.com/playlists/8Appff68pKK820pAfAffKApApIrEYdS_AAffKAfUpUKU5KK8UUAUpKU4Kv7s74S',
        'info_dict': {
            'id': '8Appff68pKK820pAfAffKApApIrEYdS_AAffKAfUpUKU5KK8UUAUpKU4Kv7s74S',
            'title': 'TRAILER CANDY',
            'thumbnail': r're:https://.+\.jpg',
            'timestamp': 1533667664,
            'upload_date': '20180807',
        },
        'playlist_mincount': 40,
    }, {
        'url': 'https://www.extrememusic.com/playlists/8Appff68pKK820pAfAffKApApIrEYdS_AAffKAfUpUKU5KK8UUAUpKU4Kv7s74S/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        data = self._call_api(
            f'playlists/{playlist_id}', playlist_id, 'Downloading playlist JSON')
        playlist = traverse_obj(data, ('playlist', {dict})) or {}
        item_order = traverse_obj(data, (
            'playlist_items', ..., 'track_id')) or traverse_obj(
            playlist, ('playlist_item_ids', ...))
        return self.playlist_result(
            self._entries_from_api(data, item_order),
            playlist_id=playlist_id, **traverse_obj(playlist, {
                'title': ('title', {str}),
                'description': ('note', {str}, filter),
                'thumbnail': (('image_large_url', 'image_detail_url', 'image_small_url'), {url_or_none}, any),
                'timestamp': ('created', {parse_iso8601}),
            }))
