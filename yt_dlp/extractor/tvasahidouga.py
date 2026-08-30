from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    int_or_none,
    smuggle_url,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class TVAsahiDougaIE(InfoExtractor):
    IE_NAME = 'douga.tv-asahi.co.jp'
    IE_DESC = 'テレ朝動画'
    _VALID_URL = r'https?://(?:www\.)?douga\.tv-asahi\.co\.jp/program/\d+-\d+/(?P<id>\d+)'
    _GEO_COUNTRIES = ['JP']
    _TESTS = [{
        'url': 'https://douga.tv-asahi.co.jp/program/13510-13509/13698?auto=t',
        'md5': '08e706e764a3e8b564f32a4af51c4db8',
        'info_dict': {
            'id': '6219296002001',
            'ext': 'mp4',
            'display_id': '13698',
            'title': 'ドラえもん タイムふろしき',
            'description': 'md5:1b69bf0ddcf48659b4ceec6f48e0ff8b',
            'duration': 662,
            'thumbnail': r're:https?://douga\.tv-asahi\.co\.jp/uploads/attachment/.+',
            'timestamp': 1425211200,
            'upload_date': '20150301',
            'uploader_id': '5490902212001',
            'series': 'ドラえもん',
            'series_id': '13510',
            'season_id': '13509',
            'episode': 'タイムふろしき',
            'episode_id': '13698',
            'episode_number': 192,
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://douga.tv-asahi.co.jp/program/13510-13509/13698',
        'only_matching': True,
    }]
    _ACCOUNT_ID = '5490902212001'
    _PLAYER_ID = 'ZmkjS3aKkB'
    _BC_URL_TMPL = 'https://players.brightcove.net/{account}/{player}_default/index.html?videoId={video_id}'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        app = self._search_json(r'window\.app\s*=', webpage, 'app data', video_id)
        meta = traverse_obj(
            app, ('falcorCache', 'metas', video_id, 'value', {dict}, {require('episode metadata')}))

        def parse_related(value):
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                return self._parse_json(value, video_id, fatal=False)

        brightcove_id = traverse_obj(meta, (
            'values', 'related_media', {parse_related}, 'ovp_video_id',
            {str_or_none}, {require('Brightcove video ID')}))
        account_id = traverse_obj(app, (
            'reactContext', 'models', 'config', 'data', 'videocloud',
            'account_id', {str_or_none})) or self._ACCOUNT_ID
        player_id = traverse_obj(app, (
            'reactContext', 'models', 'config', 'data', 'videocloud',
            'player_id', {str})) or self._PLAYER_ID

        return {
            '_type': 'url_transparent',
            'url': smuggle_url(self._BC_URL_TMPL.format(
                account=account_id, player=player_id, video_id=brightcove_id), {
                'geo_countries': ['JP'],
                'referrer': url,
            }),
            'ie_key': BrightcoveNewIE.ie_key(),
            'id': brightcove_id,
            'display_id': video_id,
            **traverse_obj(meta, {
                'title': (('name', ('values', 'avails_EpisodeTitleDisplayUnlimited')), {str}, any),
                'description': ((
                    ('values', 'evis_EpisodeLongSynopsis'),
                    'description',
                ), {str}, any),
                'thumbnail': ('thumbnail_url', {url_or_none}),
                'duration': ('values', 'duration', {int_or_none}),
                'timestamp': ('publish_start_at', {unified_timestamp}),
                'series': ('values', 'parents_series', 'avails_SeriesTitleDisplayUnlimited', {str}),
                'series_id': ('values', 'parents_series', 'id', {str_or_none}),
                'season_id': ('values', 'parents_season', 'id', {str_or_none}),
                'episode': ('values', 'avails_EpisodeTitleDisplayUnlimited', {str}),
                'episode_number': ('values', 'avails_EpisodeNumber', {int_or_none}),
                'episode_id': ('id', {str_or_none}),
            }),
        }
