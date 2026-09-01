import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    remove_start,
    unified_timestamp,
    url_or_none,
)


class QuartierRougeIE(InfoExtractor):
    IE_NAME = 'quartierrouge'
    IE_DESC = 'Quartier-Rouge / Redlights'
    _VALID_URL = (
        r'https?://(?:www\.)?(?:quartier-rouge|redlights)\.be/'
        r'(?:profil(?:e)?/(?P<id>[^/?#]+)|(?:prive(?:-ontvangst)?|escort|massage|'
        r'adresses|adressen|sexe-virtuel|virtuele-seks)(?:/[^/?#]+)*/(?P<ad_id>[^/?#]+)\.html)')
    _TESTS = [{
        'url': 'https://www.quartier-rouge.be/prive/femmes/gabriela-352661387189.html',
        'md5': 'fd4e46a5b99ecd1a22259671eb852df5',
        'info_dict': {
            'id': 'gabriela-gfe-20240228193516',
            'ext': 'mp4',
            'display_id': 'gabriela-352661387189',
            'title': 'Gabriela',
            'description': 'md5:0dc6ba28a21b3b1525872d1d0631306b',
            'thumbnail': 'https://a.qr.be/videos/695930/gabriela-gfe-20240228193516/gabriela-gfe-20240228193516.jpg',
            'timestamp': 1709148916,
            'upload_date': '20240228',
            'age_limit': 18,
        },
        'params': {
            'playlist_items': '1',
        },
    }, {
        'url': 'https://www.quartier-rouge.be/prive/femmes/gabriela-352661387189.html',
        'info_dict': {
            'id': 'gabriela-352661387189',
            'title': 'Gabriela',
            'description': 'md5:0dc6ba28a21b3b1525872d1d0631306b',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'https://www.quartier-rouge.be/prive/femmes/gabriela-gfe-anal-3.html',
        'only_matching': True,
    }, {
        'url': 'https://www.quartier-rouge.be/profil/romeo-2172/',
        'only_matching': True,
    }, {
        'url': 'https://www.quartier-rouge.be/escort/femmes/sara-escort-liege.html',
        'only_matching': True,
    }, {
        'url': 'https://www.quartier-rouge.be/massage/mia-sur-bruxelles.html',
        'only_matching': True,
    }, {
        'url': 'https://www.redlights.be/prive-ontvangst/dames/scarlet-club-kinky-rooms.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id') or mobj.group('ad_id')
        webpage = self._download_webpage(url, display_id)

        title = (self._og_search_title(webpage, default=None)
                 or self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                 or display_id)
        description = self._og_search_description(webpage, default=None)
        headers = {'Referer': url}

        entries = []
        for video_el in re.finditer(r'<video-js([^>]*)>(.*?)</video-js>', webpage, re.DOTALL):
            attrs = extract_attributes(f'<video-js{video_el.group(1)}>')
            src = url_or_none(self._search_regex(
                r'<source[^>]+\bsrc=["\']([^"\']+)', video_el.group(2), 'source', default=None))
            if not src:
                continue
            video_id = remove_start(attrs.get('id'), 'vid-') or self._search_regex(
                r'/([^/]+)\.m3u8', src, 'video id', default=None)
            if not video_id:
                continue
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                src, video_id, 'mp4', m3u8_id='hls', headers=headers, fatal=False)
            if not formats:
                continue
            timestamp = unified_timestamp(self._search_regex(
                r'(\d{14})$', video_id, 'timestamp', default=None))
            entries.append({
                'id': video_id,
                'display_id': display_id,
                'title': title,
                'description': description,
                'thumbnail': url_or_none(attrs.get('data-poster')),
                'formats': formats,
                'subtitles': subtitles,
                'age_limit': 18,
                'timestamp': timestamp,
                'http_headers': headers,
            })

        if not entries:
            raise ExtractorError('No videos found', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, display_id, title, description)
