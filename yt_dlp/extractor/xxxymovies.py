from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
)


class XXXYMoviesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xxxymovies\.com/videos/(?P<id>\d+)/(?P<display_id>[^/]+)'
    _TEST = {
        'url': 'https://xxxymovies.com/videos/196013/ryan-reid-plays-video-games-while-alina-lopez-fucks-manuel-ferrara/',
        'md5': '689ad03b81642541f70e2cadf0b2ec5d',
        'info_dict': {
            'id': '196013',
            'display_id': 'ryan-reid-plays-video-games-while-alina-lopez-fucks-manuel-ferrara',
            'ext': 'mp4',
            'title': 'Ryan Reid Plays Video Games While Alina Lopez Fucks Manuel Ferrara',
            'thumbnail': 'https://xxxymovies.com/contents/videos_screenshots/196000/196013/preview.mp4.jpg',
            'categories': 'count:44',
            'duration': 402,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'age_limit': 18,
        },
    }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_url = self._search_regex(
            r"video_url\s*:\s*'([^']+)'", webpage, 'video URL')

        title = self._html_search_regex(
            [r'<div[^>]+\bclass="block_header"[^>]*>\s*<h1>([^<]+)<',
             r'<title>(.*?)\s*-\s*(?:XXXYMovies\.com|XXX\s+Movies)</title>'],
            webpage, 'title')

        thumbnail = self._search_regex(
            r"preview_url\s*:\s*'([^']+)'",
            webpage, 'thumbnail', fatal=False)

        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')

        duration = parse_duration(self._search_regex(
            r'<span>Duration:</span>\s*(\d+:\d+)',
            webpage, 'duration', fatal=False))

        view_count = int_or_none(self._html_search_regex(
            r'<div class="video_views">\s*(\d+)',
            webpage, 'view count', fatal=False))
        like_count = int_or_none(self._search_regex(
            r'>\s*Likes? <b>\((\d+)\)',
            webpage, 'like count', fatal=False))
        dislike_count = int_or_none(self._search_regex(
            r'>\s*Dislike <b>\((\d+)\)</b>',
            webpage, 'dislike count', fatal=False))

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'categories': categories,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'age_limit': age_limit,
        }
