import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    js_to_json,
    merge_dicts,
    parse_count,
    parse_resolution,
    traverse_obj,
    url_or_none,
    urljoin,
)


class JavBangersIE(InfoExtractor):
    IE_DESC = 'javbangers.com'
    _VALID_URL = r'https?://(?:www\.)?javbangers\.com/(?:video|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.javbangers.com/video/2505/rabs-026-entertain-the-mother-in-law',
        'md5': 'b96eccbbe39e173b5e360129b74701dc',
        'info_dict': {
            'id': '2505',
            'ext': 'mp4',
            'title': 'RABS-026 Entertain The Mother-in-law',
            'description': 'RABS-026 Entertain The Mother-in-law',
            'thumbnail': r're:https?://jav\.cdntrex\.com/contents/videos_screenshots/.+\.jpg',
            'view_count': int,
            'age_limit': 18,
            'categories': ['Censored'],
            'uploader': 'LEGO',
        },
    }, {
        'url': 'https://www.javbangers.com/embed/2505',
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

        if not formats:
            if re.search(r'This video is a private video', webpage):
                self.raise_login_required('This video is private')
            if re.search(r'videos? no longer available', webpage, re.IGNORECASE):
                raise ExtractorError('Video is no longer available', expected=True)
            raise ExtractorError('Unable to extract video URL')

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

        view_count_str = self._html_search_regex(
            r'Views:\s*<em[^>]*>([^<]+)</em>', webpage, 'view count', default=None)
        if view_count_str:
            view_count_str = view_count_str.replace(' ', '')

        return merge_dicts(info, {
            'id': traverse_obj(flashvars, ('video_id', {str})) or video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': urljoin(url, traverse_obj(flashvars, ('preview_url', {url_or_none}))),
            'view_count': parse_count(view_count_str),
            'uploader': self._html_search_regex(
                r'<div class="username">\s*<a[^>]+>\s*([^<]+?)\s*</a>',
                webpage, 'uploader', default=None),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })
