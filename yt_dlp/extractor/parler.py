import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    strip_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class ParlerIE(InfoExtractor):
    IE_DESC = 'Posts on parler.com'
    _VALID_URL = [
        r'https?://(?:(?:www|app|play)\.)?parler\.com/(?:feed|post|watch|v|b)/(?P<id>[0-9A-Za-z]{26})',
        r'https?://(?:(?:www|app)\.)?parler\.com/feed/(?P<id>[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})',
    ]
    _TESTS = [
        {
            'url': 'https://app.parler.com/post/01k2jgdzymnfc8xp9qrfz9xcw7',
            'md5': 'd8dbae02bd7e17659ec201520cc681fd',
            'info_dict': {
                'id': '01k2jgdzymnfc8xp9qrfz9xcw7',
                'ext': 'mp4',
                'title': 'Parler Is Back! Big Tech Can’t Touch Us',
                'description': '',
                'thumbnail': r're:https://m\.cdnparler\.com/.+',
                'timestamp': 1755097356,
                'upload_date': '20250813',
                'uploader': 'Parler',
                'uploader_id': 'parler',
                'uploader_url': 'https://app.parler.com/parler',
                'duration': 33,
                'view_count': int,
                'comment_count': int,
                'repost_count': int,
                'tags': ['Parler', 'Play TV'],
            },
        },
        {
            'url': 'https://play.parler.com/watch/01k2jgdzymnfc8xp9qrfz9xcw7',
            'only_matching': True,
        },
        {
            'url': 'https://parler.com/feed/df79fdba-07cc-48fe-b085-3293897520d7',
            'skip': 'video gone',
            'md5': '16e0f447bf186bb3cf64de5bbbf4d22d',
            'info_dict': {
                'id': 'df79fdba-07cc-48fe-b085-3293897520d7',
                'ext': 'mp4',
                'thumbnail': 'https://bl-images.parler.com/videos/6ce7cdf3-a27a-4d72-bf9c-d3e17ce39a66/thumbnail.jpeg',
                'title': 'Parler video #df79fdba-07cc-48fe-b085-3293897520d7',
                'description': 'md5:6f220bde2df4a97cbb89ac11f1fd8197',
                'timestamp': 1659785481,
                'upload_date': '20220806',
                'uploader': 'Tulsi Gabbard',
                'uploader_id': 'TulsiGabbard',
                'uploader_url': 'https://parler.com/TulsiGabbard',
                'view_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        {
            'url': 'https://parler.com/feed/f23b85c1-6558-470f-b9ff-02c145f28da5',
            'skip': 'video gone',
            'md5': 'eaba1ff4a10fe281f5ce74e930ab2cb4',
            'info_dict': {
                'id': 'r5vkSaz8PxQ',
                'ext': 'mp4',
                'live_status': 'not_live',
                'comment_count': int,
                'duration': 1267,
                'like_count': int,
                'channel_follower_count': int,
                'channel_id': 'UCox6YeMSY1PQInbCtTaZj_w',
                'upload_date': '20220716',
                'thumbnail': 'https://i.ytimg.com/vi/r5vkSaz8PxQ/maxresdefault.jpg',
                'tags': 'count:17',
                'availability': 'public',
                'categories': ['Entertainment'],
                'playable_in_embed': True,
                'channel': 'Who Knows What! With Mahesh & Friends',
                'title': 'Tom MacDonald Names Reaction',
                'uploader': 'Who Knows What! With Mahesh & Friends',
                'uploader_id': '@maheshchookolingo',
                'age_limit': 0,
                'description': 'md5:33c21f0d35ae6dc2edf3007d6696baea',
                'channel_url': 'https://www.youtube.com/channel/UCox6YeMSY1PQInbCtTaZj_w',
                'view_count': int,
                'uploader_url': 'http://www.youtube.com/@maheshchookolingo',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = traverse_obj(self._download_json(
            'https://api.parler.com/public/v4/posts/map', video_id,
            data=json.dumps({'ulids': [video_id]}).encode(),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }), ('data', 0))
        if not data:
            raise ExtractorError('Unable to extract post', expected=True)
        if data.get('isDeleted'):
            raise ExtractorError('This post has been deleted', expected=True)

        embed_url = url_or_none(data.get('embedUrl') or data.get('link'))
        video_url = traverse_obj(data, ('videos', 0, 'url', {url_or_none}))
        hls_url = traverse_obj(data, ('videos', 0, 'thumbnail', 'm3u8_name', {url_or_none}))
        if not video_url and not hls_url:
            if embed_url:
                return self.url_result(embed_url)
            raise ExtractorError('This post has no video', expected=True)

        uploader_id = traverse_obj(data, 'username', ('user', 'username'), expected_type=str)
        info = {
            'id': video_id,
            'title': (strip_or_none(data.get('title'))
                      or strip_or_none(clean_html(data.get('body')))
                      or f'Parler video #{video_id}'),
            'url': video_url,
            'thumbnail': (
                traverse_obj(data, ('videos', 0, 'thumbnail', 'additionalResources',
                                    'large', 'url', {url_or_none}))
                or traverse_obj(data, ('videos', 0, 'thumbnail', 'url', {url_or_none}))),
            **traverse_obj(data, {
                'description': ('body', {clean_html}),
                'timestamp': ('createdAt', {unified_timestamp}),
                'uploader': ('name', {strip_or_none}),
                'duration': ('videos', 0, 'duration', {int_or_none}),
                'view_count': ('postEngagement', 'views', {int_or_none}),
                'comment_count': ('postEngagement', 'totalCommentCount', {int_or_none}),
                'repost_count': ('postEngagement', 'repostCount', {int_or_none}),
                'tags': ('tags', ..., 'name'),
            }),
            'uploader_id': uploader_id,
            'uploader_url': urljoin('https://app.parler.com/', uploader_id),
        }
        if not video_url and hls_url:
            info['formats'] = self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls')
            info.pop('url', None)
        return info
