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
        last_err = None
        twitch_ie = TwitchStreamIE()
        twitch_ie.set_downloader(self._downloader)
        for stream in self._iter_streams(url):
            login = traverse_obj(stream, (('user_login', 'user_name'), {str}), get_all=False)
            if not login:
                continue
            try:
                info = twitch_ie.extract(f'https://www.twitch.tv/{login}')
            except ExtractorError as e:
                if not e.expected:
                    raise
                self.to_screen(f'{login} is not available; trying next nobody.live stream')
                last_err = e
                continue
            info['age_limit'] = 18 if stream.get('is_mature') else info.get('age_limit') or 0
            return info

        if last_err:
            raise last_err
        raise ExtractorError('No zero-viewer streams available', expected=True)

    def _iter_streams(self, url):
        qs = parse_qs(url)
        force = traverse_obj(qs, ('force', -1, {str}))
        if force:
            yield {'user_login': force}
            return

        raw_stream = traverse_obj(qs, ('stream', -1, {str}))
        if raw_stream:
            parsed = self._parse_json(raw_stream, 'stream', fatal=False)
            if isinstance(parsed, dict):
                yield parsed
                return

        streams = self._download_json(
            'https://nobody.live/stream', 'stream', query={
                'count': 8,
                'max_viewers': 0,
                'min_age': 0,
                'search_operator': 'all',
            })
        yielded = False
        for stream in traverse_obj(streams, (..., {dict})) or ():
            yielded = True
            yield stream
        if not yielded:
            raise ExtractorError('No zero-viewer streams available', expected=True)
