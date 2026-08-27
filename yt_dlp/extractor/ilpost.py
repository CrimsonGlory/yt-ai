from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    int_or_none,
    str_or_none,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class IlPostIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ilpost\.it/(?:episodes|(?:podcasts/[^/?#]+))/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.ilpost.it/episodes/1-avis-akvasas-ka/',
        'md5': '43649f002d85e1c2f319bb478d479c40',
        'info_dict': {
            'id': '2972047',
            'ext': 'mp3',
            'display_id': '1-avis-akvasas-ka',
            'title': '1. Avis akvasas ka',
            'description': 'md5:57d147951b522c92095f64e28570cf4a',
            'url': 'https://www.ilpost.it/wp-content/uploads/2023/12/28/1703781217-l-invasione-pt1-v6.mp3',
            'thumbnail': 'https://www.ilpost.it/wp-content/uploads/2023/12/22/1703238848-copertina500x500.jpg',
            'timestamp': 1703835014,
            'upload_date': '20231229',
            'duration': 2495.0,
            'availability': 'public',
            'series': "L'invasione",
            'series_id': '235598',
        },
    }, {
        'url': 'https://www.ilpost.it/podcasts/l-invasione/1-avis-akvasas-ka',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        episode = traverse_obj(self._search_nextjs_data(webpage, display_id), (
            'props', 'pageProps', 'data', 'data', 'episode', 'data', 0, {dict}))
        if not episode:
            raise ExtractorError('Episode could not be extracted')

        return {
            'display_id': display_id,
            'vcodec': 'none',
            **traverse_obj(episode, {
                'id': ('id', {str_or_none}),
                'title': ('title', {unescapeHTML}),
                'description': ('content_html', {clean_html}),
                'url': ('episode_raw_url', {url_or_none}),
                'thumbnail': ('image', {url_or_none}),
                'timestamp': ('timestamp', {int_or_none}),
                'duration': ('milliseconds', {float_or_none(scale=1000)}),
                'availability': ('access_level', {lambda v: 'public' if v == 'all' else 'subscriber_only'}),
                'series_id': ('parent', 'id', {str_or_none}),
                'series': ('parent', 'title', {str}),
            }),
        }
