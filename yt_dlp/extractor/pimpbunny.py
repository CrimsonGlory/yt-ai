import re

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    merge_dicts,
    parse_resolution,
    traverse_obj,
    url_or_none,
    urljoin,
)


class PimpBunnyIE(InfoExtractor):
    IE_DESC = 'pimpbunny.com'
    _VALID_URL = r'https?://(?:www\.)?pimpbunny\.com/(?:[a-z]{2}/)?(?:videos|embed)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://pimpbunny.com/videos/outdoor-teasing-with-helayna-marie/',
        'md5': '1569d5fa269066564d7d45088b2ed4f4',
        'info_dict': {
            'id': '467113',
            'ext': 'mp4',
            'title': 'Outdoor Teasing With Helayna Marie',
            'description': 'Outdoor Teasing With Helayna Marie',
            'thumbnail': r're:https?://pimpbunny\.com/contents/videos_screenshots/.+\.jpg',
            'duration': 532,
            'timestamp': 1762819200,
            'upload_date': '20251111',
            'view_count': int,
            'like_count': int,
            'age_limit': 18,
            'categories': ['Outdoor', 'Big Boobs', 'Seduction', 'Big Ass'],
            'tags': 'count:15',
            'cast': ['Helayna Marie'],
        },
    }, {
        'url': 'https://pimpbunny.com/embed/467113',
        'only_matching': True,
    }, {
        'url': 'https://pimpbunny.com/es/videos/outdoor-teasing-with-helayna-marie/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        from .generic import GenericIE

        flashvars = self._search_json(
            r'var\s+\w+\s*=', webpage, 'player config', display_id,
            contains_pattern=r'\{[^{}]*video_url[^{}]*\}',
            transform_source=js_to_json, default={})
        if not flashvars.get('video_url'):
            flashvars = dict(re.findall(
                r'(video(?:_alt)?_url(?:\d*)?(?:_text)?|license_code|video_title|video_id|preview_url|video_categories|video_tags|video_models)\s*:\s*\'([^\']+)\'',
                webpage))

        formats = []
        for key in filter(re.compile(r'^video_(?:url|alt_url\d*)$').match, flashvars):
            video_url = url_or_none(urljoin(url, flashvars[key]))
            if not video_url or '/get_file/' not in video_url:
                continue
            format_id = flashvars.get(f'{key}_text', key)
            formats.append({
                'url': GenericIE._kvs_get_real_url(
                    video_url, flashvars.get('license_code')),
                'format_id': format_id,
                'ext': 'mp4',
                **(parse_resolution(format_id) or parse_resolution(video_url) or {}),
                'http_headers': {'Referer': url},
            })

        info = self._search_json_ld(
            webpage, display_id, expected_type='VideoObject', default={})
        info.pop('url', None)
        info.pop('ext', None)

        def split_csv(value):
            if not value:
                return None
            return [item.strip() for item in value.split(',') if item.strip()] or None

        video_id = traverse_obj(flashvars, ('video_id', {str})) or display_id
        title = (
            traverse_obj(flashvars, ('video_title', {str}))
            or info.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage))

        return merge_dicts(info, {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': urljoin(url, traverse_obj(flashvars, ('preview_url', {url_or_none}))),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })
