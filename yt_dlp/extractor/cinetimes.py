import re

from .archiveorg import ArchiveOrgIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    filter_dict,
    get_element_html_by_class,
    int_or_none,
    unescapeHTML,
    url_or_none,
)


class CinetimesIE(InfoExtractor):
    IE_NAME = 'cinetimes'
    IE_DESC = 'Cinetimes'
    _VALID_URL = (
        r'https?://(?:www\.)?cinetimes\.org/(?:(?:en|es-lat|es|fr)/)?'
        r't/(?P<id>[^/?#]+)/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://cinetimes.org/t/un-chien-andalou',
        'md5': '84fc15222aaa12547320bd9ade5393cb',
        'info_dict': {
            'id': 'UnChienAndalou_313',
            'ext': 'wmv',
            'display_id': 'un-chien-andalou',
            'title': 'Un chien andalou',
            'description': 'This is the infamous 1927 surreal classic, with the jaw-dropping scene where Luis Bunuel slashes an eyeball.',
            'uploader': 'Geno_Cuddy@yahoo.com',
            'duration': 985.59,
            'thumbnail': 'https://img.cinetimes.org/img/cache/ed/c3/edc3d3dcb072a92d2afb7b7f6f5f3f5f.jpg',
            'creators': ['Luis Bunuel & Salvador Dali'],
            'track': 'Luis Bu uel Un Chien Andalou Un perro andaluz 1929',
            'timestamp': 1328745475,
            'upload_date': '20120208',
            'release_year': 1929,
        },
        'add_ie': [ArchiveOrgIE.ie_key()],
    }, {
        'url': 'https://cinetimes.org/t/le-diable-geant-ou-le-miracle-de-la-madonne',
        'only_matching': True,
    }, {
        'url': 'https://cinetimes.org/en/t/paavakoothu-24-04-2025-2',
        'only_matching': True,
    }, {
        'url': 'https://cinetimes.org/t/le-voyage-dans-la-lune?video_id=23955',
        'only_matching': True,
    }, {
        'url': 'https://cinetimes.org/t/la-passion-de-jeanne-darc?video_id=51',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        player = get_element_html_by_class('movie-jumbotron-video-container', webpage) or webpage

        iframe = self._search_regex(r'(<iframe\b[^>]+>)', player, 'iframe', default=None)
        embed_url = url_or_none(unescapeHTML(extract_attributes(iframe).get('src'))) if iframe else None
        if embed_url:
            embed_url = self._proto_relative_url(embed_url)
            if 'cdn-cgi' in embed_url:
                embed_url = None

        title = self._html_search_regex(
            r'<h1[^>]+id="video-title"[^>]*>([^<]+)', webpage, 'title', default=None)
        og_title = self._og_search_title(webpage, default=None)
        if og_title:
            og_title = re.sub(r'\s*-\s*Cinetimes\s*$', '', og_title)
        title = title or og_title
        info = filter_dict({
            'display_id': display_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'release_year': int_or_none(self._search_regex(
                r'\((\d{4})\)\s*$', og_title or '', 'release year', default=None)),
        })

        if embed_url:
            return self.url_result(embed_url, url_transparent=True, **info)

        html5 = self._parse_html5_media_entries(url, player, display_id)
        if html5:
            return {
                **html5[0],
                'id': display_id,
                **info,
            }

        if re.search(r'bloqu\w+ pour des raisons de copyright|blocked for copyright', webpage, re.I):
            raise ExtractorError('This video has been blocked for copyright reasons', expected=True)
        raise ExtractorError('No video embed found', expected=True)
