from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    merge_dicts,
    remove_end,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class FypttIE(InfoExtractor):
    IE_NAME = 'fyptt'
    IE_DESC = 'fyptt.to'
    _VALID_URL = r'https?://(?:www\.)?fyptt\.to/(?P<id>\d+)/(?P<display_id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        # Video.js player (fypttstr.php)
        'url': 'https://fyptt.to/6797/thots-just-want-to-give-their-viewers-some-nice-live-flashes-on-friday/',
        'md5': '3fdbaac6807383b03f4db8ef514311e4',
        'info_dict': {
            'id': '6797',
            'ext': 'mp4',
            'display_id': 'thots-just-want-to-give-their-viewers-some-nice-live-flashes-on-friday',
            'title': 'Thots just want to give their viewers some nice live flashes on Friday',
            'description': 'They do this every Friday.',
            'thumbnail': r're:https?://fyptt\.to/wp-content/uploads/.+\.jpg',
            'timestamp': 1650326400,
            'upload_date': '20220419',
            'age_limit': 18,
        },
    }, {
        # JWPlayer (fypttjwstr.php)
        'url': 'https://fyptt.to/10382/beautiful-livestream-tits-and-nipples-slip-from-girls-who-loves-talking-with-their-viewers/',
        'md5': '7a032d1a98d6e3426d794cce2bae72fd',
        'info_dict': {
            'id': '10382',
            'ext': 'mp4',
            'display_id': 'beautiful-livestream-tits-and-nipples-slip-from-girls-who-loves-talking-with-their-viewers',
            'title': 'Beautiful livestream tits and nipples \'slip\' from girls who loves talking with their viewers',
            'description': 'md5:1a55540669158e07249aa4d4ca3cc65b',
            'thumbnail': r're:https?://fyptt\.to/wp-content/uploads/.+\.jpg',
            'timestamp': 1670889600,
            'upload_date': '20221213',
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.fyptt.to/23697/nude-girl-dancing-in-bathroom-mirror-selfie-with-long-dark-hair-swaying-and-round-ass-shaking-hot/',
        'only_matching': True,
    }]

    def _extract_player_info(self, player_url, video_id):
        player_page = self._download_webpage(player_url, video_id, 'Downloading player')

        jwplayer_info = self._extract_jwplayer_data(
            player_page, video_id, require_title=False)
        if isinstance(jwplayer_info, dict) and (jwplayer_info.get('formats') or jwplayer_info.get('url')):
            return jwplayer_info

        video_url = url_or_none(unescapeHTML(self._search_regex(
            (r'<source[^>]+\bsrc=["\']([^"\']+)',
             r'(https?://stream\.fyptt\.to/[^"\'\s]+)'),
            player_page, 'video url')))
        return {
            'url': video_url,
            'ext': 'mp4',
            'http_headers': {'Referer': player_url},
        }

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        player_url = urljoin(url, unescapeHTML(self._search_regex(
            r'<iframe[^>]+\bsrc=["\']([^"\']+fyptt(?:jw)?str\.php[^"\']*)',
            webpage, 'player url')))
        info = self._extract_player_info(player_url, video_id)
        if not info.get('url') and not info.get('formats'):
            raise ExtractorError('No video source found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)
        title = (
            json_ld.get('title')
            or remove_end(self._og_search_title(webpage, default=''), ' - FYPTT')
            or remove_end(self._html_extract_title(webpage, default=''), ' - FYPTT')
            or None)

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'age_limit': 18,
        }, json_ld, info)
