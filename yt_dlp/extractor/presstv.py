from .common import InfoExtractor
from ..utils import (
    js_to_json,
    remove_start,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PressTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?presstv\.(?:ir|co\.uk)/[^/]+/(?P<y>\d+)/(?P<m>\d+)/(?P<d>\d+)/(?P<id>\d+)/(?P<display_id>[^/?#]+)?'

    _TESTS = [{
        'url': 'https://www.presstv.co.uk/Detail/2026/08/27/775150/Aerial-footage-shows-massive-floods-in-Nepal-Rasuwa-district',
        'md5': '7d8afc75c5164ea1f95c2ee12cd7a711',
        'info_dict': {
            'id': '775150',
            'ext': 'mp4',
            'display_id': 'Aerial-footage-shows-massive-floods-in-Nepal-Rasuwa-district',
            'title': 'Aerial footage shows massive floods in Nepals Rasuwa district',
            'upload_date': '20260827',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg)',
            'description': 'md5:a33a9b8d41c1884ef548a85cd7bde699',
        },
    }, {
        'url': 'http://www.presstv.ir/Detail/2016/04/09/459911/Australian-sewerage-treatment-facility-/',
        'skip': 'video gone',
        'md5': '5d7e3195a447cb13e9267e931d8dd5a5',
        'info_dict': {
            'id': '459911',
            'display_id': 'Australian-sewerage-treatment-facility-',
            'ext': 'mp4',
            'title': 'Organic mattresses used to clean waste water',
            'upload_date': '20160409',
            'thumbnail': r're:^https?://.*\.jpg',
            'description': 'md5:20002e654bbafb6908395a5c0cfcd125',
        },
    }, {
        'url': 'https://www.presstv.ir/Detail/2026/08/27/775150/Aerial-footage-shows-massive-floods-in-Nepal-Rasuwa-district',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        formats = []
        config = self._search_json(
            r'\bvar\s+config\s*=', webpage, 'jwplayer config', video_id,
            transform_source=js_to_json, fatal=False)
        hls_url = traverse_obj(config, ('playlist', 0, 'file', {url_or_none}))
        if not hls_url:
            hls_url = self._search_regex(
                r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                webpage, 'hls url', default=None)
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        mp4_url = self._search_regex(
            r'href=(["\']?)((?:https?:)?//preview\.presstv\.[^"\'\s>]+\.mp4)\1',
            webpage, 'http url', default=None, group=2)
        if mp4_url:
            mp4_url = self._proto_relative_url(mp4_url).replace(
                '://preview.presstv.ir/', '://preview.presstv.co.uk/')
            formats.append({
                'url': mp4_url,
                'format_id': 'http',
                'ext': 'mp4',
            })

        if not formats:
            self.raise_no_formats('No video found', expected=True, video_id=video_id)

        title = remove_start(
            self._og_search_title(webpage, default=None)
            or self._html_search_meta('title', webpage, fatal=True),
            'PressTV-')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': f'{int(mobj.group("y")):04d}{int(mobj.group("m")):02d}{int(mobj.group("d")):02d}',
            'description': (
                self._html_search_meta('description', webpage, default=None)
                or self._og_search_description(webpage)),
        }
