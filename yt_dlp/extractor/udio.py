import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class UdioIE(InfoExtractor):
    IE_NAME = 'udio'
    IE_DESC = 'Udio'
    _VALID_URL = r'https?://(?:www\.)?udio\.com/songs/(?P<id>[\w-]+)'
    _STREAM_BASE = 'https://stream.udio.com'
    _STREAM_HEADERS = {
        'Referer': 'https://www.udio.com/',
        'Origin': 'https://www.udio.com',
    }
    _TESTS = [{
        'url': 'https://www.udio.com/songs/ehJuLz9DuCtVapQMVMcA7N',
        'skip': 'DRM: stream.udio.com HLS is SAMPLE-AES; GCS song_path and video_path return AccessDenied',
        'md5': '7a29fc8921e82e8c17f5830a084a428e',
        'info_dict': {
            'id': 'ehJuLz9DuCtVapQMVMcA7N',
            'ext': 'mp4',
            'title': 'Lost Love',
            'track': 'Lost Love',
            'description': 'md5:b338a27482d2a4525bf543fcd6d1b2f4',
            'uploader': "The I Don't Knows",
            'uploader_id': 'ad838917-7454-4b7e-be22-e3d0ab415b4e',
            'artists': ["The I Don't Knows"],
            'thumbnail': r're:https://imagedelivery\.net/.+',
            'duration': 269.461333333333,
            'timestamp': 1714507112,
            'upload_date': '20240430',
            'view_count': int,
            'like_count': int,
            'tags': ['upbeat synthwave', 'serene', 'synth', 'nostalgic', 'introspective',
                     'synthpop', '2019', 'keyboard', 'electric guitar', 'female vocalist'],
        },
    }, {
        'url': 'https://udio.com/songs/ehJuLz9DuCtVapQMVMcA7N',
        'only_matching': True,
    }]

    def _stream_manifest_is_drm(self, manifest, manifest_url, video_id):
        if not manifest:
            return False
        if '#EXT-X-KEY' in manifest:
            return True
        media_path = next((
            line.strip() for line in manifest.splitlines()
            if line.strip() and not line.startswith('#')), None)
        if not media_path or '.m3u8' not in media_path:
            return False
        media = self._download_webpage(
            urllib.parse.urljoin(manifest_url, media_path), video_id,
            'Downloading media playlist', fatal=False, headers=self._STREAM_HEADERS)
        return bool(media and '#EXT-X-KEY' in media)

    def _real_extract(self, url):
        song_id = self._match_id(url)
        song = traverse_obj(
            self._download_json(
                'https://www.udio.com/api/songs', song_id,
                query={'songIds': song_id}, headers={'Accept': 'application/json'}),
            ('songs', 0, {dict}))
        if not song:
            raise ExtractorError('Song not found', expected=True)

        formats = []
        api_id = traverse_obj(song, ('id', {str})) or song_id
        transform = traverse_obj(song, ('transformation_hash', {str}))
        stream_url = f'{self._STREAM_BASE}/stream/{api_id}'
        if transform:
            stream_url = f'{stream_url}/{transform}'
        manifest = self._download_webpage(
            stream_url, song_id, 'Downloading stream manifest', fatal=False,
            headers=self._STREAM_HEADERS)
        if manifest and manifest.lstrip().startswith('#EXTM3U'):
            if self._stream_manifest_is_drm(manifest, stream_url, song_id):
                self.report_drm(song_id)
            formats.extend(self._extract_m3u8_formats(
                stream_url, song_id, 'm4a', m3u8_id='hls', fatal=False,
                headers=self._STREAM_HEADERS))

        # Legacy public objects. The player no longer uses these; the bucket is
        # anonymous-denied when a stream manifest exists.
        if not formats:
            audio_url = traverse_obj(song, ('song_path', {url_or_none}))
            if audio_url:
                formats.append({
                    'url': audio_url,
                    'format_id': 'http-mp3',
                    'ext': 'mp3',
                    'vcodec': 'none',
                    'acodec': 'mp3',
                })
            video_url = traverse_obj(song, ('video_path', {url_or_none}))
            if video_url:
                formats.append({
                    'url': video_url,
                    'format_id': 'http-mp4',
                    'ext': 'mp4',
                })
        if not formats:
            self.raise_no_formats('No public media found', expected=True, video_id=song_id)

        return {
            'id': song_id,
            'formats': formats,
            **traverse_obj(song, {
                'title': ('title', {str}),
                'track': ('title', {str}),
                'artists': ('artist', {str}, filter, all),
                'uploader': ('artist', {str}),
                'uploader_id': ('user_id', {str}),
                'thumbnail': ('image_path', {url_or_none}),
                'description': (('lyrics', 'prompt'), {str}, filter, any),
                'duration': ('duration', {float_or_none}),
                'timestamp': (('published_at', 'created_at'), {parse_iso8601}, any),
                'view_count': ('plays', {int_or_none}),
                'like_count': ('likes', {int_or_none}),
                'tags': ('tags', ..., {strip_or_none}, filter),
            }),
        }
