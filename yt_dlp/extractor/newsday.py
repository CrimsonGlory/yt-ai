from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import smuggle_url
from ..utils.traversal import (
    require,
    traverse_obj,
)


class NewsdayTVIE(InfoExtractor):
    IE_NAME = 'newsday:tv'
    IE_DESC = 'NewsdayTV'
    _VALID_URL = r'https?://(?:(?:www\.)?newsday\.tv|tv\.newsday\.com)/watch/(?:[^/?#]+/)*(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://tv.newsday.com/watch/long-island/li-life/forest-bathing-therapy-life-coach-walking-hiking-pnnbtw8v',
        'md5': '1f8eb803e021d279178b46cd5e083862',
        'info_dict': {
            'id': '6329441191112',
            'ext': 'mp4',
            'title': 'Forest therapy guide Linda Lombardo helps people create a deeper connection with nature',
            'description': 'md5:ed046bd99d36ff29e662548bb0aca2ca',
            'duration': 84.288,
            'timestamp': 1686781815,
            'upload_date': '20230614',
            'uploader_id': '2014288409001',
            'tags': ['3play_processed', 'retirement', 'recreation'],
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://tv.newsday.com/watch/news/health/prescription-opioids-abuse-j7zh19bp',
        'only_matching': True,
    }, {
        'url': 'https://tv.newsday.com/watch/video/ndtv260831-noon-w0dou29z',
        'only_matching': True,
    }, {
        'url': 'https://newsday.tv/watch/long-island/li-life/forest-bathing-therapy-life-coach-walking-hiking-pnnbtw8v',
        'only_matching': True,
    }]
    _ACCOUNT_ID = '2014288409001'
    _PLAYER_ID = 'default'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = traverse_obj(
            self._search_nextjs_data(webpage, display_id),
            ('props', 'pageProps', 'data', 'page', 'leaf',
             ('brightcoveId', 'verticalBrightcoveId'), {str}, filter, any,
             {require('brightcove ID')}))
        return self.url_result(
            smuggle_url(
                f'https://players.brightcove.net/{self._ACCOUNT_ID}/{self._PLAYER_ID}_default/index.html?videoId={video_id}',
                {'referrer': url}),
            BrightcoveNewIE, video_id)
