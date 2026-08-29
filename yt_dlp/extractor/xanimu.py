import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    traverse_obj,
    url_or_none,
)


class XanimuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xanimu\.com/(?P<id>[^/]+)/?'
    _TESTS = [{
        'url': 'https://xanimu.com/51944-the-princess-the-frog-hentai/',
        'md5': '0352aa14794a4cc1e88c30d55caae5bc',
        'info_dict': {
            'id': '51944-the-princess-the-frog-hentai',
            'ext': 'mp4',
            'title': 'The Princess + The Frog Hentai',
            'thumbnail': 'https://xanimu.com/storage/2020/09/the-princess-and-the-frog-hentai.jpg',
            'description': 'The internet is talking about The Princess + The Frog Hentai. See why under Disney, Hentai, anime on xanimu.com.',
            'duration': 207,
            'timestamp': 1604573420,
            'upload_date': '20201105',
            'age_limit': 18,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://xanimu.com/huge-expansion/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)
        json_ld = self._search_json_ld(webpage, video_id, default={})

        formats = []
        for format_id in ('videoHigh', 'videoLow'):
            format_url = self._search_json(
                rf'var\s+{re.escape(format_id)}\s*=', webpage, format_id,
                video_id, default=None, contains_pattern=r'[\'"]([^\'"]+)[\'"]')
            if format_url:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'quality': -2 if format_id.endswith('Low') else None,
                    'impersonate': True,
                })
        if not formats and url_or_none(json_ld.get('url')):
            formats.append({
                'url': json_ld['url'],
                'format_id': 'contentUrl',
                'impersonate': True,
            })

        return {
            'id': video_id,
            'formats': formats,
            'age_limit': 18,
            'title': json_ld.get('title') or self._html_extract_title(webpage),
            'description': json_ld.get('description') or self._html_search_meta(
                'description', webpage, default=None),
            'thumbnail': traverse_obj(json_ld, ('thumbnails', 0, 'url')) or self._html_search_meta(
                'thumbnailUrl', webpage, default=None),
            'duration': json_ld.get('duration') or float_or_none(self._search_regex(
                r'duration:\s*[\'"]([^\'"]+?)[\'"]', webpage, 'duration', default=None)),
            'timestamp': json_ld.get('timestamp'),
            'view_count': json_ld.get('view_count'),
            'like_count': json_ld.get('like_count'),
            'comment_count': json_ld.get('comment_count'),
        }
