import base64
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    get_element_by_class,
    int_or_none,
    parse_age_limit,
    parse_iso8601,
    parse_resolution,
    remove_end,
    str_to_int,
    traverse_obj,
    try_call,
    url_or_none,
)


class MoverUzIE(InfoExtractor):
    IE_DESC = 'Mover.uz'
    _VALID_URL = r'https?://(?:www\.)?mover\.uz/(?:watch|video/embed)/(?P<id>(?!count(?:/|$))[A-Za-z0-9]+)'
    _TESTS = [{
        'url': 'https://mover.uz/watch/cMSqJpZm',
        'md5': 'a0b50df896154eda275a37219c214fd4',
        'info_dict': {
            'id': 'cMSqJpZm',
            'ext': 'mp4',
            'title': '16.38 A Fool Moon Night 98.51% 4824x combo – osu! mania',
            'description': 'md5:01433827251ca51c532d44be738062db',
            'thumbnail': r're:https://i\.mover\.uz/cMSqJpZm_h2\.jpg',
            'duration': 273,
            'timestamp': 1522007902,
            'upload_date': '20180325',
            'uploader': 'Alec76',
            'uploader_id': 'Alec76',
            'uploader_url': 'https://mover.uz/channel/Alec76',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'age_limit': 7,
            'categories': ['Игры'],
        },
    }, {
        'url': 'https://mover.uz/video/embed/cMSqJpZm',
        'only_matching': True,
    }, {
        'url': 'https://www.mover.uz/watch/cMSqJpZm',
        'only_matching': True,
    }]

    def _parse_playerjs_config(self, webpage, video_id):
        encoded = self._search_regex(
            r'(?:data-config=|new\s+Playerjs\()(["\'])(?P<config>#2[A-Za-z0-9+/=]+)\1',
            webpage, 'player config', default=None, group='config')
        if not encoded:
            return {}
        payload = encoded[2:]
        for candidate in (payload, re.sub(r'//.{32}', '', payload)):
            padded = candidate + '=' * (-len(candidate) % 4)
            decoded = try_call(lambda: base64.b64decode(padded).decode())
            config = self._parse_json(decoded, video_id, fatal=False) if decoded else None
            if isinstance(config, dict):
                return config
        return {}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        config = self._parse_playerjs_config(webpage, video_id)
        if not traverse_obj(config, ('file', {str})):
            embed = self._download_webpage(
                f'https://mover.uz/video/embed/{video_id}', video_id,
                'Downloading embed webpage', fatal=False)
            if embed:
                config = self._parse_playerjs_config(embed, video_id) or config

        formats = []
        for format_id, video_url in re.findall(
                r'(?:\[([^\]]+)\])?(https?://[^,\s]+)',
                traverse_obj(config, ('file', {str})) or ''):
            formats.append({
                'url': video_url,
                'format_id': format_id or None,
                'ext': 'mp4',
                **parse_resolution(format_id),
            })
        if not formats:
            self.raise_no_formats('No video formats found', expected=False, video_id=video_id)

        uploader_id = self._search_regex(
            r'href="https?://(?:www\.)?mover\.uz/channel/([^"]+)"',
            webpage, 'uploader id', default=None)
        category = self._html_search_regex(
            r'class="category clamped"[^>]*>\s*<a[^>]*>([^<]+)',
            webpage, 'category', default=None)

        return {
            'id': video_id,
            'title': (
                traverse_obj(config, ('title', {str}))
                or self._og_search_title(webpage, default=None)
                or remove_end(self._html_extract_title(webpage, default=None), ' - Mover.uz')),
            'description': (
                clean_html(get_element_by_class('video-description', webpage))
                or self._og_search_description(webpage, default=None)),
            'thumbnail': (
                traverse_obj(config, ('poster', {url_or_none}))
                or self._og_search_thumbnail(webpage, default=None)),
            'duration': traverse_obj(config, ('duration', {int_or_none})),
            'timestamp': parse_iso8601(self._html_search_meta(
                ['uploadDate', 'datePublished', 'dateCreated'], webpage, default=None)),
            'uploader': self._html_search_regex(
                r'itemprop="director"[^>]*>.*?itemprop="name"[^>]*>([^<]+)',
                webpage, 'uploader', default=None, flags=re.DOTALL),
            'uploader_id': uploader_id,
            'uploader_url': f'https://mover.uz/channel/{uploader_id}' if uploader_id else None,
            'view_count': str_to_int(self._search_regex(
                r'class="views clamped"[^>]*>([^<]+)', webpage, 'view count', default=None)),
            'like_count': str_to_int(self._search_regex(
                r'btn-video-vote-up[^>]*>([^<]+)', webpage, 'like count', default=None)),
            'dislike_count': str_to_int(self._search_regex(
                r'btn-video-vote-down[^>]*>([^<]+)', webpage, 'dislike count', default=None)),
            'age_limit': parse_age_limit(self._search_regex(
                r'data-age-limit="([^"]+)"', webpage, 'age limit', default=None)),
            'categories': [category] if category else None,
            'formats': formats,
        }
