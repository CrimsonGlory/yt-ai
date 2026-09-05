from .common import InfoExtractor
from ..utils import (
    str_to_int,
    unescapeHTML,
    url_or_none,
)


class Ku6IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ku6\.com/video/detail\?(?:[^#]*&)?id=(?P<id>[\w.-]+)'
    _TESTS = [{
        'url': 'https://www.ku6.com/video/detail?id=6QZvCP48tmowMnCQqiVffWmDAts.',
        'skip': 'site unavailable',
        'md5': 'f502c5792ac207b978410262b7f155f4',
        'info_dict': {
            'id': '6QZvCP48tmowMnCQqiVffWmDAts.',
            'ext': 'mp4',
            'title': '普法动画宣传片短片，让普法教育更简单',
            'thumbnail': r're:https?://rbv01\.ku6\.com/wifi/.+',
            'uploader': 'ku6',
            'view_count': int,
        },
    }, {
        'url': 'https://www.ku6.com/video/detail?id=hYkMomz8DrvBwCmwDAtOtsHZXp8.',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(
            r'document\.title\s*=\s*"([^"]+)"', webpage, 'title')
        video_url = url_or_none(
            self._search_regex(
                r'type:\s*"video/mp4",\s*src:\s*"([^"]+)"',
                webpage, 'video url', default=None)
            or self._search_regex(r'flvURL:\s*"([^"]+)"', webpage, 'video url'))
        thumbnail = url_or_none(self._search_regex(
            r'"poster":\s*"([^"]+)"', webpage, 'thumbnail', default=None))
        uploader = self._search_regex(
            r"\$\('#video-pc-author'\)\.text\(\"([^\"]+)\"\)",
            webpage, 'uploader', default=None)
        view_count = str_to_int(self._search_regex(
            r"\$\('#video-count'\)\.text\(\"([^\"]+)\"\)",
            webpage, 'view count', default=None))

        return {
            'id': video_id,
            'title': unescapeHTML(title),
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'uploader': uploader,
            'view_count': view_count,
        }
