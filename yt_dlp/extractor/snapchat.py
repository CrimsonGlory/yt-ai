from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    format_field,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class SnapchatSpotlightIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?snapchat\.com/spotlight/(?P<id>\w+)'

    _TESTS = [{
        'url': 'https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYYWtidGhudGZpAX1TKn0JAX1TKnXJAAAAAA',
        'md5': '401e2841f6e055ced4fd7aafb041d86b',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYYWtidGhudGZpAX1TKn0JAX1TKnXJAAAAAA',
            'ext': 'mp4',
            'title': 'Views 💕',
            'description': 'Views 💕',
            'uploader': 'shreypatel57',
            'uploader_url': 'https://www.snapchat.com/@shreypatel57',
            'duration': 5,
            'thumbnail': r're:https://cf-st\.sc-cdn\.net/.+',
            'timestamp': 1637777831.369,
            'upload_date': '20211124',
            'repost_count': int,
            'like_count': int,
            'width': 540,
            'height': 960,
        },
    }, {
        'url': 'https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYcnVjYWdwcGV1AZEaIYn5AZEaIYnrAAAAAQ',
        'skip': 'video gone',
        'md5': '4cd9626458c1a0e3e6dbe72c544a9ec2',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYcnVjYWdwcGV1AZEaIYn5AZEaIYnrAAAAAQ',
            'ext': 'mp4',
            'title': 'Spotlight Snap',
            'description': 'How he flirt her teacher🤭🤭🤩😍 #kdrama#cdrama #dramaclips #dramaspotlight',
            'thumbnail': r're:https://cf-st\.sc-cdn\.net/i/ztfr6xFs0FOcFhwVczWfj\.256\.IRZXSOY',
            'duration': 10.91,
            'timestamp': 1722720291.307,
            'upload_date': '20240803',
            'view_count': int,
            'repost_count': int,
            'uploader': 'ganda0535',
            'uploader_url': 'https://www.snapchat.com/add/ganda0535',
            'tags': ['#dramaspotlight', '#dramaclips', '#cdrama', '#kdrama'],
        },
    }]

    def _legacy_page_info(self, video_data):
        return {
            **traverse_obj(video_data, ('videoMetadata', {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'timestamp': ('uploadDateMs', {float_or_none(scale=1000)}),
                'view_count': ('viewCount', {int_or_none}, {lambda x: None if x == -1 else x}),
                'repost_count': ('shareCount', {int_or_none}),
                'url': ('contentUrl', {url_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'duration': ('durationMs', {float_or_none(scale=1000)}),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
                'uploader': ('creator', 'personCreator', 'username', {str}),
                'uploader_url': ('creator', 'personCreator', 'url', {url_or_none}),
            })),
            **traverse_obj(video_data, {
                'description': ('description', {str}),
                'tags': ('hashtags', ..., {str}),
                'view_count': ('engagementStats', 'viewCount', {int_or_none}, {lambda x: None if x == -1 else x}),
                'repost_count': ('engagementStats', 'shareCount', {int_or_none}),
            }),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = traverse_obj(
            self._search_nextjs_data(webpage, video_id, default={}),
            ('props', 'pageProps', {dict})) or {}
        video_data = traverse_obj(page_props, (
            'spotlightFeed', 'spotlightStories',
            lambda _, v: v['story']['storyId']['value'] == video_id, 'metadata', any))
        if video_data:
            return {
                'id': video_id,
                'ext': 'mp4',
                **self._legacy_page_info(video_data),
            }

        video = traverse_obj(
            self._search_nextjs_v13_data(webpage, video_id, fatal=False), (
                ..., {dict}, 'video', {dict}, {
                    lambda v: v if (v.get('rawSnapId') or v.get('id')) == video_id else None,
                }, any))
        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        info = {
            **json_ld,
            **traverse_obj(video, {
                'url': ('videoUrl', {url_or_none}),
                'thumbnail': ('posterUrl', {url_or_none}),
                'timestamp': ('uploadTimestampMs', {float_or_none(scale=1000)}),
                'uploader': ('postingUsername', {str}),
                'view_count': ('viewCount', {int_or_none}, {lambda x: None if x in (-1, 0) else x}),
                'repost_count': ('shareCount', {int_or_none}),
            }),
            'id': video_id,
            'ext': 'mp4',
            'uploader_url': format_field(
                traverse_obj(video, ('postingUsername', {str})), None,
                'https://www.snapchat.com/@%s'),
        }
        if not info.get('url'):
            raise ExtractorError('Unable to extract Snapchat Spotlight video', expected=True)
        return info
