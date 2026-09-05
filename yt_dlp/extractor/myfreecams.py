from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    UserNotLive,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class MyFreeCamsIE(InfoExtractor):
    IE_DESC = 'MyFreeCams'
    _VALID_URL = r'''(?x)
        https?://(?:(?:www|app|m|share|profiles)\.)?myfreecams\.com/
        (?:(?:room|chats|models)/)?\#?
        (?!(?:models|php|tags|login|signup|accounts|explore|search|index|albums|privacy|terms)(?:[/?#]|$))
        (?P<id>[A-Za-z][\w.-]{1,})
        /?(?:[?#].*)?$
    '''
    _TESTS = [{
        'url': 'https://www.myfreecams.com/#erikasmagic',
        'skip': 'not currently live',
        'info_dict': {
            'id': 'erikasmagic',
            'ext': 'mp4',
            'title': r're:GoddessErika \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
            'age_limit': 18,
            'is_live': True,
            'live_status': 'is_live',
            'thumbnail': r're:https://img\.mfcimg\.com/.+',
            'uploader': 'GoddessErika',
            'uploader_id': '13615307',
        },
    }, {
        'url': 'https://app.myfreecams.com/room/erikasmagic',
        'only_matching': True,
    }, {
        'url': 'https://share.myfreecams.com/GoddessErika',
        'only_matching': True,
    }, {
        'url': 'https://m.myfreecams.com/chats/erikasmagic',
        'only_matching': True,
    }, {
        'url': 'https://profiles.myfreecams.com/GoddessErika',
        'only_matching': True,
    }]

    _PRIVATE_STATUS = {
        2: 'Model is currently away',
        12: 'Model is currently in a private show',
        13: 'Model is currently in a group show',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            f'https://api-edge.myfreecams.com/usernameLookup/{video_id}',
            video_id)

        user = traverse_obj(data, ('result', 'user', {dict}))
        if not user or not traverse_obj(data, ('result', 'success')):
            raise ExtractorError(
                traverse_obj(data, ('result', 'message', {str})) or 'Model not found',
                expected=True)
        if traverse_obj(user, 'access_level') != 4:
            raise ExtractorError('User is not a model', expected=True)

        session = next((
            s for s in (traverse_obj(user, ('sessions', ..., {dict})) or [])
            if s.get('server_name')), None)
        vs = traverse_obj(session, ('vstate', {int}))
        if vs is None:
            vs = traverse_obj(user, ('vs', {int}))
        if vs in self._PRIVATE_STATUS:
            raise ExtractorError(self._PRIVATE_STATUS[vs], expected=True)
        if vs not in (0, 90) or not traverse_obj(session, 'server_name'):
            raise UserNotLive(video_id=video_id)

        server_id = self._search_regex(
            r'(\d+)$', traverse_obj(session, ('server_name', {str})) or '',
            'server id')
        user_id = traverse_obj(user, ('id', {int}))
        if not user_id:
            raise ExtractorError('Unable to extract model id')
        phase = traverse_obj(session, ('phase', {str})) or ''
        hls_url = (
            f'https://edgevideo.myfreecams.com/hls/NxServer/{server_id}/'
            f'ngrp:mfc_{phase}{user_id + 100000000}.f4v_mobile/playlist.m3u8')

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls', live=True)

        return {
            'id': video_id,
            'title': traverse_obj(user, ('username', {str})) or video_id,
            'uploader': traverse_obj(user, ('username', {str})),
            'uploader_id': str(user_id),
            'thumbnail': traverse_obj(user, ('avatar', {url_or_none})),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
            'age_limit': 18,
        }
