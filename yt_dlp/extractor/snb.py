from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class SNBIE(InfoExtractor):
    IE_NAME = 'snb'
    IE_DESC = 'Swiss National Bank Research TV and Web TV'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?snb\.ch/
        (?P<lang>[a-z]{2})/services-events/digital-services/
        (?:research-tv|webtv)/
        (?P<id>(?:researchtv|webtv)-\d{4}-\d{2}-\d{2}(?:_\d+)?)
    '''
    _TESTS = [{
        'url': 'https://www.snb.ch/en/services-events/digital-services/research-tv/researchtv-2025-10-02',
        'md5': '269371065c1b6ebdbb463de371eb93e0',
        'info_dict': {
            'id': '68bff74a1a4700fbff5f2f52',
            'ext': 'mp4',
            'display_id': 'researchtv-2025-10-02',
            'title': 'Karl Brunner Distinguished Lecture 2025 by John H. Cochrane (Hoover Institution)',
            'alt_title': '02.10.2025 - SNB Karl Brunner 2025_Edit',
            'uploader': 'SNB Research',
            'uploader_id': '595641605a53b88591267f02',
            'release_timestamp': 1759419000,
            'release_date': '20251002',
            'modified_timestamp': 1759485387,
            'modified_date': '20251003',
        },
    }, {
        'url': 'https://www.snb.ch/de/services-events/digital-services/research-tv/researchtv-2025-10-02',
        'only_matching': True,
    }, {
        'url': 'https://www.snb.ch/fr/services-events/digital-services/research-tv/researchtv-2025-10-02',
        'only_matching': True,
    }, {
        'url': 'https://www.snb.ch/it/services-events/digital-services/research-tv/researchtv-2025-10-02',
        'only_matching': True,
    }, {
        'url': 'https://www.snb.ch/en/services-events/digital-services/webtv/webtv-2025-12-11',
        'only_matching': True,
    }, {
        'url': 'https://www.snb.ch/en/services-events/digital-services/research-tv/researchtv-2026-05-22_01',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, page_lang = self._match_valid_url(url).group('id', 'lang')
        webpage = self._download_webpage(url, display_id)

        webcast_id, lang = self._search_regex(
            r'https?://webcast\.swisscom\.ch/csr/#/webcast/([0-9a-f]+)/(\w+)',
            webpage, 'Swisscom webcast ID', group=(1, 2))
        lang = lang or page_lang

        token = traverse_obj(self._download_json(
            f'https://webcast.swisscom.ch/api/v1/login/webcast/{webcast_id}',
            display_id, 'Downloading access token'), ('token', {str}))
        if not token:
            raise ExtractorError('Unable to extract Swisscom access token', expected=True)

        data = self._download_json(
            f'https://webcast.swisscom.ch/api/v1/public/webcast/{webcast_id}',
            display_id, headers={'Authorization': f'Bearer {token}'})

        if traverse_obj(data, (
            'securityData', ('passwordAccess', 'registrationAccess', 'ssoAccess'), {bool}, any,
        )):
            self.raise_login_required(
                'This SNB webcast requires a password or registration')

        languages = traverse_obj(data, ('languages', ..., {dict})) or []
        info = (
            next((item for item in languages if item.get('language') == lang), None)
            or next((item for item in languages if traverse_obj(
                item, ('player', 'hlsUrl', {url_or_none}))), None))
        if not info:
            raise ExtractorError('Unable to extract Swisscom webcast metadata', expected=True)

        hls_url = traverse_obj(info, ('player', 'hlsUrl', {url_or_none}))
        if not hls_url:
            raise ExtractorError('Unable to extract HLS URL', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, webcast_id, 'mp4', m3u8_id='hls')

        title = (
            traverse_obj(info, ('name', {str}))
            or traverse_obj(data, ('name', {str}))
            or self._html_search_regex(
                r'<section[^>]+class="m-webtv-event"[^>]*>\s*<h2>([^<]+)',
                webpage, 'title', default=None))

        return {
            'id': webcast_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(info, {
                'alt_title': ('player', 'videoTitle', {str}),
                'description': ('description', {str}, filter),
            }),
            **traverse_obj(data, {
                'uploader_id': ('customer', 'id', {str}),
                'uploader': ('customer', 'name', {str}),
                'release_timestamp': ('startDate', {int_or_none(scale=1000)}),
                'modified_timestamp': ('lastUpdated', {int_or_none}),
            }),
        }
