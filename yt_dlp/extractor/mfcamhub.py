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


class MfcamhubIE(InfoExtractor):
    IE_DESC = 'mfcamhub.com'
    _VALID_URL = r'https?://(?:www\.)?mfcamhub\.com/(?:videos|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://mfcamhub.com/videos/229323/lucyxxcute-camgirl-porn-video-chaturbate-lovensecontrol-latinas-blow-fuckpussy/',
        'md5': 'deda5e4156b23e8d0a7a882a9688da6f',
        'info_dict': {
            'id': '229323',
            'ext': 'mp4',
            'title': 'lucyxxcute Camgirl Porn Video [Chaturbate] - lovensecontrol, latinas, blow, fuckpussy',
            'description': 'lucyxxcute fresh porn record. New lucyxxcute Chaturbate porn - hotgirl, ass, nora, wifematerial, feel. Latest lucyxxcute sex videos',
            'thumbnail': r're:https?://mfcamhub\.com/contents/videos_screenshots/.+\.jpg',
            'duration': 603,
            'timestamp': 1774396800,
            'upload_date': '20260325',
            'view_count': int,
            'like_count': int,
            'age_limit': 18,
            'categories': ['Chaturbate3'],
            'tags': ['shavedpussy', 'sissyfication', 'masturbation', 'master', 'feel', 'gaming', 'nonnude'],
        },
    }, {
        'url': 'https://mfcamhub.com/embed/229323',
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
