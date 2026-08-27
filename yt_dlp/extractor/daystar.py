from .common import InfoExtractor
from ..utils import js_to_json, urljoin


class DaystarClipIE(InfoExtractor):
    IE_NAME = 'daystar:clip'
    _VALID_URL = r'https?://player\.daystar\.tv/(?:live/)?(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://player.daystar.tv/0MTO2ITM',
        'md5': 'ac05b974a5b673f750688905e8efa43b',
        'info_dict': {
            'id': '0MTO2ITM',
            'ext': 'mp4',
            'title': 'The Dark World of COVID Pt. 1 | Aaron Siri',
            'description': 'md5:a420d320dda734e5f29458df3606c5f4',
            'thumbnail': r're:https?://.+\.jpg',
        },
    }, {
        'url': 'https://player.daystar.tv/live/MzNwkTO',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        src_iframe = self._search_regex(r'<iframe[^>]+src="([^"]+)"', webpage, 'src iframe')
        player = self._download_webpage(src_iframe, video_id)
        config_url = urljoin(src_iframe, self._search_regex(
            r"configUrl\s*=\s*'([^']+)'", player, 'config url'))
        webpage_iframe = self._download_webpage(
            config_url, video_id, headers={'Referer': src_iframe})

        sources = self._parse_json(self._search_regex(
            r'sources:\s*(\[.*?\])', webpage_iframe, 'm3u8 source'), video_id, transform_source=js_to_json)

        formats, subtitles = [], {}
        for source in sources:
            media_url = source.get('file')
            if media_url and source.get('type') == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    urljoin('https://www.lightcast.com/embed/', media_url),
                    video_id, 'mp4', fatal=False, headers={'Referer': src_iframe})
                formats.extend(fmts)
                subtitles = self._merge_subtitles(subtitles, subs)

        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)', webpage_iframe, 'thumbnail', default=None)
        if thumbnail:
            thumbnail = thumbnail.replace('\\/', '/')

        return {
            'id': video_id,
            'title': self._html_search_meta(['og:title', 'twitter:title'], webpage),
            'description': self._html_search_meta(['og:description', 'twitter:description'], webpage),
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
        }
