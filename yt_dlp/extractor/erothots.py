import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    merge_dicts,
    remove_end,
    url_or_none,
)


class ErothotsIE(InfoExtractor):
    IE_DESC = 'erothots.co'
    _VALID_URL = r'https?://(?:www\.)?(?:erothots\.co|erothots1\.com)/(?:embed/)?video/(?P<id>[^/?#]+)(?:/(?P<display_id>[^/?#]+))?'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?(?:erothots\.co|erothots1\.com)/embed/video/[^"\']+)']
    _TESTS = [{
        'url': 'https://erothots.co/video/vgrqoafhb/latina-hot-wifee/',
        'md5': 'c3f92c2eaa69a457ee58e5359ce806b3',
        'info_dict': {
            'id': 'vgrqoafhb',
            'ext': 'mp4',
            'display_id': 'latina-hot-wifee',
            'title': 'Latina hot wifee',
            'description': 'Latina hot wifee hot wife tina hot a h latina hot',
            'thumbnail': r're:https?://cdn\.erocdn\.co/.+/thumb\.webp',
            'duration': 558,
            'timestamp': 1730420291,
            'upload_date': '20241101',
            'tags': ['hot wife', 'tina hot', 'a h', 'latina', 'hot'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://erothots.co/embed/video/vgrqoafhb',
        'only_matching': True,
    }, {
        'url': 'https://erothots1.com/video/vgrqoafhb/latina-hot-wifee/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        video_url = url_or_none(self._search_regex(
            rf'(https?://(?:cdn\.)?erocdn\.co/[^"\']+/{re.escape(video_id)}[^"\']*-video\.mp4)',
            webpage, 'video url', default=None))
        if not video_url:
            for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
                for fmt in entry.get('formats') or []:
                    candidate = url_or_none(fmt.get('url'))
                    if candidate and video_id in candidate and '-video.mp4' in candidate:
                        video_url = candidate
                        break
                if video_url:
                    break
        if not video_url:
            raise ExtractorError('No video source found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        title = (
            json_ld.get('title')
            or self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
            or remove_end(self._og_search_title(webpage, default=''), ' - EroThots')
            or None)

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'age_limit': 18,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
        }, json_ld)
