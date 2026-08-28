from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class MyVidsterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.myvidster.com/video/664906',
        'md5': 'a6ee16863acd8e969d6ea89db15ba4c1',
        'info_dict': {
            'id': '93RkWNK3BZc',
            'ext': 'mp4',
            'title': 'Crazy Oklahoma State Interception vs. Oklahoma - November 27, 2010',
            'description': 'md5:1358c34e2ab8dd099bae23605be788ce',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'timestamp': 1290912817,
            'upload_date': '20101128',
            'uploader': 'thesportsgeeks',
            'uploader_id': '@thesportsgeeks',
            'uploader_url': 'https://www.youtube.com/@thesportsgeeks',
            'channel': 'thesportsgeeks',
            'channel_id': 'UCW7KbD2WKQ96o2x6kRYFkIg',
            'channel_url': 'https://www.youtube.com/channel/UCW7KbD2WKQ96o2x6kRYFkIg',
            'channel_follower_count': int,
            'duration': 50,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'categories': ['Sports'],
            'tags': ['oklahoma', 'state', 'osu', 'ou', 'interception', 'highlight', 'tip', 'out', 'of', 'bounds', 'crazy', 'tipped', 'ball', 'pick'],
            'age_limit': 0,
            'availability': 'public',
            'live_status': 'not_live',
            'playable_in_embed': True,
            'media_type': 'video',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
        ],
    }, {
        'url': 'http://www.myvidster.com/video/32059805/Hot_chemistry_with_raw_love_making',
        'skip': 'Video gone',
        'md5': '95296d0231c1363222c3441af62dc4ca',
        'info_dict': {
            'id': '3685814',
            'title': 'md5:7d8427d6d02c4fbcef50fe269980c749',
            'upload_date': '20141027',
            'uploader': 'utkualp',
            'ext': 'mp4',
            'age_limit': 18,
        },
        'add_ie': ['XHamster'],
    }]

    @staticmethod
    def _source_url(video):
        type_url = url_or_none(video.get('type_url'))
        type_id = video.get('type_id')
        type_id_url = url_or_none(type_id)

        def usable(candidate):
            return candidate and 'undefined' not in candidate and 'myvidster.com/' not in candidate

        if usable(type_url):
            return type_url
        if usable(type_id_url):
            return type_id_url
        if type_id and not type_id_url:
            return f'https://www.youtube.com/watch?v={type_id}'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'https://api.myvidster.com/v1', video_id,
            query={'action': 'video', 'id': video_id})
        if not data.get('ok'):
            raise ExtractorError(
                traverse_obj(data, ('error', 'message'), default='Unable to fetch video'),
                expected=True)

        video = data.get('video') or {}
        real_url = self._source_url(video)
        if not real_url:
            raise ExtractorError('Unable to extract source video URL', expected=True)

        return self.url_result(real_url)
