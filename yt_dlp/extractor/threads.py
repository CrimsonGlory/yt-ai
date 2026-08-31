import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    format_field,
    int_or_none,
    parse_duration,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class ThreadsIE(InfoExtractor):
    IE_DESC = 'Threads (threads.net / threads.com)'
    _VALID_URL = r'https?://(?:www\.)?threads\.(?:net|com)/(?:(?:@[^/?#]+/)?post|t)/(?P<id>[^/?#]+)'
    _TESTS = [
        {
            'url': 'https://www.threads.com/@zuck/post/DHV7vTivqWD',
            'md5': '6f6c55c9e2755115c4a190ec6f6ed1b3',
            'info_dict': {
                'id': 'DHV7vTivqWD',
                'ext': 'mp4',
                'title': 'Me finding out Llama hit 1 BILLION downloads.',
                'description': 'Me finding out Llama hit 1 BILLION downloads.',
                'uploader': 'Mark Zuckerberg',
                'uploader_id': '63055343223',
                'uploader_url': 'https://www.threads.com/@zuck',
                'channel': 'zuck',
                'channel_url': 'https://www.threads.com/@zuck',
                'channel_is_verified': True,
                'timestamp': 1742305717,
                'upload_date': '20250318',
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
                'thumbnail': r're:https?://.+\.(?:jpg|webp)',
                'duration': 4.16071,
                'width': 400,
                'height': 300,
            },
        },
        {
            'url': 'https://www.threads.com/t/DHV7vTivqWD',
            'only_matching': True,
        },
        {
            'url': 'https://www.threads.net/@zuck/post/DHV7vTivqWD',
            'only_matching': True,
        },
        {
            'url': 'https://www.threads.net/t/DHV7vTivqWD',
            'only_matching': True,
        },
        {
            'url': 'https://www.threads.com/@zuck/post/DHV7vTivqWD/embed',
            'only_matching': True,
        },
    ]

    _SJS_RE = re.compile(r'<script\b[^>]*\bdata-sjs\b[^>]*>(\{.+?\})</script>', re.DOTALL)

    def _iter_dicts(self, obj):
        if isinstance(obj, dict):
            yield obj
            for value in obj.values():
                yield from self._iter_dicts(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from self._iter_dicts(value)

    def _extract_post(self, webpage, post_id):
        candidates = []
        for sjs in self._SJS_RE.findall(webpage):
            data = self._parse_json(sjs, post_id, fatal=False)
            if not data:
                continue
            for item in self._iter_dicts(data):
                if item.get('code') == post_id and isinstance(item.get('user'), dict):
                    candidates.append(item)
        return next(
            (
                post
                for post in candidates
                if post.get('video_versions') or post.get('video_dash_manifest') or post.get('carousel_media')
            ),
            traverse_obj(candidates, (0, {dict})),
        )

    def _extract_formats(self, media, video_id):
        formats = traverse_obj(
            media,
            (
                'video_versions',
                lambda _, v: url_or_none(v.get('url')),
                {
                    'url': ('url', {url_or_none}),
                    'format_id': (('id', {str}), ('type', {int}, {str_or_none}), any),
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                    'filesize': ('content_length', {int_or_none}),
                },
            ),
        ) or []
        width = int_or_none(media.get('original_width'))
        height = int_or_none(media.get('original_height'))
        acodec = 'none' if media.get('has_audio') is False else None
        vcodec = traverse_obj(media, ('video_codec', {str}))
        for fmt in formats:
            fmt['width'] = fmt.get('width') or width
            fmt['height'] = fmt.get('height') or height
            if acodec:
                fmt['acodec'] = acodec
            if vcodec:
                fmt['vcodec'] = vcodec

        dash = traverse_obj(media, ('video_dash_manifest', {str}))
        if dash:
            formats.extend(self._parse_mpd_formats(self._parse_xml(dash, video_id), mpd_id='dash'))
        return formats

    def _media_items(self, post):
        carousel = traverse_obj(post, ('carousel_media', ..., {dict}))
        if carousel:
            return carousel
        linked = traverse_obj(post, ('text_post_app_info', 'linked_inline_media', {dict}))
        if linked and not (post.get('video_versions') or post.get('video_dash_manifest')):
            return traverse_obj(linked, ('carousel_media', ..., {dict})) or [linked]
        return [post]

    def _real_extract(self, url):
        post_id = self._match_id(url)
        webpage = self._download_webpage(url, post_id, impersonate=True)
        post = self._extract_post(webpage, post_id)
        if not post:
            if post_id in webpage:
                raise ExtractorError('Unable to extract Threads post data')
            self.raise_login_required('This Threads post is private, deleted, or requires a logged-in account')

        username = traverse_obj(post, ('user', 'username', {str}))
        caption = traverse_obj(post, ('caption', 'text', {str}))
        common = {
            'title': caption or format_field(username, None, 'Video by %s') or f'Threads video #{post_id}',
            'description': caption,
            **traverse_obj(
                post,
                {
                    'uploader': ('user', 'full_name', {str}),
                    'uploader_id': ('user', 'pk', {str_or_none}),
                    'channel': ('user', 'username', {str}),
                    'channel_is_verified': ('user', 'is_verified', {bool}),
                    'timestamp': ('taken_at', {int_or_none}),
                    'like_count': ('like_count', {int_or_none}),
                    'comment_count': ('text_post_app_info', 'direct_reply_count', {int_or_none}),
                    'repost_count': ('text_post_app_info', 'repost_count', {int_or_none}),
                    'view_count': ('text_post_app_info', 'impression_count', {int_or_none}),
                },
            ),
            'uploader_url': format_field(username, None, 'https://www.threads.com/@%s'),
            'channel_url': format_field(username, None, 'https://www.threads.com/@%s'),
            'http_headers': {'Referer': 'https://www.threads.com/'},
        }

        entries = []
        media_list = self._media_items(post)
        for idx, media in enumerate(media_list, 1):
            formats = self._extract_formats(media, post_id)
            if not formats:
                continue
            duration = float_or_none(media.get('video_duration')) or parse_duration(
                self._search_regex(
                    r'mediaPresentationDuration="([^"]+)"',
                    media.get('video_dash_manifest') or '',
                    'duration',
                    default=None,
                ),
            )
            entries.append({
                **common,
                'id': post_id if len(media_list) == 1 else (
                    traverse_obj(media, ('code', {str})) or f'{post_id}_{idx}'),
                'formats': formats,
                'duration': duration,
                'width': int_or_none(media.get('original_width')),
                'height': int_or_none(media.get('original_height')),
                'thumbnails': list(reversed(traverse_obj(media, (
                    'image_versions2', 'candidates',
                    lambda _, v: url_or_none(v.get('url')), {
                        'url': 'url',
                        'width': ('width', {int_or_none}),
                        'height': ('height', {int_or_none}),
                    },
                )) or [])),
            })

        if not entries:
            self.raise_no_formats('There is no video in this post', expected=True, video_id=post_id)

        if len(entries) == 1:
            return {**entries[0], 'id': post_id}

        return self.playlist_result(entries, post_id, **common)
