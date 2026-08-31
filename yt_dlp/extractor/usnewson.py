from .common import InfoExtractor
from ..utils import (
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class USNewsOnIE(InfoExtractor):
    IE_NAME = 'usnewson'
    IE_DESC = 'USNewsON live news streams'
    _VALID_URL = r'https?://(?:www\.)?usnewson\.com/watch/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://usnewson.com/watch/cnn-live',
        'info_dict': {
            'id': 'cnn-live',
            'ext': 'mp4',
            'title': r're:CNN Live Stream - Watch CNN News USA Live Streaming \[HD\]',
            'description': 'md5:243a9db74359fee717a374fb34b928a2',
            'thumbnail': 'https://usnewson.com/assets/images/og-cnn.jpg',
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://usnewson.com/watch/fox-news-live',
        'only_matching': True,
    }, {
        'url': 'https://usnewson.com/watch/msnbc-live',
        'only_matching': True,
    }, {
        'url': 'https://usnewson.com/watch/oann-live-stream',
        'only_matching': True,
    }, {
        'url': 'https://usnewson.com/watch/twc-live-stream',
        'only_matching': True,
    }, {
        'url': 'https://www.usnewson.com/watch/cnn-live',
        'only_matching': True,
    }]

    def _source_m3u8_url(self, source, video_id, headers):
        src = traverse_obj(source, ('src', {str}))
        if not src:
            return None
        stream_type = (source.get('type') or '').lower()
        if stream_type == 'onestream':
            stream_info = self._download_webpage(
                src, video_id, 'Downloading stream info', headers=headers, fatal=False)
            if not stream_info:
                return None
            return url_or_none(stream_info.strip()) or self._search_regex(
                r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', stream_info, 'm3u8 URL', default=None)
        if stream_type in ('hls', 'm3u8') or src.endswith('.m3u8'):
            return url_or_none(src)
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        headers = {'Referer': 'https://usnewson.com/'}

        pllrc = self._search_json(r'var\s+pllrc\s*=', webpage, 'player config', video_id)
        default_pll = self._search_regex(
            r'window\.defaultPll\s*=\s*["\']([^"\']+)["\']',
            webpage, 'default playlist', default=None)

        sources = []
        if default_pll and isinstance(pllrc.get(default_pll), dict):
            sources.append(pllrc[default_pll])
        sources.extend(
            source for key, source in pllrc.items()
            if key != default_pll and isinstance(source, dict))

        formats, subtitles = [], {}
        youtube_id = iframe_url = None
        for source in sources:
            stream_type = (source.get('type') or '').lower()
            src = source.get('src')
            m3u8_url = self._source_m3u8_url(source, video_id, headers)
            if m3u8_url:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    m3u8_url, video_id, 'mp4', m3u8_id='hls', live=True,
                    headers=headers, fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                if formats:
                    break
            elif stream_type == 'youtube' and src:
                youtube_id = youtube_id or src
            elif stream_type == 'iframe':
                iframe_url = iframe_url or url_or_none(src)

        if not formats and youtube_id:
            return self.url_result(
                url_or_none(youtube_id) or f'https://www.youtube.com/watch?v={youtube_id}',
                'Youtube', youtube_id)
        if not formats and iframe_url:
            return self.url_result(iframe_url)
        if not formats:
            self.raise_no_formats('No playable livestream found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'title': (
                self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title', default=None)
                or self._og_search_title(webpage)),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': urljoin(url, self._og_search_thumbnail(webpage, default=None)),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
            'http_headers': headers,
        }
