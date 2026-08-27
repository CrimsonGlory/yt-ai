from .common import InfoExtractor
from .nexx import NexxIE


class FunkIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|origin|play)\.)?funk\.net/(?:channel|playlist)/[^/?#]+/(?P<display_id>[0-9a-z-]+)-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://play.funk.net/channel/mrwissen2go-8423/was-waere-wenn-hitler-den-krieg-gewonnen-haette-1509818',
        'md5': '3bb00412af77a0014cfb980a814fd88d',
        'info_dict': {
            'id': '1509818',
            'ext': 'mp4',
            'title': 'Was wäre, wenn Hitler den Krieg gewonnen hätte?',
            'alt_title': 'Was wäre, wenn Hitler den Krieg gewonnen hätte?',
            'description': 'md5:f4ef9733bb98628f34684691b02db6b3',
            'timestamp': 1525263173,
            'upload_date': '20180502',
            'duration': 842,
            'cast': ['Objektiv Media GmbH'],
            'thumbnail': 'https://assets.nexx.cloud/media/79/77/30/T3GNU5YT0GF2D5MxL.jpg',
            'display_id': 'was-waere-wenn-hitler-den-krieg-gewonnen-haette',
            'season_number': 0,
            'season': 'Season 0',
            'episode_number': 0,
            'episode': 'Episode 0',
        },
        'params': {
            'format': 'best[protocol=http]',
        },
    }, {
        'url': 'https://www.funk.net/channel/ba-793/die-lustigsten-instrumente-aus-dem-internet-teil-2-1155821',
        'skip': 'video gone',
        'md5': '8610449476156f338761a75391b0017d',
        'info_dict': {
            'id': '1155821',
            'ext': 'mp4',
            'title': 'Die LUSTIGSTEN INSTRUMENTE aus dem Internet - Teil 2',
            'description': 'md5:2a03b67596eda0d1b5125c299f45e953',
            'timestamp': 1514507395,
            'upload_date': '20171229',
            'duration': 426.0,
            'cast': ['United Creators PMB GmbH'],
            'thumbnail': 'https://assets.nexx.cloud/media/75/56/79/3YKUSJN1LACN0CRxL.jpg',
            'display_id': 'die-lustigsten-instrumente-aus-dem-internet-teil-2',
            'alt_title': 'Die LUSTIGSTEN INSTRUMENTE aus dem Internet Teil 2',
            'season_number': 0,
            'season': 'Season 0',
            'episode_number': 0,
            'episode': 'Episode 0',
        },
    }, {
        'url': 'https://www.funk.net/playlist/neuesteVideos/kameras-auf-dem-fusion-festival-1618699',
        'only_matching': True,
    }, {
        'url': 'https://play.funk.net/playlist/neuesteVideos/george-floyd-wenn-die-polizei-toetet-der-fall-2004391',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, nexx_id = self._match_valid_url(url).groups()
        return {
            '_type': 'url_transparent',
            'url': f'nexx:741:{nexx_id}',
            'ie_key': NexxIE.ie_key(),
            'id': nexx_id,
            'display_id': display_id,
        }
