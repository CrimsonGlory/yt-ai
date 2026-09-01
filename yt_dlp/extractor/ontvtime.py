import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_qs,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class OnTVTimeIE(InfoExtractor):
    IE_NAME = 'ontvtime'
    IE_DESC = 'OnTVtime'
    _VALID_URL = [
        r'https?://(?:www\.)?ontvtime\.ru/index\.php\?(?:[^#]*&)?task=view_record(?:&[^#]*)?',
        r'https?://(?:www\.)?ontvtime\.ru/live/(?P<id>[\w-]+)\.html',
    ]
    _TESTS = [{
        'url': 'https://www.ontvtime.ru/index.php?option=com_content&task=view_record&id=1450&start_record=2026-08-28-21-30',
        'md5': 'aa294b904e438760f7305a74ac260d8f',
        'info_dict': {
            'id': '1450_2026-08-28-21-30',
            'ext': 'mp4',
            'title': 'Новая волна-2026. Гала-концерт звезд',
            'description': 'md5:ce774c40362ed5ed4502f750cb03ca88',
            'channel': 'Россия 1, архив',
            'timestamp': 1787941800,
            'upload_date': '20260828',
            'live_status': 'was_live',
        },
    }, {
        'url': 'https://www.ontvtime.ru/live/russia1-tv.html',
        'only_matching': True,
    }, {
        'url': 'https://www.ontvtime.ru/index.php?option=com_content&task=view_record&id=1421&start_record=2026-08-28-20-00',
        'only_matching': True,
    }]
    _STREAM_HEADERS = {'Referer': 'https://www.ontvtime.ru/'}

    def _cookie_value(self, url, name):
        cookie = self._get_cookies(url).get(name)
        return cookie.value if cookie else None

    def _is_native_host(self, host):
        if not host or host in ('stop', '127.0.0.1', '0.0.0.0'):
            return False
        return '.' in host and not host.replace('.', '').isdigit()

    def _extract_embed_url(self, webpage, host):
        return url_or_none(self._proto_relative_url(self._search_regex(
            rf'host\s*==\s*(["\']){re.escape(host)}\1[\s\S]{{0,800}}?<iframe[^>]+src=(["\'])(?P<url>[^"\']+)\2',
            webpage, 'embed URL', default=None, group='url')))

    def _real_extract(self, url):
        live_id = self._match_valid_url(url).groupdict().get('id')
        qs = parse_qs(url)
        if live_id:
            video_id = live_id
            is_record = False
            start_record = None
        else:
            channel_id = traverse_obj(qs, ('id', 0))
            start_record = traverse_obj(qs, ('start_record', 0))
            if not channel_id or not start_record:
                raise ExtractorError('Unable to parse archive URL', expected=True)
            video_id = f'{channel_id}_{start_record}'
            is_record = True

        webpage = self._download_webpage(url, video_id)

        gid = self._search_regex(
            r'var\s+gid\s*=\s*[\'"]([A-Fa-f0-9]+)[\'"]', webpage, 'gid')
        gid2 = self._search_regex(
            r'var\s+gid2\s*=\s*[\'"]([A-Fa-f0-9]*)[\'"]', webpage, 'gid2', default='')
        if self._cookie_value(url, 'tv3') == '1' and gid2:
            gid = gid2

        host = self._cookie_value(url, 'tv')
        sid = self._cookie_value(url, 'tv2')
        start_ts = int_or_none(self._cookie_value(url, 'tv1')) if is_record else None

        channel = self._html_search_regex(
            r'id="ch_title">([^<]+)', webpage, 'channel', default=None)
        program = None
        if start_record:
            program = self._html_search_regex(
                rf'start_record={re.escape(start_record)}[^>]*>\s*<b>([^<]+)</b>',
                webpage, 'program title', default=None)
        title = program or channel or self._html_extract_title(webpage)

        info = {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, default=None),
            'channel': channel,
            'timestamp': start_ts,
            'http_headers': self._STREAM_HEADERS,
        }

        if host == 'stop':
            raise ExtractorError('This stream is unavailable', expected=True)

        if self._is_native_host(host):
            if not sid:
                raise ExtractorError('Unable to extract stream session', expected=True)
            formats, subtitles = [], {}
            for format_id, prefix, quality in (
                ('high', 'a' if is_record else 'i', 1),
                ('low', 'b' if is_record else 'j', -1),
            ):
                stream_url = f'https://{host}/stream/{gid}/{prefix}{sid}playlist.m3u8'
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    stream_url, video_id, 'mp4', m3u8_id=f'hls-{format_id}',
                    quality=quality, fatal=False, live=not is_record,
                    headers=self._STREAM_HEADERS,
                    query={'time': start_ts} if is_record and start_ts else {})
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            if not formats:
                self.raise_no_formats('No HLS formats found', expected=True, video_id=video_id)
            info.update({
                'formats': formats,
                'subtitles': subtitles,
                'is_live': not is_record,
                'live_status': 'was_live' if is_record else 'is_live',
            })
            return info

        embed_url = self._extract_embed_url(webpage, host) if host else None
        if embed_url:
            return self.url_result(embed_url, video_title=title)

        if host and re.search(
                rf'host\s*==\s*(["\']){re.escape(host)}\1[\s\S]{{0,400}}?регион',
                webpage):
            self.raise_geo_restricted()

        raise ExtractorError('Unable to extract stream URL', expected=True)
