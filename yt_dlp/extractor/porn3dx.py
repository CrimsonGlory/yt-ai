import re

from .bunnycdn import BunnyCdnIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    smuggle_url,
    str_or_none,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class Porn3dxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?porn3dx\.com/post/(?P<id>\d+)(?:/[^/?#]+)?'
    _BUNNY_LIBRARY_ID = '21030'
    _TESTS = [{
        'url': 'https://porn3dx.com/post/90233/sexy-booty-dance-by-my-girl',
        'md5': 'f1470687a3aeaf6a6c941dd847ac22c8',
        'info_dict': {
            'id': '05473580-c8f8-46c5-a323-b80ed1945f23',
            'ext': 'mp4',
            'display_id': '90233',
            'title': 'Sexy Booty dance by my girl',
            'description': 'md5:3ea6b1dddd50311231f49354a88ae2c6',
            'thumbnail': r're:https?://vz-[\w-]+\.b-cdn\.net/05473580-c8f8-46c5-a323-b80ed1945f23/thumbnail\.jpg',
            'duration': 159,
            'timestamp': 1788235771,
            'upload_date': '20260901',
            'uploader': 'Ztulian',
            'uploader_id': '209987',
            'uploader_url': 'https://porn3dx.com/Ztulian',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'tags': ['Virtamate', 'Vam', 'Ztulian', 'Lap Dance', 'Natural Tits', 'Vex'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://porn3dx.com/post/90233',
        'only_matching': True,
    }, {
        'url': 'https://www.porn3dx.com/post/90227/202607260809-21-tfworkout-4k-classic-wsmp4',
        'only_matching': True,
    }]

    def _parse_post(self, webpage, video_id):
        for raw in re.findall(r'\bwire:initial-data="([^"]+)"', webpage):
            post = traverse_obj(
                self._parse_json(unescapeHTML(raw), video_id, fatal=False),
                ('serverMemo', 'data', 'post', {dict}))
            if str(traverse_obj(post, 'id')) == video_id:
                return post
        return {}

    def _bunny_videos(self, post):
        videos = traverse_obj(post, (
            'media', lambda _, v: (
                v.get('type') == 'bunny' and not v.get('is_bunny_image')
                and v.get('bunny_guid'))))
        if videos:
            return videos
        main = traverse_obj(post, ('media_main', {dict}))
        if (main and main.get('type') == 'bunny'
                and not main.get('is_bunny_image') and main.get('bunny_guid')):
            return [main]
        return []

    def _bunny_result(self, url, media, info):
        guid = media['bunny_guid']
        library_id = traverse_obj(media, ('bunny_library_id', {str})) or self._BUNNY_LIBRARY_ID
        return self.url_result(
            smuggle_url(
                f'https://iframe.mediadelivery.net/embed/{library_id}/{guid}',
                {'Referer': url}),
            ie=BunnyCdnIE, url_transparent=True,
            **info,
            **traverse_obj(media, {
                'thumbnail': (('thumbnail_url_complete', 'thumbnail_url'), {url_or_none}, any),
                'duration': ('duration_in_second', {int_or_none}),
            }))

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        post = self._parse_post(webpage, video_id)

        info = {
            'display_id': video_id,
            'age_limit': 18,
            **traverse_obj(post, {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'view_count': ('view_count', {int_or_none}),
                'like_count': ('like_count', {int_or_none}),
                'comment_count': ('comment_count', {int_or_none}),
                'timestamp': ('published_at', {parse_iso8601}),
                'uploader': ('creator', 'username', {str}),
                'uploader_id': ('creator', 'id', {str_or_none}),
                'uploader_url': ('creator', 'url', {url_or_none}),
                'tags': ('tags', ..., 'name', {str}),
            }),
        }
        if not info.get('title'):
            info['title'] = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage)

        entries = [
            self._bunny_result(url, media, info)
            for media in self._bunny_videos(post)
        ]
        if not entries:
            entries = [
                self.url_result(embed_url, ie=BunnyCdnIE, url_transparent=True, **info)
                for embed_url in BunnyCdnIE._extract_embed_urls(url, webpage)
            ]
        if not entries:
            raise ExtractorError('No video found in this post', expected=True)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, video_id, info.get('title'), info.get('description'),
            age_limit=18)
