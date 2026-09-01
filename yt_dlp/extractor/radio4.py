from .common import InfoExtractor
from ..utils import (
    clean_html,
    float_or_none,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class Radio4IE(InfoExtractor):
    IE_NAME = 'radio4'
    IE_DESC = 'Radio4'
    _VALID_URL = r'https?://(?:www\.)?radio4\.dk/podcasts/[\w-]+/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://radio4.dk/podcasts/radio4-morgen/radio4-morgen-13-juni-kl-6-7',
        'md5': 'fb5db7f301b1afa00debe0e15b1f8376',
        'info_dict': {
            'id': 'a44b5db4-b5c7-426b-a24f-aeb30057f864',
            'ext': 'mp3',
            'display_id': 'radio4-morgen-13-juni-kl-6-7',
            'title': 'Radio4 Morgen - 13. juni kl. 6-7',
            'description': 'md5:600f939a375da110e0a89e8908d290b8',
            'duration': 3300.598,
            'timestamp': 1655093100,
            'upload_date': '20220613',
            'thumbnail': r're:https://radio4data\.imgix\.net/.+',
            'series': 'Morgen',
            'series_id': 'bd5a9b30-6d36-4dc7-bb2b-ad4a0088d655',
            'channel': 'Morgen',
            'channel_id': 'bd5a9b30-6d36-4dc7-bb2b-ad4a0088d655',
            'channel_url': 'https://radio4.dk/podcasts/radio4-morgen',
            'categories': ['News'],
        },
    }, {
        'url': 'https://www.radio4.dk/podcasts/radio4-morgen/radio4-morgen-13-juni-kl-6-7',
        'only_matching': True,
    }, {
        'url': 'https://radio4.dk/podcasts/radio4-morgen/tirsdag-d-1-september-kl-6-7',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage_url = url.split('#')[0].split('?')[0].rstrip('/')
        nuxt = self._resolve_nuxt_array(self._download_json(
            f'{webpage_url}/_payload.json', display_id, 'Downloading Nuxt payload'), display_id)

        episode = traverse_obj(nuxt, (
            'data', lambda _, v: isinstance(v, dict) and url_or_none(v.get('audioUrl')), any)) or {}
        program = traverse_obj(nuxt, (
            'data', lambda _, v: isinstance(v, dict) and v.get('name') and v.get('slug') and not v.get('audioUrl'),
            any)) or {}

        audio_url = traverse_obj(episode, ('audioUrl', {url_or_none}))
        if not audio_url:
            webpage = self._download_webpage(url, display_id)
            audio_url = self._search_regex(
                r'<a[^>]+\bclass="download"[^>]+\bhref="(https?://[^"]+)"',
                webpage, 'audio URL')

        return {
            'id': traverse_obj(episode, ('id', {str})) or display_id,
            'display_id': display_id,
            'url': audio_url,
            'vcodec': 'none',
            **traverse_obj(program, {
                'series': ('name', {clean_html}, filter),
                'series_id': ('id', {str}),
                'channel': ('name', {clean_html}, filter),
                'channel_id': ('id', {str}),
                'channel_url': ('url', {url_or_none}),
                'categories': ('categories', ..., {clean_html}, filter, all, filter),
                'thumbnail': (('posterUrl', 'artworkUrl'), {url_or_none}, any),
            }),
            **traverse_obj(episode, {
                'title': ('title', {clean_html}, filter),
                'description': ('description', {clean_html}, filter),
                'duration': ('duration', {float_or_none}),
                'timestamp': ('published', {parse_iso8601}),
                'thumbnail': ('imageUrl', {url_or_none}),
                'tags': ('tags', ..., {clean_html}, filter, all, filter),
                'episode_number': ('episode', {int_or_none}),
                'season_number': ('season', {int_or_none}),
            }),
        }
