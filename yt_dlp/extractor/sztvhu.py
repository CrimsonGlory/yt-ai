from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import ExtractorError


class SztvHuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:sztv|tvszombathely)\.hu/(?:[^/?#]+)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.sztv.hu/hirado/hirado-2026-augusztus-28',
        'md5': '44ad9dd7e6c9f87aa9602b396b4b11de',
        'info_dict': {
            'id': '2SEHYeO2YaM',
            'ext': 'mp4',
            'title': 'Híradó - 2026. augusztus 28.',
            'description': 'md5:c59a96754a829885bc964a9c1a7db481',
            'duration': 1004,
            'uploader': 'Szombathelyi Televízió',
            'uploader_id': '@szombathelyitv',
            'uploader_url': 'https://www.youtube.com/@szombathelyitv',
            'channel': 'Szombathelyi Televízió',
            'channel_id': 'UCXyrIcogt9R0y0nPltSdcuA',
            'channel_url': 'https://www.youtube.com/channel/UCXyrIcogt9R0y0nPltSdcuA',
            'channel_follower_count': int,
            'view_count': int,
            'age_limit': 0,
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['News & Politics'],
            'tags': 'count:8',
            'timestamp': 1787932806,
            'upload_date': '20260828',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
        ],
    }, {
        'url': 'http://sztv.hu/hirek/cserkeszek-nepszerusitettek-a-kornyezettudatos-eletmodot-a-savaria-teren-20130909',
        'skip': 'native VOD player removed; videos are now YouTube embeds',
        'md5': 'a6df607b11fb07d0e9f2ad94613375cb',
        'info_dict': {
            'id': '20130909',
            'ext': 'mp4',
            'title': 'Cserkészek népszerűsítették a környezettudatos életmódot a Savaria téren',
            'description': 'A zöld nap játékos ismeretterjesztő programjait a Magyar Cserkész Szövetség szervezte, akik az ország nyolc városában adják át tudásukat az érdeklődőknek. A PET...',
        },
    }, {
        'url': 'https://www.sztv.hu/hirek/a-gyongyosherman-szentkiraly-ujperint-derbit-sok-helyzet-jellemezte',
        'only_matching': True,
    }, {
        'url': 'https://www.sztv.hu/online/elo-adas',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        youtube_id = self._search_regex(
            r'(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/)|youtu\.be/)([0-9A-Za-z_-]{11})',
            webpage, 'youtube id', default=None)
        if not youtube_id:
            raise ExtractorError('No video found', expected=True)

        return self.url_result(
            f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id)
