from .common import InfoExtractor
from .twitch import TwitchStreamIE
from ..utils import (
    ExtractorError,
    parse_qs,
    traverse_obj,
)


class NobodyLiveIE(InfoExtractor):
    IE_NAME = 'nobody.live'
    IE_DESC = 'nobody.live zero-viewer Twitch streams'
    _VALID_URL = r'https?://(?:www\.)?nobody\.live/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://nobody.live/',
        'info_dict': {
            'id': str,
            'ext': 'mp4',
            'display_id': str,
            'title': str,
            'description': str,
            'thumbnail': r're:https://.+',
            'uploader': str,
            'uploader_id': str,
            'timestamp': int,
            'upload_date': r're:\d{8}',
            'age_limit': int,
            'live_status': 'is_live',
        },
        'params': {
            # Livestream bytes change; filename must not depend on the random Twitch id
            'outtmpl': 'test.%(ext)s',
        },
        'add_ie': ['TwitchStream'],
    }, {
        'url': 'https://nobody.live/?force=monstercat',
        'only_matching': True,
    }, {
        'url': 'https://nobody.live/?stream=%7B%22user_login%22%3A%22monstercat%22%7D',
        'only_matching': True,
    }, {
        'url': 'https://www.nobody.live/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        stream = self._resolve_stream(url)
        login = traverse_obj(stream, (('user_login', 'user_name'), {str}), get_all=False)
        if not login:
            raise ExtractorError('Unable to determine Twitch channel', expected=True)

        return self.url_result(
            f'https://www.twitch.tv/{login}', ie=TwitchStreamIE, url_transparent=True,
            age_limit=18 if stream.get('is_mature') else 0)

    def _resolve_stream(self, url):
        qs = parse_qs(url)
        force = traverse_obj(qs, ('force', -1, {str}))
        if force:
            return {'user_login': force}

        raw_stream = traverse_obj(qs, ('stream', -1, {str}))
        if raw_stream:
            parsed = self._parse_json(raw_stream, 'stream', fatal=False)
            if isinstance(parsed, dict):
                return parsed

        streams = self._download_json(
            'https://nobody.live/stream', 'stream', query={
                'count': 1,
                'max_viewers': 0,
                'min_age': 0,
                'search_operator': 'all',
            })
        stream = traverse_obj(streams, (0, {dict}))
        if not stream:
            raise ExtractorError('No zero-viewer streams available', expected=True)
        return stream
