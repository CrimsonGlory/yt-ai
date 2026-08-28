import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    strip_or_none,
    url_or_none,
    urljoin,
)


class ToypicsIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'Toypics video'
    _VALID_URL = r'https?://(?:videos\.)?toypics\.net/(?:view|(?:u/(?P<uploader>[^/?#&]+)))/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://toypics.net/u/Philly/3218',
        'md5': 'd2ba2ab8487137e85a04c6dbcc71dbd7',
        'info_dict': {
            'id': '3218',
            'ext': 'mp4',
            'title': 'Juicy pullout',
            'description': 'Just enjoying my loose hole but so need to get it looser',
            'thumbnail': r're:https?://static\.toypics\.net/.+\.jpg',
            'uploader': 'Philly',
            'age_limit': 18,
            'view_count': int,
        },
    }, {
        'url': 'http://videos.toypics.net/view/514/chancebulged,-2-1/',
        'skip': 'video gone',
        'md5': '16e806ad6d6f58079d210fe30985e08b',
        'info_dict': {
            'id': '514',
            'ext': 'mp4',
            'title': "Chance-Bulge'd, 2",
            'age_limit': 18,
            'uploader': 'kidsune',
        },
    }, {
        'url': 'https://videos.toypics.net/u/Philly/3218',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = url_or_none(self._og_search_video_url(
            webpage, default=None)) or url_or_none(self._html_search_meta(
            'twitter:player:stream', webpage)) or self._search_regex(
            r'''file:\s*['"](https?://[^'"]+\.mp4)['"]''', webpage, 'video URL')

        title = strip_or_none(
            self._html_search_regex(r'<h4>([^<]+)</h4>', webpage, 'title', default=None)
            or self._og_search_title(webpage))

        uploader = self._match_valid_url(url).group('uploader') or strip_or_none(
            self._html_search_regex(
                r'<h5 class="text-danger">([^<]+)</h5>', webpage, 'uploader', default=None))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': strip_or_none(self._og_search_description(webpage)),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader': uploader,
            'view_count': int_or_none(self._search_regex(
                r'(\d+)\s*views', webpage, 'view count', default=None)),
            'age_limit': 18,
        }


class ToypicsUserIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'Toypics user profile'
    _VALID_URL = r'https?://(?:videos\.)?toypics\.net/u/(?P<id>[^/?#&]+)/?(?:$|[?#])'
    _TEST = {
        'url': 'https://toypics.net/u/Philly',
        'info_dict': {
            'id': 'Philly',
        },
        'playlist_mincount': 5,
    }

    def _real_extract(self, url):
        username = self._match_id(url)
        webpage = self._download_webpage(
            url, username, note='Retrieving profile page')
        return self.playlist_from_matches(
            re.findall(rf'href="(/u/{re.escape(username)}/\d+)"', webpage),
            username, getter=lambda path: urljoin(url, path), ie='Toypics')
