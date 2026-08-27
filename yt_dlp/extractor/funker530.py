import json

from .bunnycdn import BunnyCdnIE
from .common import InfoExtractor
from .rumble import RumbleEmbedIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    parse_iso8601,
    smuggle_url,
    traverse_obj,
    urljoin,
)


class Funker530IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funker530\.com/video/(?P<id>[^/?#]+)'
    _API_URL = 'https://api.funker530.com/api/Get'
    # Public Azure Functions key from the site's JS bundle
    _API_CODE = 'sL3mjD-c0BJdI9b9h4s7WhIPU8ca9p6h3yiLyFczS-I9AzFupvbo9g=='
    _BUNNY_LIBRARY_ID = '167129'
    _THUMB_BASE = 'https://images.funker530.com/images/media/'
    _TESTS = [{
        'url': 'https://funker530.com/video/azov-patrol-caught-in-open-under-automatic-grenade-launcher-fire/',
        'md5': '085f50fea27523a388bbc22e123e09c8',
        'info_dict': {
            'id': 'eeb9c731-fa9e-4c38-9200-46a243d282ac',
            'ext': 'mp4',
            'title': 'Azov Patrol Caught In Open Under Automatic Grenade Launcher Fire',
            'display_id': 'azov-patrol-caught-in-open-under-automatic-grenade-launcher-fire',
            'description': 'md5:01cbda51742bcf848009f7f0a4cda844',
            'thumbnail': r're:https?://images\.funker530\.com/.+',
            'timestamp': 1686238080,
            'upload_date': '20230608',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
        },
    }, {
        'url': 'https://funker530.com/video/my-friends-joined-the-russians-civdiv/',
        'md5': 'a42c2933391210662e93e867d7124b70',
        'info_dict': {
            'id': 'k-pk4bOvoac',
            'ext': 'mp4',
            'title': 'My “Friends” joined the Russians.',
        },
        'skip': 'Video gone',
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        videos = self._download_json(
            self._API_URL, display_id,
            query={
                'code': self._API_CODE,
                'slug': display_id,
                'amount': 1,
                'hideNSFW': 'false',
            },
            headers={
                'Content-Type': 'application/json',
                'GetType': 'Video',
                'Origin': 'https://funker530.com',
                'Referer': 'https://funker530.com/',
            })
        video = traverse_obj(videos, 0, expected_type=dict)
        if not video:
            raise ExtractorError('No videos found', expected=True)

        info = {
            'display_id': display_id,
            **traverse_obj(video, {
                'title': ('title', {str}),
                'description': ('ogDescription', {str}, filter),
                'uploader': ('author', {str}, filter),
                'view_count': ('viewCount', {int_or_none}),
                'like_count': ('likes', {int_or_none}),
                'comment_count': ('numberOfComments', {int_or_none}),
                'timestamp': ('publicationDate', {parse_iso8601}),
                'age_limit': ('mature', {lambda x: 18 if x else 0}),
                'tags': ('keywords', {lambda x: [t.strip() for t in x.split(',') if t.strip()]}),
                'thumbnail': ('thumbnail', 'file', {urljoin(self._THUMB_BASE)}),
            }),
        }
        if not info.get('description'):
            info['description'] = clean_html(video.get('description'))

        bunny_id = traverse_obj(video, ('bunnyId', {str}, filter))
        if bunny_id:
            return self.url_result(
                smuggle_url(
                    f'https://iframe.mediadelivery.net/embed/{self._BUNNY_LIBRARY_ID}/{bunny_id}',
                    {'Referer': url}),
                ie=BunnyCdnIE, video_id=bunny_id, url_transparent=True, **info)

        rumble_id = traverse_obj(video, ('rumbleJson', {json.loads}, 'vid', {str}))
        embed_html = video.get('connatixVid') or ''
        rumble_url = rumble_id and f'https://rumble.com/embed/{rumble_id}'
        if not rumble_url:
            rumble_url = traverse_obj(list(RumbleEmbedIE._extract_embed_urls(url, embed_html)), 0)
        if rumble_url:
            return self.url_result(rumble_url, ie=RumbleEmbedIE, url_transparent=True, **info)

        youtube_url = traverse_obj(list(YoutubeIE._extract_embed_urls(url, embed_html)), 0)
        if youtube_url:
            return self.url_result(youtube_url, ie=YoutubeIE, url_transparent=True, **info)

        raise ExtractorError('No videos found', expected=True)
