import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    url_or_none,
)


class UrortIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'NRK P3 Urørt'
    _VALID_URL = r'https?://(?:www\.)?urort\.p3\.no/track/(?:embed/(?P<embed_id>\d+)|(?P<artist>[^/?#]+)/(?P<id>[^/?#]+))'
    _TESTS = [{
        'url': 'https://urort.p3.no/track/iben-1/disjointed',
        'md5': 'd1fe3aeb30833d2a42ff65216d3ceed5',
        'info_dict': {
            'id': '232483',
            'ext': 'wav',
            'title': 'Disjointed',
            'display_id': 'disjointed',
            'uploader': 'Iben',
            'thumbnail': r're:https?://.+',
            'description': 'Hør Disjointed fra Iben',
        },
    }, {
        'url': 'https://urort.p3.no/track/embed/232483',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id') or mobj.group('embed_id')
        webpage = self._download_webpage(url, display_id)

        info_el = self._search_regex(
            r'(<div[^>]+\bdata-trackurl="[^"]+"[^>]*>)', webpage, 'track info')
        attrs = extract_attributes(info_el)
        track_url = url_or_none(attrs.get('data-trackurl'))
        if not track_url:
            self.raise_no_formats('No track URL found', expected=True)
        track_id = attrs.get('data-trackid') or display_id

        title = clean_html(self._search_regex(
            r'<h1[^>]*\bclass="title"[^>]*>(.*?)</h1>',
            webpage, 'title', default=None, flags=re.DOTALL))
        if not title:
            title = self._html_search_regex(
                r'<div class="title"[^>]*>\s*(?:<span[^>]*>.*?</span>)?\s*<a[^>]+>([^<]+)</a>',
                webpage, 'title', default=None)
        if not title:
            title = self._og_search_title(webpage)

        uploader = self._html_search_regex(
            r'<div class="artist"><a[^>]+>([^<]+)</a>',
            webpage, 'artist', default=None)

        return {
            'id': track_id,
            'display_id': display_id,
            'url': track_url,
            'title': title,
            'uploader': uploader,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'ext': determine_ext(track_url, 'wav'),
            'vcodec': 'none',
        }
