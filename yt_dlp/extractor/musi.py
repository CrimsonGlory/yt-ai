import json

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    traverse_obj,
)


class MusiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?feelthemusi\.com/(?:playlist|api/v4/playlists/fetch)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://feelthemusi.com/playlist/een9re',
        'info_dict': {
            'id': 'een9re',
            'title': 'Example',
        },
        'playlist_mincount': 1,
        'playlist': [{
            'md5': '54f5ec7f607f9a228579c0b1994edfa6',
            'info_dict': {
                'id': '6ONlT1H8djA',
                'ext': 'mp4',
                'title': 'Wonderland',
                'alt_title': 'Wonderland',
                'description': 'md5:887dfec8edb78de80cc4668b22031695',
                'media_type': 'video',
                'uploader': 'Alexander Nakarada - CreatorChords',
                'channel': 'Alexander Nakarada - CreatorChords',
                'channel_id': 'UCXiw-2gHe37qD0k5vVd-Ueg',
                'channel_url': 'https://www.youtube.com/channel/UCXiw-2gHe37qD0k5vVd-Ueg',
                'channel_is_verified': True,
                'channel_follower_count': int,
                'view_count': int,
                'like_count': int,
                'age_limit': 0,
                'duration': 354,
                'thumbnail': r're:https?://i\.ytimg\.com/.+',
                'categories': ['Music'],
                'tags': ['Alexander Nakarada', 'Fantasy Fair', 'Wonderland'],
                'artists': ['Alexander Nakarada'],
                'creators': ['Alexander Nakarada'],
                'track': 'Wonderland',
                'album': 'Fantasy Fair',
                'timestamp': 1703793530,
                'upload_date': '20231228',
                'release_date': '20210115',
                'playable_in_embed': True,
                'availability': 'public',
                'live_status': 'not_live',
            },
        }],
        'params': {
            'playlist_items': '1',
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
            'Signature solving failed',
        ],
    }, {
        'url': 'https://feelthemusi.com/playlist/een9re',
        'info_dict': {
            'id': 'een9re',
            'title': 'Example',
        },
        'playlist_mincount': 30,
    }, {
        'url': 'https://www.feelthemusi.com/playlist/een9re',
        'only_matching': True,
    }, {
        'url': 'https://feelthemusi.com/api/v4/playlists/fetch/een9re',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        data = self._download_json(
            f'https://feelthemusi.com/api/v4/playlists/fetch/{playlist_id}', playlist_id)

        error = traverse_obj(data, ('error', {str}))
        if error:
            raise ExtractorError(error, expected=True)

        playlist = traverse_obj(data, ('success', {dict}))
        if not playlist:
            raise ExtractorError('Unable to extract playlist', expected=True)

        video_ids = traverse_obj(playlist, (
            'data', {json.loads}, 'data', ..., 'video_id', {str}))
        if not video_ids:
            raise ExtractorError('No videos found in playlist', expected=True)

        return self.playlist_from_matches(
            video_ids, playlist_id, playlist.get('title'), ie=YoutubeIE)
