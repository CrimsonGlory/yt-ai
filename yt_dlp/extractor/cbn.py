import urllib.parse

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_qs,
    smuggle_url,
    update_url_query,
)
from ..utils.traversal import traverse_obj


class CBNIE(InfoExtractor):
    IE_NAME = 'cbn'
    IE_DESC = 'CBN'
    _VALID_URL = r'''(?x)
        https?://(?:www1?\.)?cbn\.com/
        (?:
            video/(?P<video_slug>[^?#]+?)/*
            |(?P<show_slug>700club)/?
            |sites/all/libraries/html5player/html5player\.php
        )
        (?:[?#]|$)
    '''
    _TESTS = [{
        'url': 'https://cbn.com/video/shows/700-club-august-24-2026',
        'md5': '5f6a648674a22b994a1c49ba17d38f08',
        'info_dict': {
            'id': '6403968437112',
            'ext': 'mp4',
            'title': 'The 700 Club - August 24, 2026',
            'description': 'md5:cf1cb8b14755aaccba523bcc8734341f',
            'duration': 3021.009,
            'timestamp': 1787588644,
            'upload_date': '20260824',
            'uploader_id': '734546207001',
            'thumbnail': r're:https?://.+\.jpg',
            'tags': list,
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://cbn.com/video/shows/700-club-canada-august-28-2026',
        'only_matching': True,
    }, {
        'url': 'https://cbn.com/video/live-cbn-news-channel',
        'only_matching': True,
    }, {
        'url': 'https://cbn.com/700club?v=1',
        'only_matching': True,
    }, {
        'url': 'https://www1.cbn.com/sites/all/libraries/html5player/html5player.php?videoId=6403968437112',
        'only_matching': True,
    }, {
        'url': 'https://www.cbn.com/video/shows/700-club-august-24-2026',
        'only_matching': True,
    }]
    _ACCOUNT_ID = '734546207001'
    _PLAYER_ID = 'TADSYViJy'
    _HTML5_PLAYER_ID = 'mpS2K0BKQ'
    _BC_URL_TMPL = (
        'https://players.brightcove.net/{account}/{player}_default/index.html?{kind}Id={bc_id}')

    def _brightcove_result(self, bc_id, url, account_id=None, player_id=None, is_playlist=False):
        bc_url = self._BC_URL_TMPL.format(
            account=account_id or self._ACCOUNT_ID,
            player=player_id or self._PLAYER_ID,
            kind='playlist' if is_playlist else 'video',
            bc_id=bc_id)
        return self.url_result(
            smuggle_url(bc_url, {'referrer': url}), BrightcoveNewIE, bc_id)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        qs = parse_qs(url)
        display_id = (
            mobj.group('video_slug')
            or mobj.group('show_slug')
            or traverse_obj(qs, ('videoId', 0))
            or 'player')

        query_video_id = traverse_obj(qs, ('videoId', 0, {str}))
        if query_video_id:
            return self._brightcove_result(
                query_video_id, url,
                account_id=traverse_obj(qs, ('bcaccount', 0, {str})),
                player_id=traverse_obj(qs, ('bcplayerid', 0, {str})) or self._HTML5_PLAYER_ID)

        video_slug = mobj.group('video_slug')
        if video_slug:
            parsed = urllib.parse.urlparse(url)
            node = self._download_json(
                update_url_query(
                    parsed._replace(query='', fragment='').geturl(), {'_format': 'json'}),
                display_id, fatal=False)
            video_id = traverse_obj(node, ('field_brightcove_video_id', 0, 'value', {str}))
            if video_id:
                return self._brightcove_result(video_id, url)

        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            r'\bdata-video-id=["\']?(\d+)', webpage, 'brightcove video id', default=None)
        playlist_id = self._search_regex(
            r'\bdata-playlist-id=["\']?(\d+)', webpage, 'brightcove playlist id', default=None)
        account_id = self._search_regex(
            r'\bdata-account=["\']?(\d+)', webpage, 'brightcove account', default=None)
        player_id = self._search_regex(
            r'\bdata-player=["\']([^"\']+)', webpage, 'brightcove player', default=None)
        if not video_id:
            params = self._parse_json(self._search_regex(
                r'var\s+cbn_media_parameters\s*=\s*JSON\.parse\((["\'])(?P<json>.+?)\1\)',
                webpage, 'media parameters', default='{}', group='json'),
                display_id, fatal=False)
            video_id = video_id or traverse_obj(params, ('videoId', {str}))
            account_id = account_id or traverse_obj(params, ('bcaccount', {str}))
            player_id = player_id or traverse_obj(params, ('bcplayerid', {str}))

        if video_id:
            return self._brightcove_result(
                video_id, url, account_id=account_id, player_id=player_id)
        if playlist_id:
            return self._brightcove_result(
                playlist_id, url, account_id=account_id, player_id=player_id, is_playlist=True)
        raise ExtractorError('Unable to extract Brightcove video', expected=True)
