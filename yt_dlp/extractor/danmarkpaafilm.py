from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    get_element_by_class,
    int_or_none,
    parse_duration,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class DanmarkPaaFilmIE(InfoExtractor):
    IE_NAME = 'danmarkpaafilm'
    IE_DESC = 'Danmark på Film'
    _VALID_URL = r'https?://(?:www\.)?danmarkpaafilm\.dk/(?P<kind>film|klip|popup)/(?P<id>[^/?#]+)'
    _TESTS = [
        {
            'url': 'https://www.danmarkpaafilm.dk/film/det-perfekte-menneske',
            'md5': 'b0d715a8024f781d3cb280ca99b07d86',
            'info_dict': {
                'id': '52715',
                'ext': 'mp4',
                'display_id': 'det-perfekte-menneske',
                'title': 'Det perfekte menneske',
                'description': 'Jørgen Leth om sin kortfilmklassiker: Et smukt ungt par fungerer som demonstrationsobjekter. Vi skal se, hvordan et menneske bliver til i kraft af de roller, der tildeles det.',
                'thumbnail': r're:https?://www\.danmarkpaafilm\.dk/.+',
                'duration': 780,
                'release_year': 1968,
                'creators': ['Jørgen Leth'],
            },
            'params': {'format': 'bv'},
        },
        {
            'url': 'https://www.danmarkpaafilm.dk/klip/glimt-fra-roedding-hoejskole',
            'only_matching': True,
        },
        {
            'url': 'https://www.danmarkpaafilm.dk/popup/52715/L2ZpbG0vZGV0LXBlcmZla3RlLW1lbm5lc2tl?universeId=8144',
            'only_matching': True,
        },
        {
            'url': 'https://www.danmarkpaafilm.dk/film/inuit',
            'only_matching': True,
        },
    ]
    _PLAYER_IFRAME_RE = r'<iframe[^>]+src=(["\'])(?P<url>https://dbcamsapi\.azurewebsites\.net/play/[^"\']+)\1'
    _M3U8_RE = r'(["\'])(?P<url>https://dbcamsapi\.azurewebsites\.net/aespxy/[^"\']+\.m3u8(?:\?[^"\']*)?)\1'

    def _real_extract(self, url):
        kind, display_id = self._match_valid_url(url).group('kind', 'id')
        webpage = self._download_webpage(url, display_id, impersonate=True)

        settings = self._search_json(
            r'<script[^>]+data-drupal-selector="drupal-settings-json"[^>]*>',
            webpage,
            'drupal settings',
            display_id,
            fatal=False,
        )
        node_id = (
            self._html_search_regex(r'data-(?:node-id|history-node-id)="(\d+)"', webpage, 'node id', default=None)
            or (display_id if kind == 'popup' and display_id.isdigit() else None)
            or self._search_regex(r'"currentPath"\s*:\s*"node/(\d+)"', webpage, 'node id')
        )
        universe_id = traverse_obj(settings, ('dfi', 'universe', {str})) or '8144'

        embed = self._download_webpage(
            f'https://www.danmarkpaafilm.dk/player-playback-url/{node_id}/{universe_id}',
            node_id,
            note='Downloading playback embed',
            impersonate=True,
        )
        play_url = url_or_none(
            unescapeHTML(self._search_regex(self._PLAYER_IFRAME_RE, embed, 'DBC player iframe', group='url')),
        )
        if not play_url:
            raise ExtractorError('No DBC AMS player embed found', expected=True)

        player = self._download_webpage(play_url, node_id, note='Downloading DBC AMS player')
        m3u8_url = url_or_none(unescapeHTML(self._search_regex(self._M3U8_RE, player, 'HLS URL', group='url')))
        if not m3u8_url:
            raise ExtractorError('No HLS manifest in DBC AMS player', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, node_id, 'mp4', m3u8_id='hls', headers={'Referer': play_url},
        )

        hero = clean_html(get_element_by_class('header__hero__text', webpage))
        duration = parse_duration(self._search_regex(r'(\d+:\d+)\s*min', hero or '', 'duration', default=None))
        if duration is None:
            duration = parse_duration(self._search_regex(r'(\d+\s*min\.?)', hero or '', 'duration', default=None))
        creator = self._search_regex(r'^(.+?),\s*(?:19|20)\d{2}\b', hero or '', 'creator', default=None)

        return {
            'id': node_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'release_year': int_or_none(
                self._search_regex(r'\b((?:19|20)\d{2})\b', hero or '', 'release year', default=None),
            ),
            'creators': [creator] if creator else None,
            'formats': formats,
            'subtitles': subtitles,
        }
