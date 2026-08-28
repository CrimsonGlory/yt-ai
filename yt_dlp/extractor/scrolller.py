import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ScrolllerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?scrolller\.com/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://scrolller.com/a-helping-hand-1k9pxikxkw',
        'md5': 'cee62f8f16685fdd3558248e13a6c1af',
        'info_dict': {
            'id': 'a-helping-hand-1k9pxikxkw',
            'ext': 'mp4',
            'thumbnail': r're:https://images\.scrolller\.com/.+',
            'title': 'A helping hand',
            'age_limit': 0,
        },
    }, {
        'url': 'https://scrolller.com/tigers-chasing-a-drone-c5d1f2so6j',
        'info_dict': {
            'id': 'tigers-chasing-a-drone-c5d1f2so6j',
            'ext': 'mp4',
            'thumbnail': r're:https://images\.scrolller\.com/.+',
            'title': 'Tigers chasing a drone',
            'age_limit': 0,
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://scrolller.com/baby-rhino-smells-something-9chhugsv9p',
        'info_dict': {
            'id': 'baby-rhino-smells-something-9chhugsv9p',
            'ext': 'mp4',
            'thumbnail': r're:https://images\.scrolller\.com/.+',
            'title': 'Baby rhino smells something',
            'age_limit': 0,
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://scrolller.com/its-all-fun-and-games-cco8jjmoh7',
        'info_dict': {
            'id': 'its-all-fun-and-games-cco8jjmoh7',
            'ext': 'mp4',
            'thumbnail': r're:https://images\.scrolller\.com/.+',
            'title': 'It\'s all fun and games...',
            'age_limit': 0,
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://scrolller.com/may-the-force-be-with-you-octokuro-yeytg1fs7a',
        'info_dict': {
            'id': 'may-the-force-be-with-you-octokuro-yeytg1fs7a',
            'ext': 'mp4',
            'thumbnail': r're:https://.+\.(?:jpg|jpeg|webp)',
            'title': 'May the force be with you (Octokuro)',
            'age_limit': 18,
        },
        'params': {'skip_download': True},
    }]
    _GRAPHQL_QUERY = '''
        query SubredditPostQuery($url: String!) {
            getPost(data: { url: $url }) {
                title
                isNsfw
                mediaSources {
                    url
                    width
                    height
                }
            }
        }'''

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = traverse_obj(self._download_json(
            'https://api.scrolller.com/admin', video_id,
            data=json.dumps({
                'query': self._GRAPHQL_QUERY,
                'variables': {'url': f'/{video_id}'},
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Accept': '*/*',
            }), ('data', 'getPost', {dict}))
        if not video_data:
            raise ExtractorError('Unable to extract post', expected=True, video_id=video_id)

        formats, thumbnails = [], []
        for source in traverse_obj(video_data, ('mediaSources', ..., {dict})):
            media_url = url_or_none(source.get('url'))
            if not media_url:
                continue
            media = {
                'url': media_url,
                'width': int_or_none(source.get('width')),
                'height': int_or_none(source.get('height')),
            }
            if determine_ext(media_url) in ('jpg', 'jpeg', 'png', 'webp'):
                thumbnails.append(media)
            else:
                formats.append(media)

        if not formats:
            self.raise_no_formats('There is no video.', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'title': video_data.get('title'),
            'thumbnails': thumbnails,
            'formats': formats,
            'age_limit': 18 if video_data.get('isNsfw') else 0,
        }
