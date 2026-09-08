from .common import InfoExtractor
from .dailymotion import DailymotionIE
from ..utils.traversal import require, traverse_obj


class GameStarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?game(?P<site>pro|star)\.de/videos/.*,(?P<id>[0-9]+)\.html'
    _TESTS = [{
        'url': 'https://www.gamestar.de/videos/der-sargnagel-fuer-aaa-gaming,142100.html',
        'md5': 'a0d30b989792eba5563739bc450a139b',
        'info_dict': {
            'id': 'k3Ccwm2JjIDC5wJuJSW',
            'ext': 'mp4',
            'title': 'Der Sargnagel für AAA-Gaming',
            'description': 'md5:42d07c5f43d20902e0d24ab99973d522',
            'thumbnail': r're:https?://s\d+\.dmcdn\.net/v/',
            'duration': 3421,
            'timestamp': 1788667200,
            'upload_date': '20260906',
            'uploader': 'GameStar',
            'uploader_id': 'x2mvqg3',
            'age_limit': 0,
            'view_count': int,
            'like_count': int,
            'tags': list,
        },
        # Dailymotion HLS fMP4 init fragment is <10KiB in --test mode
        'file_minsize': None,
        'params': {'format': 'hls-480'},
        'add_ie': ['Dailymotion'],
    }, {
        'url': 'http://www.gamestar.de/videos/trailer,3/hobbit-3-die-schlacht-der-fuenf-heere,76110.html',
        'only_matching': True,
    }, {
        'url': 'http://www.gamepro.de/videos/top-10-indie-spiele-fuer-nintendo-switch-video-tolle-nindies-games-zum-download,95316.html',
        'only_matching': True,
    }, {
        'url': 'http://www.gamestar.de/videos/top-10-indie-spiele-fuer-nintendo-switch-video-tolle-nindies-games-zum-download,95316.html',
        'only_matching': True,
    }, {
        'url': 'https://www.gamestar.de/videos/im-neuen-gameplay-trailer-von-the-expanse-osiris-reborn-spruehen-die-funken,141896.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate='firefox')

        player = self._search_json(
            r'setupVideoPlayer\(', webpage, 'player config', video_id)
        dm_id = traverse_obj(player, ('player', 'dmId', {str}, {require('dailymotion id')}))

        return self.url_result(
            f'https://www.dailymotion.com/video/{dm_id}',
            ie=DailymotionIE, video_id=dm_id)
