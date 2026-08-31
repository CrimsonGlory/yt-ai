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
    _TESTS = [{
        'url': 'https://www.udio.com/songs/ehJuLz9DuCtVapQMVMcA7N',
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
