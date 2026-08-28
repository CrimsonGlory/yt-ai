import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
    merge_dicts,
    parse_resolution,
    qualities,
    remove_end,
    urljoin,
)


class SunPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|embeds\.)?sunporno\.com/(?:videos|v|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.sunporno.com/v/3159/horny-egyptian-fucker-drills-cock-hungry-whore-hard-and-fast/',
        'md5': 'b4495fefc8150f24164b43714d70f6c3',
        'info_dict': {
            'id': '3159',
            'ext': 'mp4',
            'title': 'Horny Egyptian fucker drills cock hungry whore hard and fast',
            'description': 'Horny Egyptian fucker drills cock hungry whore hard and fast. Video duration: 26 minutes 42 seconds.',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg|png)',
            'duration': 1602,
            'timestamp': 1720629217,
            'upload_date': '20240710',
            'age_limit': 18,
            'tags': ['horny', 'cock', 'homemade', 'sexy', 'blowjob', 'missionary', 'fuck'],
        },
    }, {
        'url': 'http://www.sunporno.com/videos/807778/',
        'md5': '507887e29033502f29dba69affeebfc9',
        'info_dict': {
            'id': '807778',
            'ext': 'mp4',
            'title': 'md5:0a400058e8105d39e35c35e7c5184164',
            'description': 'md5:a31241990e1bd3a64e72ae99afb325fb',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 302,
            'age_limit': 18,
        },
        'skip': 'video gone',
    }, {
        'url': 'http://embeds.sunporno.com/embed/807778',
        'only_matching': True,
    }, {
        'url': 'https://www.sunporno.com/embed/3159',
        'only_matching': True,
    }]

    def _extract_kvs_formats(self, url, webpage, video_id):
        from .generic import GenericIE

        flashvars = self._search_json(
            r'var\s+flashvars\s*=', webpage, 'flashvars', video_id,
            transform_source=js_to_json, default={})
        if not flashvars:
            flashvars = dict(re.findall(
                r'(video(?:_alt)?_url(?:\d*)?(?:_text)?|license_code|video_title)\s*:\s*\'([^\']+)\'',
                webpage))

        formats = []
        for key in filter(re.compile(r'^video_(?:url|alt_url\d*)$').match, flashvars):
            video_url = flashvars[key]
            if '/get_file/' not in video_url:
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
        return formats, flashvars

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if 'embeds.sunporno.com' in url:
            url = f'https://www.sunporno.com/embed/{video_id}'

        webpage = self._download_webpage(url, video_id)
        formats, flashvars = self._extract_kvs_formats(url, webpage, video_id)
        if not formats:
            embed_url = f'https://www.sunporno.com/embed/{video_id}'
            if url.rstrip('/') != embed_url:
                webpage = self._download_webpage(
                    embed_url, video_id, note='Downloading embed webpage')
                formats, flashvars = self._extract_kvs_formats(
                    embed_url, webpage, video_id)
                url = embed_url

        if not formats:
            quality = qualities(['mp4', 'flv'])
            for video_url in re.findall(r'<(?:source|video) src="([^"]+)"', webpage):
                video_ext = determine_ext(video_url)
                formats.append({
                    'url': video_url,
                    'format_id': video_ext,
                    'quality': quality(video_ext),
                })

        info = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        info.pop('url', None)
        info.pop('ext', None)
        if info.get('tags'):
            info['tags'] = [t.strip() for t in info['tags'] if t.strip()]

        title = (
            flashvars.get('video_title')
            or info.get('title')
            or self._og_search_title(webpage, default=None)
            or remove_end(self._html_extract_title(webpage), ' - SunPorno.com'))

        return merge_dicts(info, {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18,
        })
