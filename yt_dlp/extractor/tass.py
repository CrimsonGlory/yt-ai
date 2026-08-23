import json

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    qualities,
)


class TassIE(InfoExtractor):
    _VALID_URL = r'https?://(?:tass\.ru|itar-tass\.com)/[^/]+/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://tass.ru/obschestvo/1586870',
            'md5': '3b4cdd011bc59174596b6145cda474a4',
            'info_dict': {
                'id': '1586870',
                'ext': 'mp4',
                'title': 'Посетителям московского зоопарка показали красную панду',
                'description': 'Приехавшую из Дублина Зейну можно увидеть в павильоне "Кошки тропиков"',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://itar-tass.com/obschestvo/1600009',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        sources_raw = self._search_regex(
            r'(?s)sources\s*:\s*(\[.+?\])', webpage, 'sources', default=None)
        quality = qualities(['sd', 'hd'])

        formats = []
        if sources_raw:
            sources = json.loads(js_to_json(sources_raw))
            for source in sources:
                video_url = source.get('file')
                if not video_url or not video_url.startswith('http') or not video_url.endswith('.mp4'):
                    continue
                label = source.get('label')
                formats.append({
                    'url': video_url,
                    'format_id': label,
                    'quality': quality(label),
                })
        if not formats:
            html5 = self._parse_html5_media_entries(url, webpage, video_id)
            if html5:
                formats = html5[0].get('formats') or (
                    [{'url': html5[0]['url']}] if html5[0].get('url') else [])
            og_video = self._og_search_video_url(webpage, default=None)
            if og_video:
                formats.append({'url': og_video})
            for m3u8_url in self._og_search_property('og:video', webpage, default=None), self._search_regex(
                    r'(https?://[^"\']+\.m3u8[^"\']*)', webpage, 'm3u8', default=None):
                if m3u8_url and '.m3u8' in m3u8_url:
                    formats.extend(self._extract_m3u8_formats(
                        m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False) or [])

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
