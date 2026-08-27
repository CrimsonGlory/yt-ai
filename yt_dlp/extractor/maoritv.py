from .brightcove import BrightcoveNewIE
from .common import InfoExtractor


class MaoriTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:maoritelevision\.com|maoriplus\.co\.nz)/(?:[a-z]{2}/)?(?P<id>(?:shows?|movie|live)/[^?#]+?)(?:/play)?/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.maoriplus.co.nz/show/this-is-home/season-1/episode-1/play',
        'md5': '6502360bd1fe9f7189642f261747e774',
        'info_dict': {
            'id': '6400066584112',
            'ext': 'mp4',
            'title': 'This Is Home, Episode 1',
            'description': 'md5:284deacd4019cdb1af95e837ea5395f4',
            'uploader_id': '1614493167001',
            'upload_date': '20260703',
            'timestamp': 1783038087,
            'duration': 1699.499,
            'thumbnail': r're:https?://.+\.jpg',
            'tags': ['this is home', 'this is home s1'],
        },
    }, {
        'url': 'https://www.maoritelevision.com/shows/korero-mai/S01E054/korero-mai-series-1-episode-54',
        'skip': 'This site has moved to maoriplus.co.nz',
        'info_dict': {
            'id': '4774724855001',
            'ext': 'mp4',
            'title': 'Kōrero Mai, Series 1 Episode 54',
            'upload_date': '20160226',
            'timestamp': 1456455018,
            'description': 'md5:59bde32fd066d637a1a55794c56d8dcb',
            'uploader_id': '1614493167001',
        },
    }, {
        'url': 'https://www.maoriplus.co.nz/movie/marama/play',
        'only_matching': True,
    }, {
        'url': 'https://www.maoriplus.co.nz/live/whakaata-maori/play',
        'only_matching': True,
    }]
    BRIGHTCOVE_URL_TEMPLATE = 'https://players.brightcove.net/%s/%s_default/index.html?videoId=%s'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        brightcove_id = self._search_regex(
            (r'brightcoveId\\?"\s*:\s*\\?"(\d+)', r'data-main-video-id=["\'](\d+)'),
            webpage, 'brightcove id')
        account_id = self._search_regex(
            r'accountId\\?"\s*:\s*\\?"(\d+)', webpage, 'account id',
            default='1614493167001')
        player_id = self._search_regex(
            r'playerId\\?"\s*:\s*\\?"([^"\\]+)', webpage, 'player id',
            default='3kgMijbMH')
        return self.url_result(
            self.BRIGHTCOVE_URL_TEMPLATE % (account_id, player_id, brightcove_id),
            BrightcoveNewIE, brightcove_id)
