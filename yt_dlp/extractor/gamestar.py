from .common import InfoExtractor
from .dailymotion import DailymotionIE
from ..utils.traversal import require, traverse_obj


class GameStarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?game(?P<site>pro|star)\.de/videos/.*,(?P<id>[0-9]+)\.html'
    _TESTS = [{
        'url': 'http://www.gamestar.de/videos/trailer,3/hobbit-3-die-schlacht-der-fuenf-heere,76110.html',
        'md5': '3a1b2d7494e6f3230a6835038436d8ac',
        'info_dict': {
            'id': 'k4b9wq1ir4jtBxy5fgF',
            'ext': 'mp4',
            'title': 'Hobbit 3: Die Schlacht der Fünf Heere - Teaser-Trailer zum dritten Teil',
            'description': 'md5:d543730d27e0dc4e839cee9d219f42a8',
            'thumbnail': r're:https?://s\d+\.dmcdn\.net/v/',
            'duration': 17,
            'timestamp': 1655790897,
            'upload_date': '20220621',
            'uploader': 'GameStar',
            'uploader_id': 'x2mvqg3',
            'age_limit': 0,
            'view_count': int,
            'like_count': int,
            'tags': ['Trailer', 'Video'],
        },
        'params': {'format': 'hls-720'},
        'add_ie': ['Dailymotion'],
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
