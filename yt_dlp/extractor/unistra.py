import re

from .common import InfoExtractor
from ..utils import qualities


class UnistraIE(InfoExtractor):
    _VALID_URL = r'https?://utv\.unistra\.fr/(?:index|video)\.php\?id_video=(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://utv.unistra.fr/video.php?id_video=154',
            'md5': '736f605cfdc96724d55bb543ab3ced24',
            'info_dict': {
                'id': '154',
                'ext': 'mp4',
                'title': 'M!ss Yella',
                'description': 'md5:280c67ed7e363f5eeacef6f1a62b2389',
                'thumbnail': r're:https?://utv\.unistra\.fr/img/img_video/.+',
            },
        },
        {
            'url': 'http://utv.unistra.fr/index.php?id_video=437',
            'md5': '1ddddd6cccaae76f622ce29b8779636d',
            'info_dict': {
                'id': '437',
                'ext': 'mp4',
                'title': 'Prix Louise Weiss 2014',
                'description': 'md5:7a94e0aa49b74a7c2d5c738bc83703d9',
                'thumbnail': r're:https?://utv\.unistra\.fr/img/img_video/.+',
            },
        },
    ]
    _VOD_BASE = 'https://vod-stream.di.unistra.fr/vod-flash/video/vod'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        quality = qualities(['SD', 'HD'])
        formats, seen = [], set()
        for entry in self._parse_html5_media_entries(url, webpage, video_id):
            for fmt in entry.get('formats') or []:
                media_url = fmt.get('url')
                if not media_url or media_url in seen:
                    continue
                seen.add(media_url)
                format_id = (
                    'HD' if media_url.endswith('-HD.mp4')
                    else 'SD' if media_url.endswith('-SD.mp4') else None)
                if format_id:
                    fmt['format_id'] = format_id
                    fmt['quality'] = quality(format_id)
                formats.append(fmt)

        if not formats:
            files = set(re.findall(r'file\s*:\s*"(/[^"]+)"', webpage))
            for file_path in files:
                format_id = 'HD' if file_path.endswith('-HD.mp4') else 'SD'
                formats.append({
                    'url': f'{self._VOD_BASE}{file_path}',
                    'format_id': format_id,
                    'quality': quality(format_id),
                })

        title = self._html_search_regex(
            r'<title>UTV - (.*?)</', webpage, 'title')
        description = self._html_search_regex(
            r'<meta name="Description" content="(.*?)"', webpage, 'description', flags=re.DOTALL)
        thumbnail = self._search_regex(
            r'image:\s*"(.*?)"', webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
