from .audiomack import AudiomackAlbumIE, AudiomackIE
from .audius import AudiusIE, AudiusTrackIE
from .bandcamp import BandcampAlbumIE, BandcampIE
from .common import InfoExtractor
from .soundcloud import SoundcloudIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    float_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj

_UUID_RE = r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}'


class MusicBrainzBaseIE(InfoExtractor):
    _API_HEADERS = {
        'Accept': 'application/json',
        'User-Agent': 'yt-ai/musicbrainz (https://github.com/yt-dlp/yt-dlp/issues/13673)',
    }
    _MEDIA_IES = (
        YoutubeIE,
        SoundcloudIE,
        AudiusIE,
        AudiusTrackIE,
        AudiomackIE,
        AudiomackAlbumIE,
        BandcampIE,
        BandcampAlbumIE,
    )

    def _download_mb_json(self, path, video_id, query=None):
        return self._download_json(
            f'https://musicbrainz.org/ws/2/{path}', video_id,
            'Downloading MusicBrainz JSON',
            query={'fmt': 'json', **(query or {})},
            headers=self._API_HEADERS)

    def _iter_url_relations(self, entity):
        yield from traverse_obj(entity, ('relations', ..., 'url', 'resource', {url_or_none}))

    def _first_supported_url(self, entity):
        best = None
        for media_url in self._iter_url_relations(entity):
            for order, ie in enumerate(self._MEDIA_IES):
                if ie.suitable(media_url) and (best is None or order < best[0]):
                    best = (order, media_url, ie)
                    break
        if not best:
            return None
        return best[1], best[2]

    def _recording_info(self, recording, album=None):
        title = recording.get('title')
        recording_id = recording.get('id')
        return {k: v for k, v in {
            'id': recording_id,
            'title': title,
            'track': title,
            'track_id': recording_id,
            'artists': traverse_obj(recording, ('artist-credit', ..., 'name', {str})) or None,
            'album': album or traverse_obj(recording, ('releases', 0, 'title', {str})),
            'duration': float_or_none(recording.get('length'), scale=1000),
            'release_date': unified_strdate(recording.get('first-release-date')),
        }.items() if v is not None}

    def _media_url_result(self, entity, extra=None):
        media = self._first_supported_url(entity)
        if not media:
            return None
        media_url, ie = media
        return self.url_result(media_url, ie=ie, url_transparent=True, **(extra or {}))


class MusicBrainzIE(MusicBrainzBaseIE):
    IE_NAME = 'musicbrainz'
    IE_DESC = 'MusicBrainz recordings'
    _VALID_URL = rf'https?://(?:(?:www|beta)\.)?musicbrainz\.org/recording/(?P<id>{_UUID_RE})'
    _TESTS = [{
        'url': 'https://musicbrainz.org/recording/01a292ae-371a-4a46-bc82-f21c30f0bf0e',
        'skip': 'requires account',
        'md5': 'ea6995055d6649a573a0fdab22690482',
        'info_dict': {
            'id': 'pQEz62B2ASY',
            'ext': 'mp4',
            'title': 'Borough of Broadkill',
            'track': 'Borough of Broadkill',
            'track_id': '01a292ae-371a-4a46-bc82-f21c30f0bf0e',
            'artists': ['Riedler Musics'],
            'album': 'Borough of Broadkill',
            'duration': 118.0,
            'release_date': '20210731',
            'release_year': 2021,
            'description': 'md5:c9d78bfdb6a37f9ccbc6eb1dc9f92656',
            'uploader': 'Riedler Musics',
            'uploader_id': '@RiedlerMusics',
            'uploader_url': 'https://www.youtube.com/@RiedlerMusics',
            'channel': 'Riedler Musics',
            'channel_id': 'UC0aIZx6FIHB5Fq_sr0TMXSw',
            'channel_url': 'https://www.youtube.com/channel/UC0aIZx6FIHB5Fq_sr0TMXSw',
            'channel_follower_count': int,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1627748220,
            'upload_date': '20210731',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Music'],
            'tags': 'count:13',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
            'license': 'Creative Commons Attribution license (reuse allowed)',
            'location': 'LINZ',
        },
        'add_ie': ['Youtube'],
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
            'unable to extract yt initial data',
        ],
    }, {
        'url': 'https://beta.musicbrainz.org/recording/01a292ae-371a-4a46-bc82-f21c30f0bf0e',
        'only_matching': True,
    }, {
        'url': 'https://www.musicbrainz.org/recording/01a292ae-371a-4a46-bc82-f21c30f0bf0e',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        recording_id = self._match_id(url)
        data = self._download_mb_json(
            f'recording/{recording_id}', recording_id,
            query={'inc': 'url-rels+artist-credits+releases'})
        info = self._media_url_result(data, extra=self._recording_info(data))
        if not info:
            raise ExtractorError('No supported streaming links found', expected=True)
        return info


class MusicBrainzReleaseIE(MusicBrainzBaseIE):
    IE_NAME = 'musicbrainz:release'
    IE_DESC = 'MusicBrainz releases'
    _VALID_URL = rf'https?://(?:(?:www|beta)\.)?musicbrainz\.org/release/(?P<id>{_UUID_RE})'
    _TESTS = [{
        'url': 'https://musicbrainz.org/release/210f2efa-c0d1-4598-a9e0-f8089f25d10a',
        'only_matching': True,
    }, {
        'url': 'https://musicbrainz.org/release/14ff6f9b-6848-4252-97c5-3a8426eeff8a',
        'only_matching': True,
    }]

    def _browse_recordings(self, release_id):
        offset = 0
        while True:
            page = self._download_mb_json('recording', release_id, query={
                'release': release_id,
                'inc': 'url-rels+artist-credits',
                'limit': 100,
                'offset': offset,
            })
            recordings = page.get('recordings') or []
            yield from recordings
            if len(recordings) < 100:
                return
            offset += len(recordings)
            self._sleep(1, release_id)

    def _real_extract(self, url):
        release_id = self._match_id(url)
        data = self._download_mb_json(
            f'release/{release_id}', release_id,
            query={'inc': 'url-rels+artist-credits'})
        title = data.get('title')

        album_media = self._first_supported_url(data)
        if album_media:
            media_url, ie = album_media
            return self.url_result(media_url, ie=ie)

        self._sleep(1, release_id)
        entries = []
        for recording in self._browse_recordings(release_id):
            info = self._media_url_result(
                recording, extra=self._recording_info(recording, album=title))
            if info:
                entries.append(info)

        if not entries:
            raise ExtractorError('No supported streaming links found', expected=True)
        return self.playlist_result(entries, release_id, title)
