import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    orderedSet,
    parse_duration,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class RadioCourtoisieIE(InfoExtractor):
    IE_NAME = 'radiocourtoisie'
    IE_DESC = 'Radio Courtoisie'
    _VALID_URL = r'https?://(?:www\.)?(?:radiocourtoisie|rc)\.fr/\d{4}/\d{2}/\d{2}/(?P<id>[\w-]+)'
    _API_BASE = 'https://www.rc.fr'
    _TESTS = [{
        'url': 'https://www.radiocourtoisie.fr/2026/08/31/dou-vient-la-marseillaise/',
        'md5': '59992f2aba9803222a0c86b8d8bfcc1e',
        'info_dict': {
            'id': '231944',
            'ext': 'mp3',
            'display_id': 'dou-vient-la-marseillaise',
            'title': 'D’où vient la Marseillaise ?',
            'description': 'md5:2a5fcf07046c240881c819afd8facf6a',
            'thumbnail': r're:https://media\.rc\.fr/.+',
            'duration': 1000,
            'timestamp': 1788177638,
            'upload_date': '20260831',
            'series': 'Chronique réactionnaire',
            'creators': ['Adeline Yves-Marie'],
        },
    }, {
        'url': 'https://www.rc.fr/2026/08/31/ligne-droite-du-31-aout-2026/',
        'info_dict': {
            'id': '231919',
            'display_id': 'ligne-droite-du-31-aout-2026',
            'title': 'Ligne Droite du 31 août 2026',
            'description': 'md5:3b1bad37f6eb0925678fc610a09b03f1',
            'thumbnail': r're:https://media\.rc\.fr/.+',
            'timestamp': 1788150645,
            'upload_date': '20260831',
            'series': 'Ligne Droite',
            'creators': ['Seze (de) Richard'],
        },
        'playlist_count': 2,
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.rc.fr/2026/08/31/rcmag-du-31-aout-2026-le-pacte-europeen-sur-la-migration-et-les-debats-sur-lidentite-et-la-securite/',
        'only_matching': True,
    }, {
        'url': 'https://www.radiocourtoisie.fr/2023/02/28/ligne-droite-du-28-fevrier-2023/',
        'only_matching': True,
    }]

    def _extract_playlist_id(self, url, slug):
        post = traverse_obj(self._download_json(
            f'{self._API_BASE}/wp-json/wp/v2/sr_playlist', slug,
            'Downloading playlist metadata', fatal=False,
            query={'slug': slug, 'per_page': '1', '_embed': '1'}), (0, {dict}))
        if post:
            return str(post['id']), post, None
        webpage = self._download_webpage(url, slug)
        playlist_id = self._search_regex(
            r'(?:sr_playlist/|data-albums="|postid-)(\d+)', webpage, 'playlist id')
        return playlist_id, None, webpage

    def _parse_html_tracks(self, webpage):
        if not webpage:
            return []
        return orderedSet(re.findall(r'data-audiopath="(https?://[^"]+\.mp3)"', webpage))

    def _real_extract(self, url):
        slug = self._match_id(url)
        playlist_id, post, webpage = self._extract_playlist_id(url, slug)

        tracks_data = self._download_json(
            self._API_BASE, playlist_id, 'Downloading Sonaar playlist JSON', query={
                'load': 'playlist.json',
                'albums': playlist_id,
                'single_playlist': '1',
            }, fatal=False)

        entries = []
        for idx, track in enumerate(traverse_obj(tracks_data, (
                'tracks', lambda _, v: url_or_none(v['mp3']))), 1):
            track_id = traverse_obj(track, ('id', {int_or_none}, {str_or_none})) or f'{playlist_id}-{idx}'
            entries.append({
                'id': track_id,
                'url': track['mp3'],
                'ext': 'mp3',
                'vcodec': 'none',
                **traverse_obj(track, {
                    'title': (('track_title', 'album_title'), {clean_html}, any),
                    'duration': ('length', {parse_duration}),
                    'thumbnail': ('poster', {url_or_none}),
                }),
            })

        if not entries:
            if webpage is None:
                webpage = self._download_webpage(url, playlist_id, fatal=False)
            for idx, mp3_url in enumerate(self._parse_html_tracks(webpage), 1):
                entries.append({
                    'id': f'{playlist_id}-{idx}',
                    'url': mp3_url,
                    'ext': 'mp3',
                    'vcodec': 'none',
                })

        if not entries:
            raise ExtractorError('No audio available for this programme', expected=True)

        info = {k: v for k, v in {
            'id': playlist_id,
            'display_id': slug,
            **traverse_obj(post, {
                'title': ('title', 'rendered', {clean_html}),
                'description': ('excerpt', 'rendered', {clean_html}),
                'timestamp': ('date_gmt', {parse_iso8601}),
                'thumbnail': ((
                    ('_embedded', 'wp:featuredmedia', 0, 'source_url'),
                    ('yoast_head_json', 'og_image', 0, 'url')), {url_or_none}, any),
                'creators': ('_embedded', 'author', ..., 'name', {clean_html}, filter, all, filter),
                'series': (
                    '_embedded', 'wp:term', ...,
                    lambda _, v: (isinstance(v, dict)
                                  and v.get('taxonomy') == 'playlist-category'
                                  and v.get('slug') not in (None, 'podcasts')),
                    'name', {clean_html}, any),
            }),
        }.items() if v is not None}
        if webpage and not info.get('title'):
            info['title'] = self._og_search_title(webpage, default=None)
            info['description'] = self._og_search_description(webpage, default=None)
            info['thumbnail'] = self._og_search_thumbnail(webpage, default=None)

        if len(entries) == 1:
            return {**entries[0], **info}

        return self.playlist_result(entries, multi_video=True, **info)
