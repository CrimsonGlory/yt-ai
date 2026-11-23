from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    jwt_decode_hs256,
    parse_duration,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


def result_from_props(props):
    return {
        **traverse_obj(props, {
            'id': ('_id', {str}),
            'title': ('title', {str}),
            'url': ('mediaURL', {url_or_none}),
            'description': ('description', {clean_html}),
            'thumbnail': ('image', {jwt_decode_hs256}, 'url', {url_or_none}),
            'timestamp': ('timestamp', {int_or_none}),
            'duration': ('duration', {int_or_none}),
        }),
        'ext': 'mp3',
        'vcodec': 'none',
    }


class PodbayFMIE(InfoExtractor):
    _VALID_URL = r'https?://podbay\.fm/p/[^/?#]+/e/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://podbay.fm/p/behind-the-bastards/e/1647338400',
        'skip': 'Cloudflare challenge',
        'md5': '3d4642297b6e20c4e7d8f761c05a5bff',
        'info_dict': {
            'id': '618e55de-c833-5a1d-8ada-af996f319e8a',
            'ext': 'mp3',
            'title': 'Part One: Kissinger',
            'description': 'md5:3a217f5a6a7c36ffdd57f31287f0723a',
            'duration': 5001,
            'thumbnail': 'md5:b5a01d84c880f9480dcf1f6e58f5d9f7',
            'timestamp': 1647338400,
            'upload_date': '20220315',
        },
    }]

    def _real_extract(self, url):
        episode_id = self._match_id(url)
        webpage = self._download_webpage(url, episode_id, impersonate=True)
        data = self._search_nextjs_data(webpage, episode_id)
        return result_from_props(data['props']['pageProps']['episode'])


class PodbayFMChannelIE(InfoExtractor):
    _VALID_URL = r'https?://podbay\.fm/p/(?P<id>[^/?#]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://podbay.fm/p/behind-the-bastards',
        'info_dict': {
            'id': 'behind-the-bastards',
            'title': 'Behind the Bastards',
        },
        'playlist_mincount': 21,
    }]
    _ITUNES_NS = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

    @staticmethod
    def _results_from_page(channel_id, page):
        return [{
            **result_from_props(e),
            'extractor': PodbayFMIE.IE_NAME,
            'extractor_key': PodbayFMIE.ie_key(),
            # somehow they use timestamps as the episode identifier
            'webpage_url': f'https://podbay.fm/p/{channel_id}/e/{e["timestamp"]}',
        } for e in page['episodes']]

    def _entries_from_rss(self, channel_id, rss):
        for item in rss.findall('./channel/item'):
            enclosure = item.find('enclosure')
            media_url = url_or_none(None if enclosure is None else enclosure.get('url'))
            if not media_url:
                continue
            timestamp = unified_timestamp(item.findtext('pubDate'))
            episode_id = (item.findtext('guid') or '').strip() or str(timestamp or '')
            if not episode_id:
                continue
            duration_raw = item.findtext('itunes:duration', namespaces=self._ITUNES_NS)
            image = item.find('itunes:image', self._ITUNES_NS)
            yield {
                'id': episode_id,
                'title': item.findtext('title'),
                'url': media_url,
                'description': clean_html(item.findtext('description')),
                'thumbnail': url_or_none(None if image is None else image.get('href')),
                'timestamp': timestamp,
                'duration': int_or_none(duration_raw) or parse_duration(duration_raw),
                'ext': 'mp3',
                'vcodec': 'none',
                'extractor': PodbayFMIE.IE_NAME,
                'extractor_key': PodbayFMIE.ie_key(),
                'webpage_url': (
                    f'https://podbay.fm/p/{channel_id}/e/{timestamp}' if timestamp else None),
            }

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        webpage = self._download_webpage(url, channel_id, impersonate=True)
        podcast = traverse_obj(
            self._search_nextjs_data(webpage, channel_id),
            ('props', 'pageProps', 'podcast', {dict})) or {}

        # /api/podcast is HTTP 410 and tRPC podcast.getBySlug times out.
        feed_url = url_or_none(podcast.get('feed_url'))
        rss = self._download_xml(
            feed_url, channel_id, 'Downloading podcast RSS', fatal=False) if feed_url else None
        entries = list(self._entries_from_rss(channel_id, rss)) if rss is not None else []
        if not entries:
            entries = self._results_from_page(channel_id, podcast)

        return self.playlist_result(entries, channel_id, podcast.get('title'))
