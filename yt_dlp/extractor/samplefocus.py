import re

from .common import InfoExtractor
from ..utils import (
    get_element_by_attribute,
    int_or_none,
    parse_iso8601,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class SampleFocusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?samplefocus\.com/samples/(?P<id>[^/?&#]+)'
    _TESTS = [{
        'url': 'https://samplefocus.com/samples/lil-peep-sad-emo-guitar',
        'md5': '48c8d62d60be467293912e0e619a5120',
        'info_dict': {
            'id': '40316',
            'display_id': 'lil-peep-sad-emo-guitar',
            'ext': 'mp3',
            'title': 'Lil Peep Sad Emo Guitar',
            'thumbnail': r're:^https?://.+\.png',
            'license': 'Standard Licensing',
            'uploader': 'CapsCtrl',
            'uploader_id': 'capsctrl',
            'like_count': int,
            'comment_count': int,
            'view_count': int,
            'duration': 31,
            'timestamp': 1592304245,
            'upload_date': '20200616',
            'categories': ['Samples', 'Guitar', 'Electric guitar'],
        },
    }, {
        'url': 'https://samplefocus.com/samples/dababy-style-bass-808',
        'only_matching': True,
    }, {
        'url': 'https://samplefocus.com/samples/young-chop-kick',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)

        data = self._search_json(
            r'<script[^>]+data-component-name=["\']SampleHero["\'][^>]*>',
            webpage, 'sample data', display_id, fatal=False)
        sample = traverse_obj(data, ('sample', {dict})) or {}
        json_ld = self._search_json_ld(
            webpage, display_id, expected_type='AudioObject', default={})

        sample_id = str_or_none(sample.get('id')) or self._search_regex(
            r'/samples/sample_files/(\d+)/', webpage, 'sample id')
        title = (
            traverse_obj(sample, ('name', {str}))
            or json_ld.get('title')
            or self._og_search_title(webpage, fatal=False)
            or self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title'))
        mp3_url = traverse_obj(sample, ('sample_mp3_url', {url_or_none})) or json_ld.get('url')
        if not mp3_url:
            self.raise_no_formats('Unable to extract mp3 URL', video_id=sample_id)

        comments = traverse_obj(data, ('comments', ..., {
            'author': ('commentor_user_name', {str}),
            'author_id': ('commentor_slug', {str}),
            'text': ('body', {str}),
        })) or []

        breadcrumb = get_element_by_attribute('typeof', 'BreadcrumbList', webpage)
        categories = []
        if breadcrumb:
            for _, name in re.findall(r'<span[^>]+property=(["\'])name\1[^>]*>([^<]+)', breadcrumb):
                categories.append(name)

        return {
            'id': sample_id,
            'title': title,
            'formats': [{
                'url': mp3_url,
                'ext': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
                'http_headers': {
                    'Referer': url,
                },
            }],
            'display_id': display_id,
            'thumbnail': (
                traverse_obj(sample, ('sample_waveform_url', {url_or_none}))
                or self._og_search_thumbnail(webpage)),
            'uploader': (
                traverse_obj(data, ('uploader', 'display_name', {str}))
                or traverse_obj(sample, ('user_display_name_truncated', {str}))
                or json_ld.get('uploader')),
            'license': self._html_search_regex(
                r'<a[^>]+href=(["\'])/license\1[^>]*>(?P<license>[^<]+)<',
                webpage, 'license', fatal=False, group='license'),
            'uploader_id': (
                traverse_obj(data, ('uploader', 'slug', {str}))
                or traverse_obj(sample, ('user_slug', {str}))),
            'like_count': traverse_obj(sample, ('favorites_count', {int_or_none})),
            'comment_count': len(comments),
            'view_count': traverse_obj(sample, ('plays_count', {int_or_none})),
            'duration': int_or_none(sample.get('approximate_duration')) or json_ld.get('duration'),
            'timestamp': parse_iso8601(sample.get('published_at')) or json_ld.get('timestamp'),
            'comments': comments,
            'categories': categories,
        }
