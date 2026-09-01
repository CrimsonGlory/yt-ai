from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    url_or_none,
)


class CanliTVIE(InfoExtractor):
    IE_NAME = 'canlitv'
    IE_DESC = 'canlitv.com'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?canlitv\.com/
        (?!(?:tr|televizyonlar|kameralar|favoriler|rating|yayin-akisi|blog|kanal-bilgi|player|hd)
            (?:/|$|[?#])
            |[^/?#]*-kanallari(?:/|$|[?#]))
        (?P<id>[^/?#]+)
        /?(?:$|[?#])
    '''
    _TESTS = [{
        'url': 'https://canlitv.com/tv8-izle-4',
        'info_dict': {
            'id': '10924',
            'ext': 'mp4',
            'display_id': 'tv8-izle-4',
            'title': r're:Tv8 Canlı izle \| Canlitv\.com',
            'description': 'Tv8 canlı izle, Tv8 kanalınının internet yayınını canlı olarak izleyebileceğiniz sayfa.',
            'thumbnail': r're:https?://canlitv\.com/kanal/logo/\d+\.jpg',
            'is_live': True,
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://canlitv.com/canli-tv8',
        'only_matching': True,
    }, {
        'url': 'https://www.canlitv.com/atv-canli',
        'only_matching': True,
    }, {
        'url': 'https://canlitv.com/kiz-kulesi',
        'only_matching': True,
    }]
    _PLAYER_URL = 'https://canlitv.com/player/index.php'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'var\s+aktifKanal\s*=\s*(\d+)', webpage, 'channel id', default=None)
        if not video_id or video_id == '0':
            video_id = self._search_regex(
                r'Player"\)\.src\s*=\s*"/player/index\.php\?id=(\d+)',
                webpage, 'channel id')

        player = self._download_webpage(
            self._PLAYER_URL, video_id, 'Downloading player',
            query={'id': video_id, 'mobile': '0'},
            headers={'Referer': url})

        formats, subtitles = [], {}
        jw_info = self._extract_jwplayer_data(
            player, video_id, require_title=False, m3u8_id='hls') or {}
        if isinstance(jw_info, list):
            jw_info = jw_info[0] if jw_info else {}

        for fmt in jw_info.get('formats') or []:
            fmt_url = url_or_none(fmt.get('url'))
            if not fmt_url or 'canlitv.mp4' in fmt_url:
                continue
            formats.append(fmt)
        if jw_info.get('subtitles'):
            self._merge_subtitles(jw_info['subtitles'], target=subtitles)

        if not formats:
            m3u8_url = url_or_none(self._search_regex(
                r'(https?://[^"\']+\.m3u8[^"\']*)', player, 'm3u8 URL', default=None))
            if m3u8_url:
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                    m3u8_url, video_id, 'mp4', m3u8_id='hls', live=True)

        if not formats:
            raise ExtractorError('No live stream available', expected=True)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage, default=None) or jw_info.get('title') or display_id,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }
