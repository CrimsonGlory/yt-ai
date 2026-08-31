from .common import InfoExtractor
from ..utils import (
    clean_html,
    get_element_by_id,
    get_element_html_by_class,
    parse_count,
    parse_duration,
    unified_strdate,
    urljoin,
)


class MGTOWTVIE(InfoExtractor):
    IE_NAME = 'mgtow.tv'
    IE_DESC = 'MGTOW TV'
    _VALID_URL = r'https?://(?:www\.)?mgtow\.tv/(?:watch/(?:[^/?#]*_)?|embed/|v/)(?P<id>[\w-]+)(?:\.html)?'
    _TESTS = [{
        'url': 'https://www.mgtow.tv/watch/inA4r3ODfbwlaZl',
        'md5': '2a0d0f4ee13e5a3cb5d5feb943849cb4',
        'info_dict': {
            'id': 'inA4r3ODfbwlaZl',
            'ext': 'mp4',
            'title': 'Women Using Barbie to Filter Themselves out of the Dating Pool!',
            'description': 'md5:d3c65b157356728c49b309bbf558a5eb',
            'thumbnail': r're:https?://cdn\.mgtow\.tv/.+\.jpeg',
            'duration': 604,
            'upload_date': '20230802',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'uploader': 'Raging Golden Eagle',
            'uploader_id': 'ManospherePodcast',
            'uploader_url': 'https://www.mgtow.tv/@ManospherePodcast',
            'channel': 'Raging Golden Eagle',
            'channel_id': 'ManospherePodcast',
            'channel_url': 'https://www.mgtow.tv/@ManospherePodcast',
            'categories': ['Film & Animation'],
        },
    }, {
        'url': 'https://www.mgtow.tv/watch/women-using-barbie-to-filter-themselves-out-of-the-dating-pool_inA4r3ODfbwlaZl.html',
        'only_matching': True,
    }, {
        'url': 'https://www.mgtow.tv/embed/inA4r3ODfbwlaZl',
        'only_matching': True,
    }, {
        'url': 'https://www.mgtow.tv/v/Gi9WnS',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'(?:https?:)?//(?:www\.)?mgtow\.tv/embed/([\w-]+)',
            webpage, 'video id', default=display_id)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        if not entries or not (entries[0].get('formats') or entries[0].get('url')):
            self.raise_no_formats('No video source found', expected=True, video_id=video_id)
        info = entries[0]

        uploader_id = self._search_regex(
            r'href="https?://(?:www\.)?mgtow\.tv/@([^"/?#]+)"',
            webpage, 'uploader id', default=None)
        uploader = self._html_search_regex(
            r'class="publisher-name"[^>]*>\s*<a[^>]*>([^<]+)',
            webpage, 'uploader', default=None) or uploader_id
        uploader_url = urljoin('https://www.mgtow.tv/', f'@{uploader_id}') if uploader_id else None
        category = self._html_search_regex(
            r'/videos/category/\d+[^>]*>([^<]+)', webpage, 'category', default=None)

        info.update({
            'id': video_id,
            'title': (
                self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)),
            'description': (
                clean_html(get_element_html_by_class('watch-video-description', webpage) or '')
                or self._og_search_description(webpage, default=None)),
            'thumbnail': self._og_search_thumbnail(webpage) or info.get('thumbnail'),
            'duration': parse_duration(self._search_regex(
                r'"duration"\s*:\s*"([\d:]+)"', webpage, 'duration', default=None)),
            'upload_date': unified_strdate(self._search_regex(
                r'Published on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
                webpage, 'upload date', default=None)),
            'view_count': parse_count(get_element_by_id('video-views-count', webpage)),
            'like_count': parse_count(get_element_by_id('likes', webpage)),
            'dislike_count': parse_count(get_element_by_id('dislikes', webpage)),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'channel': uploader,
            'channel_id': uploader_id,
            'channel_url': uploader_url,
            'categories': [category] if category else None,
        })
        return info
