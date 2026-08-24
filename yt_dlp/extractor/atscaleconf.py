import re

from .common import InfoExtractor


class AtScaleConfEventIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?atscaleconference\.com/events/(?P<id>[^/&$?]+)'

    _TESTS = [{
        'url': 'https://atscaleconference.com/events/data-scale-spring-2022/',
        'playlist_mincount': 13,
        'info_dict': {
            'id': 'data-scale-spring-2022',
            'title': 'Data @Scale Spring 2022',
            'description': 'md5:9eded9bdc5d01ddf76ef4ee53ef1e7e4',
        },
    }, {
        'url': 'https://atscaleconference.com/events/video-scale-2021/',
        'playlist_mincount': 14,
        'info_dict': {
            'id': 'video-scale-2021',
            'title': 'Video @Scale 2021',
            'description': 'md5:9eded9bdc5d01ddf76ef4ee53ef1e7e4',
        },
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        return self.playlist_from_matches(
            re.findall(r'data-url\s*=\s*"(https?://(?:www\.)?atscaleconference\.com/videos/[^"]+)"', webpage),
            ie='Generic', playlist_id=playlist_id,
            title=self._og_search_title(webpage), description=self._og_search_description(webpage))
