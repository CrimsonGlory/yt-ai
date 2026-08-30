import re

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    merge_dicts,
    parse_count,
    parse_duration,
    parse_resolution,
    traverse_obj,
    url_or_none,
    urljoin,
)


class ThothubIE(InfoExtractor):
    IE_DESC = 'thothub.to'
    _VALID_URL = r'https?://(?:www\.)?thothub\.to/(?:videos|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://thothub.to/videos/985503/mira004-tiktok-1/',
        'md5': 'f3acbd5195a6014b35eb9d721adfdd3b',
        'info_dict': {
            'id': '985503',
            'ext': 'mp4',
            'title': 'Mira004 tiktok (1)',
            'description': 'Mira tiktok thighs',
            'thumbnail': r're:https?://thothub\.to/contents/videos_screenshots/.+\.jpg',
            'duration': 7,
            'view_count': int,
            'age_limit': 18,
            'categories': ['Twitch', 'Instagram'],
            'tags': ['mira004', 'muira', 'thighs', 'gym girl', 'tiktok', '1', 'mira'],
            'uploader': 'supersperm15',
        },
    }, {
        'url': 'https://thothub.to/embed/985503',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        from .generic import GenericIE

        flashvars = self._search_json(
            r'var\s+\w+\s*=', webpage, 'player config', video_id,
            contains_pattern=r'\{[^{}]*video_url[^{}]*\}',
            transform_source=js_to_json, default={})
        if not flashvars.get('video_url'):
            flashvars = dict(re.findall(
                r'(video(?:_alt)?_url(?:\d*)?(?:_text)?|license_code|video_title|video_id|preview_url|video_categories|video_tags|video_models)\s*:\s*\'([^\']+)\'',
                webpage))

        formats = []
        for key in filter(re.compile(r'^video_(?:url|alt_url\d*)$').match, flashvars):
            video_url = flashvars[key]
            if not video_url or '/get_file/' not in video_url:
                continue
            format_id = flashvars.get(f'{key}_text', key)
            formats.append({
                'url': urljoin(url, GenericIE._kvs_get_real_url(
                    video_url, flashvars.get('license_code'))),
                'format_id': format_id,
                'ext': 'mp4',
                **(parse_resolution(format_id) or parse_resolution(video_url) or {}),
                'http_headers': {'Referer': url},
            })

        if not formats and re.search(r'This video is a private video', webpage):
            self.raise_login_required('This video is private', method='password')

        info = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        info.pop('url', None)
        info.pop('ext', None)

        def split_csv(value):
            if not value:
                return None
            return [item.strip() for item in value.split(',') if item.strip()] or None

        title = (
            traverse_obj(flashvars, ('video_title', {str}))
            or info.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage))

        return merge_dicts(info, {
            'id': traverse_obj(flashvars, ('video_id', {str})) or video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': urljoin(url, traverse_obj(flashvars, ('preview_url', {url_or_none}))),
            'duration': parse_duration(self._html_search_regex(
                r'Duration:\s*<em>([^<]+)</em>', webpage, 'duration', default=None)),
            'view_count': parse_count(self._html_search_regex(
                r'Views:\s*<em>([^<]+)</em>', webpage, 'view count', default=None)),
            'uploader': self._html_search_regex(
                r'<div class="username">\s*<a[^>]+>\s*([^<]+?)\s*</a>',
                webpage, 'uploader', default=None),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })
