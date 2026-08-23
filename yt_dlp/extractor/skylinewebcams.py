import re

from .common import InfoExtractor


class SkylineWebcamsIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?skylinewebcams\.com/[^/]+/webcam/(?:[^/]+/)+(?P<id>[^/]+)\.html'
    _TEST = {
        'url': 'https://www.skylinewebcams.com/it/webcam/italia/lazio/roma/scalinata-piazza-di-spagna-barcaccia.html',
        'info_dict': {
            'id': 'scalinata-piazza-di-spagna-barcaccia',
            'ext': 'mp4',
            'title': 're:^Live Webcam Scalinata di Piazza di Spagna - La Barcaccia [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'Roma, veduta sulla Scalinata di Piazza di Spagna e sulla Barcaccia',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        stream_url = self._search_regex(
            r'(?:url|source)\s*:\s*(["\'])(?P<url>(?:https?:)?//.+?\.m3u8.*?)\1', webpage,
            'stream url', group='url', default=None)

        cam_id = self._search_regex(
            r'(?:social|cdn\.skylinewebcams\.com/)(\d+)\.jpg',
            webpage, 'camera id', default=None) or self._search_regex(
            r'data-value="\d+&(?:amp;)?id=(\d+)"', webpage, 'camera id', default=None)

        if not stream_url and cam_id:
            stream_url = f'https://hd-auth.skylinewebcams.com/live.m3u8?a={cam_id}'

        if not stream_url:
            stream_url = self._search_regex(
                r'(https?://[^"\']+\.m3u8[^"\']*)', webpage, 'stream url')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        return {
            'id': cam_id or video_id,
            'display_id': video_id,
            'url': stream_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'is_live': True,
        }
