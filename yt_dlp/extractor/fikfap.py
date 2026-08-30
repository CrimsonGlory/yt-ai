import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class FikFapBaseIE(InfoExtractor):
    _API_BASE = 'https://api.fikfap.com'
    _MEDIA_HEADERS = {
        'Origin': 'https://fikfap.com',
        'Referer': 'https://fikfap.com/',
    }

    def _real_initialize(self):
        self._anon_token = str(uuid.uuid4())

    def _api_headers(self):
        return {
            'Accept': 'application/json',
            'Authorization-Anonymous': self._anon_token,
            'X-Client-Logged-In': 'false',
            'X-Client-Type': 'browser',
            **self._MEDIA_HEADERS,
        }

    def _call_api(self, path, video_id, note='Downloading JSON metadata', query=None, fatal=True):
        return self._download_json(
            f'{self._API_BASE}/{path}', video_id, note,
            fatal=fatal, headers=self._api_headers(), query=query)


class FikFapIE(FikFapBaseIE):
    IE_NAME = 'fikfap'
    IE_DESC = 'FikFap'
    _VALID_URL = r'https?://(?:www\.)?fikfap\.com/(?:user/[^/?#]+|hash/[^/?#]+)/post/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://fikfap.com/user/alinevs/post/1429486',
        'md5': '01dfaaa8c04f809b02669e6494fdd5b6',
        'info_dict': {
            'id': '1429486',
            'ext': 'mp4',
            'title': '⬇️check my FREE VIP OF ⬇️',
            'age_limit': 18,
            'thumbnail': r're:https://vz-.+\.b-cdn\.net/.+',
            'timestamp': 1761007837,
            'upload_date': '20251021',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'uploader': 'alinevs',
            'uploader_id': '32f4c8d6-2409-4db8-9e66-d3b5ff0c1a98',
            'uploader_url': 'https://fikfap.com/user/alinevs',
            'channel': 'alinevs',
            'channel_id': '32f4c8d6-2409-4db8-9e66-d3b5ff0c1a98',
            'channel_url': 'https://fikfap.com/user/alinevs',
            'tags': ['lesbian'],
        },
        # CMAF HLS --test only fetches the fMP4 init fragment (~1KB)
        'params': {'format': 'bv'},
        'file_minsize': None,
    }, {
        'url': 'https://fikfap.com/hash/lesbian/post/1429486',
        'only_matching': True,
    }, {
        'url': 'https://www.fikfap.com/user/alinevs/post/1429486',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        post = self._call_api(f'posts/{video_id}', video_id)

        if traverse_obj(post, 'deletedAt'):
            raise ExtractorError('This post has been deleted', expected=True)

        formats, subtitles = [], {}
        stream_url = traverse_obj(post, ('videoStreamUrl', {url_or_none}))
        if stream_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id='hls', headers=self._MEDIA_HEADERS)

        original_url = traverse_obj(post, ('videoFileOriginalUrl', {url_or_none}))
        if original_url:
            formats.append({
                'url': original_url,
                'format_id': 'original',
                'ext': determine_ext(original_url, 'mp4'),
                'quality': 1,
                'http_headers': self._MEDIA_HEADERS,
            })

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        for f in formats:
            f.setdefault('http_headers', {}).update(self._MEDIA_HEADERS)

        username = traverse_obj(post, ('author', 'username', {str}))
        uploader_id = traverse_obj(post, ('author', 'userId', {str_or_none}))
        uploader_url = f'https://fikfap.com/user/{username}' if username else None

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 18,
            'http_headers': self._MEDIA_HEADERS,
            **traverse_obj(post, {
                'title': ('label', {str}),
                'thumbnail': ('thumbnailStreamUrl', {url_or_none}),
                'duration': ('duration', {int_or_none}),
                'timestamp': (('publishedAt', 'createdAt'), {parse_iso8601}, any),
                'view_count': ('viewsCount', {int_or_none}),
                'like_count': ('likesCount', {int_or_none}),
                'comment_count': ('commentsCount', {int_or_none}),
                'tags': ('hashtags', ..., 'label', {str}),
            }),
            'uploader': username,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'channel': username,
            'channel_id': uploader_id,
            'channel_url': uploader_url,
        }


class FikFapUserIE(FikFapBaseIE):
    IE_NAME = 'fikfap:user'
    IE_DESC = 'FikFap user'
    _VALID_URL = r'https?://(?:www\.)?fikfap\.com/user/(?P<id>[^/?#]+)(?:/overview)?/?(?:[?#]|$)'
    _PAGE_SIZE = 21
    _TESTS = [{
        'url': 'https://fikfap.com/user/alinevs',
        'info_dict': {
            'id': 'alinevs',
            'title': 'alinevs',
            'description': str,
        },
        'playlist_mincount': 5,
        'params': {
            'extract_flat': True,
            'playlistend': 5,
            'skip_download': True,
        },
    }, {
        'url': 'https://fikfap.com/user/alinevs/overview',
        'only_matching': True,
    }, {
        'url': 'https://www.fikfap.com/user/alinevs/',
        'only_matching': True,
    }]

    def _entries(self, username):
        after_id, seen, page = None, set(), 1
        while True:
            query = {'amount': str(self._PAGE_SIZE)}
            if after_id:
                query['afterId'] = after_id
            posts = self._call_api(
                f'profile/username/{username}/posts', username,
                f'Downloading posts page {page}', query=query)
            if not isinstance(posts, list) or not posts:
                break

            new_count = 0
            for post in posts:
                post_id = traverse_obj(post, ('postId', {str_or_none}))
                if not post_id or post_id in seen:
                    continue
                seen.add(post_id)
                new_count += 1
                author = traverse_obj(post, ('author', 'username', {str})) or username
                yield self.url_result(
                    f'https://fikfap.com/user/{author}/post/{post_id}',
                    ie=FikFapIE, video_id=post_id)
                after_id = post_id

            if new_count == 0 or len(posts) < self._PAGE_SIZE:
                break
            page += 1

    def _real_extract(self, url):
        username = self._match_id(url)
        profile = self._call_api(
            f'profile/username/{username}', username,
            'Downloading user profile', fatal=False) or {}
        return self.playlist_result(
            self._entries(username), username,
            traverse_obj(profile, ('username', {str})) or username,
            traverse_obj(profile, ('description', {str})))
