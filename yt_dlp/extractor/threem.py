import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    smuggle_url,
)
from ..utils.traversal import traverse_obj


class ThreeMIE(InfoExtractor):
    IE_NAME = '3m'
    IE_DESC = '3M'
    _VALID_URL = r'https?://(?:www\.)?3m\.com/(?:[^/?#]+/)*p/d/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.3m.com/3M/en_US/p/d/b00050763/',
        'md5': '7e1ce9574e029d5fa960ff8ad533fff6',
        'info_dict': {
            'id': '1810572960764717948',
            'ext': 'mp4',
            'title': '3M™ Worktunes™ Connect+ Wireless Hearing Protector',
            'description': '',
            'duration': 43.115,
            'timestamp': 1726854479,
            'upload_date': '20240920',
            'uploader_id': '2635130879001',
            'thumbnail': r're:https?://.+\.jpg',
            'tags': ['3m', 'metallica', 'worktunes', 'connect+', 'connect plus', 'connect',
                     'wireless', 'bluetooth', 'feature and benefits', 'video', 'mp4', 'final'],
        },
        'params': {'format': 'b[protocol=https]'},
    }, {
        'url': 'https://www.3m.com/3M/en_US/p/d/b10013240/',
        'only_matching': True,
    }, {
        'url': 'https://3m.com/3M/en_US/p/d/b00050763/',
        'only_matching': True,
    }]

    _BRIGHTCOVE_URL_TMPL = (
        'https://players.brightcove.net/{account}/{player}_default/index.html?{kind}Id={video_id}')
    # snaps2 client maps gallery videoPlayerId -> Brightcove account/player
    _PLAYER_MAP = {
        '1273986095001': ('1265527901001', 'ryw20m2ml'),
        '1300495914001': ('900160696001', 'r1yj74hXe'),
        '1300793176001': ('782847723001', 'Bkh3xE37x'),
        '1363991536001': ('1231248590001', 'HkONzVnme'),
        '1429744018001': ('1226740749001', 'BJEzbH3Qx'),
        '1490404457001': ('1231248592001', 'SkxfVNnXl'),
        '1493748004001': ('1231248591001', 'rJ83GNh7l'),
        '1494079984001': ('958462695001', 'rkeWX7Vnml'),
        '3234636295001': ('1231248593001', 'SkwmgVnQg'),
        '3255438718001': ('3251589553001', 'Sklbdy4hmg'),
        '3259523391001': ('2635130879001', 'jk66NsK4P'),
    }

    def _extract_player_map(self, webpage, video_id):
        js_url = self._search_regex(
            r'<script[^>]+src=["\'](https?://(?:www\.)?3m\.com/snaps2/snaps2Client\.[^"\']+\.js)',
            webpage, 'snaps2 client', default=None)
        if not js_url:
            return {}
        js = self._download_webpage(js_url, video_id, 'Downloading snaps2 client', fatal=False)
        return {
            catalog_id: (account_id, player_id)
            for catalog_id, account_id, player_id in re.findall(
                r'(\d+):\{dataAccountId:(\d+),dataPlayerId:"([^"]+)"\}', js or '')
        }

    def _resolve_player(self, catalog_id, webpage, video_id, player_map):
        player = player_map.get(catalog_id)
        if player:
            return player
        player_map.update(self._extract_player_map(webpage, video_id))
        player = player_map.get(catalog_id)
        if player:
            return player
        raise ExtractorError(f'Unable to map 3M video player id {catalog_id} to a Brightcove player')

    def _real_extract(self, url):
        product_id = self._match_id(url)
        webpage = self._download_webpage(url, product_id)
        data = self._search_json(
            r'window\.__INITIAL_DATA\s*=', webpage, 'initial data', product_id,
            end_pattern=r';')

        player_map = dict(self._PLAYER_MAP)
        entries = []
        for media in traverse_obj(data, ('media', lambda _, v: v['videoPlayerListId'])):
            video_id = str(media['videoPlayerListId'])
            catalog_id = str(media.get('videoPlayerId') or '')
            account_id, player_id = self._resolve_player(
                catalog_id, webpage, product_id, player_map)
            kind = 'playlist' if (media.get('videoPlayerType') or '').lower() == 'playlist' else 'video'
            bc_url = self._BRIGHTCOVE_URL_TMPL.format(
                account=account_id, player=player_id, kind=kind, video_id=video_id)
            entries.append(self.url_result(
                smuggle_url(bc_url, {'referrer': url}), BrightcoveNewIE, video_id))

        if not entries:
            raise ExtractorError('No video found on this product page', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, product_id,
            traverse_obj(data, ('productDetails', 'name'), 'primaryPageTitle'))
