from .common import InfoExtractor
from .vimeo import VimeoIE
from ..utils import (
    filter_dict,
    parse_duration,
    str_to_int,
    unescapeHTML,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BlodIE(InfoExtractor):
    IE_NAME = 'blod'
    IE_DESC = 'Bodossaki Lectures on Demand'
    _VALID_URL = r'https?://(?:www\.)?blod\.gr/lectures/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.blod.gr/lectures/ta-konstantineia-psifidota-tis-rotontas-i-tehni-tou-idanikou/',
        'md5': 'de793478331e1e0ba3706962965f6cb7',
        'info_dict': {
            'id': '1016566922',
            'ext': 'mp4',
            'display_id': 'ta-konstantineia-psifidota-tis-rotontas-i-tehni-tou-idanikou',
            'title': 'Τα κωνσταντίνεια ψηφιδωτά της Ροτόντας: Η τέχνη του ιδανικού',
            'description': 'md5:d2c58f7fbee06919edf278a03ec9ae4a',
            'duration': 2971,
            'timestamp': 1697760000,
            'upload_date': '20231020',
            'thumbnail': r're:https?://(?:www\.)?blod\.gr/media/.+',
            'language': 'el',
            'creators': ['Μπακιρτζής Χαράλαμπος', 'Χατζημιχάλης Γιώργος'],
            'tags': ['Γιώργος Χατζημιχάλης', 'ψηφιδωτό', 'Ροτόντα'],
            'view_count': int,
            'uploader': 'Bodossaki Foundation',
            'uploader_id': 'user84412930',
            'uploader_url': 'https://vimeo.com/user84412930',
        },
        'params': {
            'format': 'bv*[height<=360][protocol^=m3u8]/bv*',
            'external_downloader': 'ffmpeg',
        },
        'expected_warnings': ['Failed to parse XML: not well-formed'],
    }, {
        'url': 'https://www.blod.gr/lectures/i-apeikonisi-tou-theiou-me-ohima-ton-mytho-anamesa-stin-ellada-kai-ti-romi-eisagogikes-paratiriseis/',
        'only_matching': True,
    }, {
        'url': 'https://blod.gr/lectures/oidipous-tyrannos',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)

        vimeo_id = self._search_regex(
            r'\bdata-vimeo-id=["\'](\d+)', webpage, 'vimeo id')

        ld = self._search_json(
            r'<script[^>]+type=(["\'])application/ld(?:\+|&#x2[bB];|&#43;)json\1[^>]*>',
            webpage, 'JSON-LD', display_id, end_pattern='</script>', default={})
        video = traverse_obj(
            ld, ('@graph', lambda _, v: v.get('@type') == 'VideoObject', {dict}),
            get_all=False) or {}

        info = {
            'display_id': display_id,
            **traverse_obj(video, {
                'title': ('name', {str}),
                'description': ('description', {unescapeHTML}),
                'duration': ('duration', {parse_duration}),
                'timestamp': ('uploadDate', {unified_timestamp}),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
                'language': ('inLanguage', {str}),
            }),
            'creators': traverse_obj(
                ld, ('@graph', lambda _, v: v.get('@type') == 'Person', 'name', {str})) or None,
            'view_count': str_to_int(self._search_regex(
                r'(?s)class="total-views"[^>]*>.*?<b>\s*([\d.,]+)',
                webpage, 'view count', default=None)),
        }
        keywords = video.get('keywords')
        if isinstance(keywords, str):
            info['tags'] = [t.strip() for t in keywords.split(',') if t.strip()]
        if not info.get('title'):
            info['title'] = (
                self._html_search_regex(
                    r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
                or self._og_search_title(webpage))

        return self.url_result(
            VimeoIE._smuggle_referrer(f'https://player.vimeo.com/video/{vimeo_id}', url),
            VimeoIE, vimeo_id, url_transparent=True, **filter_dict(info))
