import re

from .common import InfoExtractor
from ..utils import (
    orderedSet,
    parse_duration,
    urljoin,
)


class Mp4PornIE(InfoExtractor):
    IE_NAME = 'mp4porn'
    IE_DESC = 'mp4porn.space'
    _VALID_URL = r'https?://(?:www\.)?mp4-?porn\.(?:org|site|space|website)/video/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://mp4porn.space/video/edwige+fenech+nude+scene+compilation+2693877',
        'md5': 'dd3e4e3f8a0626202cf3f8199347a890',
        'info_dict': {
            'id': 'edwige+fenech+nude+scene+compilation+2693877',
            'ext': 'mp4',
            'title': 'Edwige Fenech Nude Scene Compilation',
            'description': 'Cult actress Edwige Fenech - Nude scene compilation from various movies',
            'duration': 743,
            'age_limit': 18,
            'categories': ['italian', 'celebrity', 'compilation', 'funny', 'it', 'lingerie', 'nude', 'vintage'],
            'tags': 'count:27',
        },
    }, {
        'url': 'https://mp4-porn.org/video/edwige+fenech+nude+scene+compilation+2693877',
        'only_matching': True,
    }, {
        'url': 'https://mp4porn.site/video/she+likes+to+be+submissive+xhmpEBP',
        'only_matching': True,
    }, {
        'url': 'https://www.mp4porn.website/video/edwige+fenech+nude+scene+compilation+2693877',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, video_id)
        webpage_url = urlh.url
        headers = {'Referer': webpage_url}

        play_url = urljoin(webpage_url, self._search_regex(
            r'\burl_v\s*=\s*(["\'])(?P<url>/play/[^"\']+)\1',
            webpage, 'play URL', group='url'))

        formats = self._extract_m3u8_formats(
            play_url.replace('/play/', '/play_hls/', 1), video_id, 'mp4',
            m3u8_id='hls', fatal=False, headers=headers)
        formats.append({
            'url': play_url,
            'format_id': 'http',
            'ext': 'mp4',
            'http_headers': headers,
        })

        return {
            'id': video_id,
            'title': self._html_search_regex(
                r'(?s)<div class="base_title">(.*?)</div>',
                webpage, 'title', default=None) or video_id,
            'description': self._html_search_meta(
                'description', webpage, default=None) or None,
            'duration': parse_duration(self._html_search_regex(
                r'<div class="duration_">([^<]+)', webpage, 'duration', default=None)),
            'age_limit': 18,
            'categories': orderedSet(re.findall(
                r'<a class="linked_url" href="/category/[^"]*">([^<]+)', webpage)) or None,
            'tags': orderedSet(re.findall(
                r'<a class="linked_url" href="/tag/[^"]*">([^<]+)', webpage)) or None,
            'formats': formats,
            'http_headers': headers,
        }
