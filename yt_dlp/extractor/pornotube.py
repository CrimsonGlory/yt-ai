import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    urlencode_postdata,
)


class PornotubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?pornotube\.com/(?:[^?#]*?)/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.pornotube.com/orientation/straight/video/4964/title/weird-hot-and-wet-science',
        'md5': 'a9e6a915debd0ce3de32d190974b9d3a',
        'info_dict': {
            'id': '4964',
            'ext': 'mp4',
            'title': 'Weird Hot and Wet Science',
            'description': 'md5:a8304bef7ef06cb4ab476ca6029b01b0',
            'categories': ['Adult Humor', 'Blondes'],
            'uploader': 'Alpha Blue Archives',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 300,
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self._set_cookie(urllib.parse.urlparse(url).hostname, 'ageGated', 'true')
        webpage = self._download_webpage(url, video_id)

        confirm_url = self._search_regex(
            r'<a[^>]+id="avs-confirm-btn"[^>]+href="([^"]+)"',
            webpage, 'age confirmation url', default=None)
        if confirm_url:
            webpage = self._download_webpage(
                urllib.parse.urljoin(url, confirm_url), video_id,
                note='Confirming age gate')

        delivery = self._download_json(
            'https://www.pornotube.com/deliver', video_id,
            note='Downloading delivery information',
            data=urlencode_postdata({
                'clipId': video_id,
                'format': 'HLS',
            }),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://www.pornotube.com',
                'Referer': url,
            })

        formats = self._extract_m3u8_formats(
            delivery['mediaUrl'], video_id, 'mp4', m3u8_id='hls')

        return {
            'id': video_id,
            'title': self._html_search_regex(
                r'<h1[^>]*class="[^"]*pageTitle[^"]*"[^>]*>([^<]+)',
                webpage, 'title'),
            'description': self._html_search_meta('description', webpage),
            'duration': int_or_none(delivery.get('clipDurationSeconds')),
            'uploader': self._html_search_regex(
                r'/search/studio/id/\d+/[^>]*>([^<]+)', webpage,
                'uploader', default=None),
            'thumbnail': self._html_search_meta('twitter:image', webpage),
            'categories': re.findall(
                r'<a[^>]+/search/category/id/\d+/[^>]*>([^<]+)', webpage),
            'age_limit': 18,
            'formats': formats,
        }
