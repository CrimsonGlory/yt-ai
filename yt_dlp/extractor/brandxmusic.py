from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    join_nonempty,
    parse_duration,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BrandXMusicBaseIE(InfoExtractor):
    _API_URL = 'https://api.cadenzabox.com'
    _ORIGIN = 'https://brandxmusic.net'
    _PAGE_SIZE = 50

    def _call_api(self, resource, video_id, query, note=None):
        return self._download_json(
            f'{self._API_URL}/{resource}', video_id,
            note or 'Downloading JSON metadata', query=query,
            headers={
                'Accept': 'application/json',
                'Origin': self._ORIGIN,
                'Referer': f'{self._ORIGIN}/',
            })

    @staticmethod
    def _localized_text(value):
        if isinstance(value, str):
            return value or None
        return traverse_obj(value, ('en', {str}), (..., {str}, any))

    @staticmethod
    def _person_name(person):
        if not isinstance(person, dict):
            return None
        return join_nonempty(
            person.get('firstName'), person.get('middleName'), person.get('lastName'),
            delim=' ') or None

    @staticmethod
    def _tag_name(tag):
        if isinstance(tag, dict):
            return tag.get('name') or tag.get('id')
        return tag if isinstance(tag, str) else None

    def _parse_track(self, track, track_id=None):
        track_id = track_id or traverse_obj(track, ('slug', {str})) or str_or_none(track.get('_id'))
        audio_url = traverse_obj(track, ('webAudio', {url_or_none}))
        if not audio_url:
            return None
        artists = traverse_obj(track, ('composers', ..., {self._person_name}))
        return {
            'id': track_id,
            'url': audio_url,
            'ext': 'mp3',
            'vcodec': 'none',
            'acodec': 'mp3',
            'webpage_url': f'{self._ORIGIN}/tracks/?tracks={track_id}',
            'duration': (parse_duration(track.get('duration')) or float_or_none(track.get('durationMs'), 1000)),
            'artists': artists,
            'composers': artists,
            **traverse_obj(
                track,
                {
                    'title': ('title', {str}),
                    'track': ('title', {str}),
                    'display_id': ('longSlug', {str}),
                    'description': ('description', {str}, filter),
                    'alt_title': ('versionTitle', {str}, filter),
                    'track_number': ('trackNumber', {int_or_none}),
                    'track_id': ('isrc', {str}),
                    'timestamp': (('releaseDate', ('release', 'releaseDate')), {unified_timestamp}, any),
                    'album': ('release', 'title', {str}),
                    'thumbnail': ((
                        ('release', 'packshot', 'original'),
                        ('release', 'packshot', '750w'),
                        ('release', 'packshot', '300w'),
                        ('release', 'packshotUrl'),
                    ), {url_or_none}, any),
                    'tags': ('tags', ..., {self._tag_name}, {str}),
                },
            ),
        }


class BrandXMusicIE(BrandXMusicBaseIE):
    IE_NAME = 'brandxmusic'
    IE_DESC = 'Brand X Music'
    _VALID_URL = r'https?://(?:www\.)?brandxmusic\.net/tracks/?\?(?:[^#]*&)?tracks=(?P<id>[\w-]+)'
    _TESTS = [
        {
            'url': 'https://www.brandxmusic.net/tracks/?tracks=bxm018-10',
            'md5': 'fe6eb61589c6bfe35ea34910cd03d593',
            'info_dict': {
                'id': 'bxm018-10',
                'ext': 'mp3',
                'title': 'Innocence of Youth',
                'track': 'Innocence of Youth',
                'alt_title': 'Full',
                'display_id': 'bxm018-10-innocence-of-youth-main',
                'description': 'Haunting piano intro. Eerie lullaby at :30 sung by innocent childlike vocal. Harp flourishes. Accompanied by solo cello at :57. Bridge at 1:44.',
                'duration': 185,
                'track_number': 10,
                'track_id': 'BGA471607341',
                'album': 'Volume 12',
                'artists': ['John Sponsler', 'Tom Gire'],
                'composers': ['John Sponsler', 'Tom Gire'],
                'thumbnail': r're:https://storage\.googleapis\.com/cadenzabox-prod-bucket/.+',
                'timestamp': 1269993600,
                'upload_date': '20100331',
                'tags': 'count:41',
                'vcodec': 'none',
            },
        },
        {
            'url': 'https://brandxmusic.net/tracks/?tracks=bxmt17-1',
            'only_matching': True,
        },
        {
            'url': 'https://www.brandxmusic.net/tracks?tracks=bxm018-10',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        track_id = self._match_id(url)
        data = self._call_api('tracks', track_id, {'slug': track_id})
        track = traverse_obj(data, ('data', 0, {dict}))
        if not track:
            raise ExtractorError('Track not found', expected=True)
        info = self._parse_track(track, track_id)
        if not info:
            self.raise_no_formats(
                'No public audio stream is available for this track', expected=True, video_id=track_id,
            )
        return info


class BrandXMusicAlbumIE(BrandXMusicBaseIE):
    IE_NAME = 'brandxmusic:album'
    IE_DESC = 'Brand X Music albums'
    _VALID_URL = r'https?://(?:www\.)?brandxmusic\.net/albums/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [
        {
            'url': 'https://www.brandxmusic.net/albums/bxmt17',
            'info_dict': {
                'id': 'bxmt17',
                'title': 'Xpeditions',
                'description': 'md5:9eac8e8c9a766ee08478b9552c705f94',
                'thumbnail': r're:https://storage\.googleapis\.com/cadenzabox-prod-bucket/.+',
                'timestamp': 1589846400,
                'upload_date': '20200519',
            },
            'playlist_mincount': 20,
        },
        {
            'url': 'https://brandxmusic.net/albums/bxm018',
            'only_matching': True,
        },
    ]

    def _entries(self, release_id, album_id):
        skip = 0
        while True:
            page = self._call_api(
                'tracks',
                album_id,
                {
                    'releaseId': release_id,
                    '$limit': self._PAGE_SIZE,
                    '$skip': skip,
                    '$sort[trackNumber]': 1,
                    '$sort[versionNumber]': 1,
                },
                note=f'Downloading tracks page {skip // self._PAGE_SIZE + 1}',
            )
            tracks = traverse_obj(page, ('data', ..., {dict})) or []
            for track in tracks:
                info = self._parse_track(track)
                if info:
                    yield info
            if len(tracks) < self._PAGE_SIZE:
                break
            skip += self._PAGE_SIZE
            total = int_or_none(page.get('total'))
            if total is not None and skip >= total:
                break

    def _real_extract(self, url):
        album_id = self._match_id(url)
        data = self._call_api('releases', album_id, {'slug': album_id})
        release = traverse_obj(data, ('data', 0, {dict}))
        if not release:
            raise ExtractorError('Album not found', expected=True)
        release_id = traverse_obj(release, ('_id', {str}))
        if not release_id:
            raise ExtractorError('Unable to extract album id', expected=True)

        return self.playlist_result(
            self._entries(release_id, album_id),
            album_id,
            **traverse_obj(
                release,
                {
                    'title': ('title', {str}),
                    'description': ('description', {self._localized_text}),
                    'thumbnail': ((
                        ('packshot', 'original'),
                        ('packshot', '750w'),
                        ('packshot', '300w'),
                        'packshotUrl',
                    ), {url_or_none}, any),
                    'timestamp': ('releaseDate', {unified_timestamp}),
                },
            ),
        )
