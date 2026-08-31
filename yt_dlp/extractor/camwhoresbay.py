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


class CamwhoresbayIE(InfoExtractor):
    IE_DESC = 'camwhoresbay.com'
    _VALID_URL = r'https?://(?:www\.)?camwhoresbay\.com/(?:videos|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.camwhoresbay.com/videos/756896/blonde-fingering-hard-till-she-cums3/',
        'md5': 'fc152c285e39733684331e028159155b',
        'info_dict': {
            'id': '756896',
            'ext': 'mp4',
            'title': 'Blonde Fingering Hard till she Cums',
            'description': 'Awesome finger fucking masturbating show from this amateur blonde legs widely spread where you can see her tight pussy getting wet upclose to her cam She then spreads her legs wide and begin to rub an',
            'thumbnail': r're:https?://cwb\.cdntrex\.com/contents/videos_screenshots/.+\.jpg',
            'duration': 624,
            'view_count': int,
            'age_limit': 18,
            'categories': ['Amateur', 'Blonde', 'Fingering'],
            'tags': 'count:47',
            'uploader': 'ladysofie',
        },
    }, {
        'url': 'https://www.camwhoresbay.com/embed/756896',
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
                r'Duration:\s*<em[^>]*>([^<]+)</em>', webpage, 'duration', default=None)),
            'view_count': parse_count(self._html_search_regex(
                r'Views:\s*<em[^>]*>([^<]+)</em>', webpage, 'view count', default=None)),
            'uploader': self._html_search_regex(
                r'<div class="username">\s*<a[^>]+>\s*([^<]+?)\s*</a>',
                webpage, 'uploader', default=None),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })
