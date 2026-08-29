import urllib.parse

from .medialaan import MedialaanBaseIE
from ..utils import str_or_none
from ..utils.traversal import require, traverse_obj


class VTMIE(MedialaanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vtm\.be/[^/?#]+~v(?P<id>[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12})'
    _TESTS = [{
        'url': 'https://vtm.be/spanning-aan-ronde-tafel-in-de-verraders-emoties-lopen-hoog-op-tussen-danira-en-faroek~vd21cc7ff-5e32-452a-bef3-9ecb8f141ed1',
        'md5': '6df10540afc77c90c0b95dc36d607f33',
        'info_dict': {
            'id': '14254336',
            'ext': 'mp4',
            'title': 'Spanning aan ronde tafel in ‘De Verraders’: emoties lopen hoog op tussen Danira en Faroek',
            'channel': 'VTM',
            'channel_id': '867',
            'description': 'md5:4259136f4ac865448bcda48f5cdaf170',
            'duration': 66,
            'genres': ['news'],
            'release_date': '20260824',
            'release_timestamp': 1787589000,
            'series': 'De Verraders',
            'series_id': '3192',
            'tags': ['Televisie', 'Entertainment'],
            'thumbnail': r're:https?://images\.mychannels\.video/imgix/.+',
            'uploader': 'VTM',
            'uploader_id': '74',
        },
        'params': {
            'format': 'b[protocol=https]',
        },
    }, {
        'url': 'https://vtm.be/gast-vernielt-genkse-hotelkamer~ve7534523-279f-4b4d-a5c9-a33ffdbe23e1',
        'only_matching': True,
    }]

    def _download_vtm_webpage(self, url, video_id):
        webpage = self._download_webpage(url, video_id, impersonate=True)
        if 'window.__APOLLO_STATE__' in webpage:
            return webpage
        callback = self._search_regex(
            r'callbackUrl\s*=\s*new URL\(decodeURIComponent\((["\'])(?P<url>(?:(?!\1).)+)\1\)',
            webpage, 'privacy gate callback', group='url', default=None)
        if not callback:
            return webpage
        return self._download_webpage(
            urllib.parse.unquote(callback), video_id,
            note='Confirming privacy gate', impersonate=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_vtm_webpage(url, video_id)
        apollo_state = self._search_json(
            r'window\.__APOLLO_STATE__\s*=', webpage, 'apollo state', video_id)
        mychannels_id = traverse_obj(apollo_state, (
            f'Video:{{"uuid":"{video_id}"}}', 'myChannelsVideo', {str_or_none}, {require('mychannels ID')}))

        return super()._extract_from_mychannels_api(mychannels_id, impersonate=True)
