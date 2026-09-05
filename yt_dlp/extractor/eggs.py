import secrets

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class EggsBaseIE(InfoExtractor):
    _API_HEADERS = {
        'Accept': '*/*',
        'apVersion': '8.2.00',
        'deviceName': 'Android',
    }

    def _real_initialize(self):
        self._API_HEADERS['deviceId'] = secrets.token_hex(8)

    def _call_api(self, endpoint, video_id):
        return self._download_json(
            f'https://app-front-api.eggs.mu/v1/{endpoint}', video_id,
            headers=self._API_HEADERS)

    def _extract_music_info(self, data):
        if yt_url := traverse_obj(data, ('youtubeUrl', {url_or_none})):
            return self.url_result(yt_url, ie=YoutubeIE)

        artist_name = traverse_obj(data, ('artist', 'artistName', {str_or_none}))
        music_id = traverse_obj(data, ('musicId', {str_or_none}))
        webpage_url = None
        if artist_name and music_id:
            webpage_url = f'https://eggs.mu/artist/{artist_name}/song/{music_id}'

        return {
            'id': music_id,
            'vcodec': 'none',
            'webpage_url': webpage_url,
            'extractor_key': EggsIE.ie_key(),
            'extractor': EggsIE.IE_NAME,
            **traverse_obj(data, {
                'title': ('musicTitle', {str}),
                'url': ('musicDataPath', {url_or_none}),
                'uploader': ('artist', 'displayName', {str}),
                'uploader_id': ('artist', 'artistId', {str_or_none}),
                'thumbnail': ('imageDataPath', {url_or_none}),
                'view_count': ('numberOfMusicPlays', {int_or_none}),
                'like_count': ('numberOfLikes', {int_or_none}),
                'comment_count': ('numberOfComments', {int_or_none}),
                'composers': ('composer', {str}, all),
                'tags': ('tags', ..., {str}),
                'timestamp': ('releaseDate', {parse_iso8601}),
                'artist': ('artist', 'displayName', {str}),
            })}


class EggsIE(EggsBaseIE):
    IE_NAME = 'eggs:single'
    _VALID_URL = r'https?://eggs\.mu/artist/[^/?#]+/song/(?P<id>[\da-f-]+)'

    _TESTS = [
        {
            'url': 'https://eggs.mu/artist/okuba_010101/song/4f5e3632-59fa-4a0a-826a-d50769941de9',
            'md5': '30051cb7bc6abc93838201f61560b0f2',
            'info_dict': {
                'id': '4f5e3632-59fa-4a0a-826a-d50769941de9',
                'ext': 'm4a',
                'title': '指先',
                'uploader': "the奥歯's",
                'uploader_id': '23808',
                'thumbnail': 'md5:f5f2792698ef7138e0faf1bfdba92fa7',
                'timestamp': 1770364800,
                'upload_date': '20260206',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'composers': [''],
                'artists': ["the奥歯's"],
            },
        }, {
        'url': 'https://eggs.mu/artist/32_sunny_girl/song/0e95fd1d-4d61-4d5b-8b18-6092c551da90',
        'info_dict': {
            'id': '0e95fd1d-4d61-4d5b-8b18-6092c551da90',
            'ext': 'm4a',
            'title': 'シネマと信号',
            'uploader': 'Sunny Girl',
            'thumbnail': r're:https?://.*\.jpg(?:\?.*)?$',
            'uploader_id': '1607',
            'like_count': int,
            'timestamp': 1731327327,
            'composers': ['橘高連太郎'],
            'view_count': int,
            'comment_count': int,
            'artists': ['Sunny Girl'],
            'upload_date': '20241111',
            'tags': ['SunnyGirl', 'シネマと信号'],
        },
    }, {
        'url': 'https://eggs.mu/artist/KAMO_3pband/song/1d4bc45f-1af6-47a9-8b30-a70cae350b4f',
        'skip': 'stale test sample / site changed',
        'info_dict': {
            'id': '80cLKA2wnoA',
            'ext': 'mp4',
            'title': 'KAMO「いい女だから」Audio',
            'uploader': 'KAMO',
            'live_status': 'not_live',
            'channel_id': 'UCsHLBw2__5Q9y55skXPotOg',
            'channel_follower_count': int,
            'description': 'md5:d260da711ecbec3e720293dc11401b87',
            'availability': 'public',
            'uploader_id': '@KAMO_band',
            'upload_date': '20240925',
            'thumbnail': 'https://i.ytimg.com/vi/80cLKA2wnoA/maxresdefault.jpg',
            'comment_count': int,
            'channel_url': 'https://www.youtube.com/channel/UCsHLBw2__5Q9y55skXPotOg',
            'view_count': int,
            'duration': 151,
            'like_count': int,
            'channel': 'KAMO',
            'playable_in_embed': True,
            'uploader_url': 'https://www.youtube.com/@KAMO_band',
            'tags': [],
            'timestamp': 1727271121,
            'age_limit': 0,
            'categories': ['People & Blogs'],
        },
        'add_ie': ['Youtube'],
        'params': {'skip_download': 'Youtube'},
    }]

    def _real_extract(self, url):
        song_id = self._match_id(url)
        json_data = self._call_api(f'musics/{song_id}', song_id)
        return self._extract_music_info(json_data)


class EggsArtistIE(EggsBaseIE):
    IE_NAME = 'eggs:artist'
    _VALID_URL = r'https?://eggs\.mu/artist/(?P<id>\w+)/?(?:[?#&]|$)'

    _TESTS = [{
        'url': 'https://eggs.mu/artist/strobogram_band',
        'info_dict': {
            'id': 'strobogram_band',
            'title': 'strobogram',
            'description': '都内で活動中の4ピースバンド。',
            'thumbnail': r're:https?://image-pro\.eggs\.mu/profile/\d+\.jpe?g(?:\?.*)?$',
        },
        'playlist_mincount': 2,
        'params': {'skip_download': True},
    }, {
        'url': 'https://eggs.mu/artist/32_sunny_girl',
        'info_dict': {
            'id': '32_sunny_girl',
            'title': 'Sunny Girl',
            'description': 'Muddy Mine / 東京高田馬場CLUB PHASE / Gt.Vo 橘高 連太郎 / Ba.Cho 小野 ゆうき / Dr 大森 りゅうひこ',
            'thumbnail': r're:https?://image-pro\.eggs\.mu/profile/\d+\.jpe?g(?:\?.*)?$',
        },
        'playlist_mincount': 18,
        'params': {'skip_download': True},
    }, {
        'url': 'https://eggs.mu/artist/KAMO_3pband',
        'info_dict': {
            'id': 'KAMO_3pband',
            'title': 'KAMO',
            'description': '川崎発３ピースバンド',
            'thumbnail': r're:https?://image-pro\.eggs\.mu/profile/\d+\.jpe?g(?:\?.*)?$',
        },
        'playlist_mincount': 2,
        'params': {'skip_download': True},
    }]

    def _real_extract(self, url):
        artist_id = self._match_id(url)
        artist_data = self._call_api(f'artists/{artist_id}', artist_id)
        song_data = self._call_api(f'artists/{artist_id}/musics', artist_id)
        return self.playlist_result(
            traverse_obj(song_data, ('data', ..., {dict}, {self._extract_music_info})),
            playlist_id=artist_id, **traverse_obj(artist_data, {
                'title': ('displayName', {str}),
                'description': ('profile', {str}),
                'thumbnail': ('imageDataPath', {url_or_none}),
            }))
