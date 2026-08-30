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


class GayhausIE(InfoExtractor):
    IE_DESC = 'gayhaus.com'
    _VALID_URL = r'https?://(?:www\.)?gayhaus\.com/(?:videos|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://gayhaus.com/videos/14909/track-meet/',
        'md5': '2990e5678ee1ecf86252746c15bdfd0c',
        'info_dict': {
            'id': '14909',
            'ext': 'mp4',
            'title': 'Track Meet',
            'description': 'Watch Track Meet — free gay porn video on gayhaus.com. Stream HD gay tube scenes updated daily.',
            'thumbnail': r're:https?://gayhaus\.com/contents/videos_screenshots/.+\.jpg',
            'duration': 3834,
            'timestamp': 1739461038,
            'upload_date': '20250213',
            'view_count': int,
            'like_count': int,
            'age_limit': 18,
            'categories': ['Anal', 'Bareback', 'Big Cock', 'Blowjob', 'Daddy', 'Gay', 'Hunk', 'Old And Young (18+)', 'Vintage'],
            'tags': ['anal', 'blowjob', 'bareback', 'hunks', 'big-cock', 'daddy', 'old-young', 'vintage'],
        },
    }, {
        'url': 'https://gayhaus.com/embed/14909',
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
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })
