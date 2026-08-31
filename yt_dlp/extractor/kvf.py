from .common import InfoExtractor
from ..utils import (
    NO_DEFAULT,
    clean_html,
    int_or_none,
    strip_or_none,
    unescapeHTML,
    unified_strdate,
    url_or_none,
)


class KVFIE(InfoExtractor):
    IE_DESC = 'Kringvarp Føroya'
    _VALID_URL = r'https?://(?:www\.)?kvf\.fo/(?:(?:sjon|ljod)/sending/|sending/|vit/(?:sjonvarp|ljod)/\d{4}/\d{2}/\d{2}/|netvarp/(?:sv|uv)/\d{4}/\d{2}/\d{2}/)(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://kvf.fo/sending/mett-fyri-minni?sid=173187',
        'md5': 'adc422b57aa98f82c91a368ed96dbc6a',
        'info_dict': {
            'id': 'DOK01396',
            'ext': 'mp4',
            'display_id': 'mett-fyri-minni',
            'title': 'Mett fyri minni (1:3)',
            'description': 'Í fyrsta parti vitjar Sunniva Gudmundsdóttir Mortensen plantuommuna í Nólsoy, kokkin Sonna Zachariassen og kondittaran Malene Fischer Waag.',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'upload_date': '20240404',
            'release_year': 2024,
        },
        'params': {'format': 'worst'},
    }, {
        'url': 'https://kvf.fo/vit/sjonvarp/2019/11/07/sara-og-dunnan-1-partur',
        'only_matching': True,
    }, {
        'url': 'https://kvf.fo/sjon/sending/dv?sid=212435',
        'only_matching': True,
    }, {
        'url': 'https://kvf.fo/ljod/sending/sogan-um-johnny-cash?sid=212406',
        'only_matching': True,
    }, {
        'url': 'https://kvf.fo/netvarp/sv/2026/08/28/dagur-og-vika',
        'only_matching': True,
    }, {
        'url': 'https://kvf.fo/netvarp/uv/2026/08/28/sgan-um-johnny-cash-8-partur',
        'only_matching': True,
    }]

    def _search_js_var(self, webpage, name, default=NO_DEFAULT):
        return self._search_regex(
            rf'var\s+{name}\s*=\s*(["\'])(?P<value>(?:(?!\1).)*)\1',
            webpage, name, default=default, group='value')

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        media_id = self._search_js_var(webpage, 'media')
        mode = self._search_js_var(webpage, 'mode', default='video')
        if mode not in ('video', 'audio'):
            mode = 'video'

        if self._search_js_var(webpage, 'geo', default='0') == '1':
            self.raise_geo_restricted(countries=['FO'])

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'https://vod.kringvarp.fo/redirect/{mode}/_definst_/smil:smil/{mode}/{media_id}.smil?type=m3u8',
            media_id, 'mp4' if mode == 'video' else 'm4a', m3u8_id='hls')

        return {
            'id': media_id,
            'display_id': display_id,
            'title': (strip_or_none(unescapeHTML(
                self._search_js_var(webpage, 'title', default='')))
                or self._og_search_title(webpage)),
            'description': (strip_or_none(clean_html(
                self._search_js_var(webpage, 'desc', default='')))
                or self._og_search_description(webpage, default=None)),
            'thumbnail': url_or_none(self._search_js_var(webpage, 'image', default=None)) or self._og_search_thumbnail(webpage),
            'upload_date': unified_strdate(self._html_search_regex(
                r'id="sending_publish"[^>]*>([^<]+)', webpage, 'upload date', default=None)),
            'release_year': int_or_none(self._search_js_var(webpage, 'created', default=None)),
            'formats': formats,
            'subtitles': subtitles,
        }
