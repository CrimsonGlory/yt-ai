from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class SpooncastIE(InfoExtractor):
    IE_NAME = 'spooncast'
    IE_DESC = 'Spoon Radio'
    _VALID_URL = r'https?://(?:www\.)?spooncast\.net/(?P<country>[a-z]{2})/cast/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.spooncast.net/jp/cast/5950201',
        'md5': '1eb9a93b8c9cefae3c7d4397f1eb0f7f',
        'info_dict': {
            'id': '5950201',
            'ext': 'm4a',
            'title': '少し歌を🪽🩵',
            'uploader': 'ｾﾞｾﾞ',
            'uploader_id': 'oq88qr29',
            'uploader_url': 'https://www.spooncast.net/jp/@oq88qr29',
            'channel': 'ｾﾞｾﾞ',
            'channel_id': '315544305',
            'channel_url': 'https://www.spooncast.net/jp/@oq88qr29',
            'channel_is_verified': False,
            'channel_follower_count': int,
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'duration': 4668.0,
            'thumbnail': 'https://jp-cdn.spooncast.net/lives/2024/03/16/92816b9c-17dd-4ec5-af53-bb428c745076.jpg',
            'tags': ['無言滞在歓迎'],
            'timestamp': 1710559036,
            'upload_date': '20240316',
        },
    }, {
        'url': 'https://www.spooncast.net/kr/cast/3899776',
        'only_matching': True,
    }, {
        'url': 'https://spooncast.net/jp/cast/5950201',
        'only_matching': True,
    }]

    @staticmethod
    def _https_url(url):
        url = url_or_none(url)
        if url and url.startswith('http://'):
            return 'https://' + url[7:]
        return url

    def _real_extract(self, url):
        country, video_id = self._match_valid_url(url).group('country', 'id')
        data = self._download_json(
            f'https://{country}-api.spooncast.net/casts/{video_id}/', video_id,
            headers={'Referer': url}, expected_status=(200, 401))
        if traverse_obj(data, 'status_code') not in (None, 200):
            raise ExtractorError(
                traverse_obj(data, ('detail', {str})) or 'Unable to fetch cast metadata',
                expected=True)
        cast = traverse_obj(data, ('results', 0, {dict}))
        if not cast:
            raise ExtractorError('Cast not found', expected=True)

        voice_url = self._https_url(traverse_obj(cast, ('voice_url', {url_or_none})))
        if not voice_url:
            if traverse_obj(cast, 'plan'):
                self.raise_login_required('This cast is only available for members')
            self.raise_no_formats('No public audio URL found', expected=True, video_id=video_id)

        author_tag = traverse_obj(cast, ('author', 'tag', {str}))
        uploader_url = (
            f'https://www.spooncast.net/{country}/@{author_tag}' if author_tag else None)

        return {
            'id': traverse_obj(cast, ('id', {str_or_none})) or video_id,
            'url': voice_url,
            'ext': 'm4a',
            'vcodec': 'none',
            'acodec': 'aac',
            'thumbnail': self._https_url(traverse_obj(cast, ('img_url', {url_or_none}))),
            'timestamp': parse_iso8601(traverse_obj(cast, ('created', {str}))),
            'uploader_url': uploader_url,
            'channel_url': uploader_url,
            **traverse_obj(cast, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'duration': ('duration', {float_or_none}),
                'like_count': ('like_count', {int_or_none}),
                'view_count': ('play_count', {int_or_none}),
                'comment_count': ('text_comment_count', {int_or_none}),
                'tags': ('tags', ..., {str}, filter, all, filter),
                'uploader': ('author', 'nickname', {str}),
                'uploader_id': ('author', 'tag', {str_or_none}),
                'channel': ('author', 'nickname', {str}),
                'channel_id': ('author', 'id', {str_or_none}),
                'channel_follower_count': ('author', 'follower_count', {int_or_none}),
                'channel_is_verified': ('author', 'is_verified', {bool}),
            }),
        }
