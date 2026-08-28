from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class OfTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?of\.tv/(?:video|v)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://of.tv/v/zjtc6',
        'md5': 'fcdffb9e0a375851d53a939b45313a8c',
        'info_dict': {
            'id': 'zjtc6',
            'ext': 'mp4',
            'title': 'S1E1: Monte Cristo Sandwich',
            'description': 'md5:89a6a3404540e9d5a4ec9ffa63a85d4d',
            'thumbnail': r're:https?://.*',
            'duration': 1423,
            'timestamp': 1652394900,
            'upload_date': '20220512',
            'creator': 'This is Fire',
            'creators': ['This is Fire'],
            'channel': 'This is Fire',
            'channel_id': '9iGia',
            'uploader_id': 'this-is-fire',
            'tags': ['Originals'],
        },
    }, {
        'url': 'https://of.tv/video/627d7d95b353db0001dadd1a',
        'only_matching': True,
    }, {
        'url': 'https://of.tv/v/zjtc6/embed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = traverse_obj(
            self._download_json(f'https://api.of.tv/v0/videos/{video_id}', video_id),
            ('data', 'video', {dict}))
        if not video:
            raise ExtractorError('Video not found', expected=True)

        video_id = video.get('unique_id') or video_id
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            video['video_src'], video_id, 'mp4', m3u8_id='hls')

        for sub in traverse_obj(video, ('transcript', ...)):
            sub_url = traverse_obj(sub, ('url', {url_or_none}))
            if sub_url:
                subtitles.setdefault('en', []).append({
                    'url': sub_url,
                    'ext': traverse_obj(sub, ('type', {str})),
                })

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'tags': traverse_obj(video, ('genres', ..., 'name', {str})),
            **traverse_obj(video, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('published_at', {parse_iso8601}),
                'thumbnail': ('thumbnail_url', {url_or_none}),
                'creator': ('creator', 'channel_name', {str}),
                'channel': ('creator', 'channel_name', {str}),
                'channel_id': ('creator', 'unique_id', {str}),
                'uploader_id': ('creator', 'oftv_handle', {str}),
            }),
        }


class OfTVPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?of\.tv/(?:creators?|c)/(?P<id>[a-zA-Z0-9-]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://of.tv/c/this-is-fire',
        'playlist_mincount': 8,
        'info_dict': {
            'id': 'this-is-fire',
            'title': 'This is Fire',
        },
    }, {
        'url': 'https://of.tv/creators/this-is-fire/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        data = self._download_json(
            f'https://api.of.tv/v0/pages/creators/{playlist_id}', playlist_id)
        creator = traverse_obj(data, ('data', 'creator', {dict}))
        if not creator:
            raise ExtractorError('Creator not found', expected=True)

        return self.playlist_from_matches(
            traverse_obj(data, ('data', 'creator_playlist', 'items', ..., 'unique_id', {str})),
            playlist_id, traverse_obj(creator, ('channel_name', {str})),
            getter=lambda vid: f'https://of.tv/v/{vid}', ie=OfTVIE)
