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


class XFetishTubeIE(InfoExtractor):
    IE_DESC = 'x-fetish.tube'
    _VALID_URL = r'https?://(?:www\.)?x-fetish\.tube/(?:video|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://x-fetish.tube/video/549498/knottydevil-aka-knottydevil-11-30-2025-onlyfans-video-and-to-finish-off-the-month-here-is-a-hot-bed-tie-featuring-flexyfairyk-and-pixiebait/',
        'md5': '6e81dfade34aded8a871e2b48c39f650',
        'info_dict': {
            'id': '549498',
            'ext': 'mp4',
            'title': 'Knottydevil aka knottydevil - 11-30-2025 OnlyFans Video - and to finish off the month here is a hot bed tie featuring flexyfairyk and pixiebait',
            'description': 'md5:cf9da994f7be7917cc49a823bdf83c88',
            'thumbnail': r're:https?://x-fetish\.tube/contents/videos_screenshots/.+\.jpg',
            'duration': 1221,
            'timestamp': 1771880533,
            'upload_date': '20260223',
            'view_count': int,
            'like_count': int,
            'age_limit': 18,
            'categories': ['Onlyfans'],
            'tags': 'count:9',
            'cast': ['Knottydevil'],
        },
    }, {
        'url': 'https://x-fetish.tube/embed/549498',
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

        return merge_dicts({
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': urljoin(url, traverse_obj(flashvars, ('preview_url', {url_or_none}))),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        }, info)
