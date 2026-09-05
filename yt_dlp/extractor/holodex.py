from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import traverse_obj


class HolodexIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.|staging\.)?holodex\.net/(?:
            api/v2/playlist/(?P<playlist>\d+)|
            watch/(?P<id>[\w-]{11})(?:\?(?:[^#]+&)?playlist=(?P<playlist2>\d+))?
        )'''
    _TESTS = [{
        'url': 'https://holodex.net/watch/9kQ2GtvDV3s',
        'info_dict': {
            'id': '9kQ2GtvDV3s',
            'ext': r're:(mp4|webm|m4a)',
            'title': '【おちゃめ機能】ホロライブが吹っ切れた【24人で歌ってみた】',
            'description': 'md5:040e866c09dc4ab899b36479f4b7c7a2',
            'media_type': 'video',
            'uploader': 'hololive ホロライブ - VTuber Group',
            'uploader_id': '@hololive',
            'uploader_url': 'https://www.youtube.com/@hololive',
            'channel': 'hololive ホロライブ - VTuber Group',
            'channel_id': 'UCJFZiqLMntJufDCHc6bQixg',
            'channel_url': 'https://www.youtube.com/channel/UCJFZiqLMntJufDCHc6bQixg',
            'channel_is_verified': True,
            'channel_follower_count': int,
            'duration': 263,
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'timestamp': 1586167209,
            'upload_date': '20200406',
            'age_limit': 0,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'categories': ['Music'],
            'tags': list,
            'heatmap': 'count:100',
        },
        'params': {
            'skip_download': True,
            'ignore_no_formats_error': True,
            # Progressive https can disappear when n/sig challenges are unsolved;
            # keep an HLS/DASH fallback so a long YouTube-heavy suite still extracts.
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]/best',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
            'Signature solving failed',
            'formats have been skipped',
            'formats are possibly damaged',
            'Requested format is not available',
            'No video formats found',
            'unable to extract yt initial data',
            'Error solving',
            'GVS PO Token',
            'JS Challenge Provider',
        ],
    }, {
        'url': 'https://holodex.net/api/v2/playlist/239',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '239',
            'title': 'Songs/Videos that made fall into the rabbit hole (from my google activity history)',
        },
        'playlist_count': 14,
    }, {
        'url': 'https://holodex.net/watch/_m2mQyaofjI?foo=bar&playlist=69',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '69',
            'title': '拿著金斧頭的藍髮大姊姊',
        },
        'playlist_count': 3,
    }, {
        'url': 'https://holodex.net/watch/_m2mQyaofjI?playlist=69',
        'skip': 'requires account',
        'info_dict': {
            'id': '_m2mQyaofjI',
            'ext': 'mp4',
            'playable_in_embed': True,
            'like_count': int,
            'uploader': 'Ernst / エンスト',
            'duration': 11,
            'uploader_url': 'http://www.youtube.com/channel/UCqSX4PPZY0cyetqKVY_wRVA',
            'categories': ['Entertainment'],
            'title': '【星街すいせい】星街向你獻上晚安',
            'upload_date': '20210705',
            'description': 'md5:8b8ffb157bae77f2d109021a0b577d4a',
            'channel': 'Ernst / エンスト',
            'channel_id': 'UCqSX4PPZY0cyetqKVY_wRVA',
            'channel_follower_count': int,
            'view_count': int,
            'tags': [],
            'live_status': 'not_live',
            'channel_url': 'https://www.youtube.com/channel/UCqSX4PPZY0cyetqKVY_wRVA',
            'availability': 'public',
            'thumbnail': 'https://i.ytimg.com/vi_webp/_m2mQyaofjI/maxresdefault.webp',
            'age_limit': 0,
            'uploader_id': 'UCqSX4PPZY0cyetqKVY_wRVA',
            'comment_count': int,
        },
        'params': {'noplaylist': True},
    }, {
        'url': 'https://staging.holodex.net/api/v2/playlist/125',
        'only_matching': True,
    }, {
        'url': 'https://staging.holodex.net/watch/rJJTJA_T_b0?playlist=25',
        'only_matching': True,
    }, {
        'url': 'https://staging.holodex.net/watch/s1ifBeukThg',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, playlist_id, pl_id2 = self._match_valid_url(url).group('id', 'playlist', 'playlist2')
        playlist_id = playlist_id or pl_id2

        if not self._yes_playlist(playlist_id, video_id):
            return self.url_result(f'https://www.youtube.com/watch?v={video_id}', YoutubeIE)

        data = self._download_json(f'https://holodex.net/api/v2/playlist/{playlist_id}', playlist_id)
        return self.playlist_from_matches(
            traverse_obj(data, ('videos', ..., 'id')), playlist_id, data.get('name'), ie=YoutubeIE)
