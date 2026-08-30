from .common import InfoExtractor
from ..utils import (
    UserNotLive,
    determine_ext,
    float_or_none,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CimeBaseIE(InfoExtractor):
    def _call_api(self, path, video_id, **kwargs):
        return self._download_json(
            f'https://ci.me/api/app/{path}', video_id,
            headers={'Accept': 'application/json'}, **kwargs)['data']

    def _extract_playback(self, playback, video_id, live=False):
        media_url = traverse_obj(playback, ('url', {url_or_none}))
        if not media_url:
            return [], {}
        if determine_ext(media_url) == 'm3u8':
            return self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls', live=live)
        return [{'url': media_url, 'ext': determine_ext(media_url, 'mp4')}], {}

    def _parse_common(self, data):
        return traverse_obj(data, {
            'title': ('title', {str}),
            'thumbnail': (('coverImageUrl', 'imageUrl'), {url_or_none}, any),
            'duration': ('duration', {float_or_none(scale=1000)}),
            'timestamp': (('openedAt', 'createdAt', 'liveOpenedAt'), {parse_iso8601}, any),
            'view_count': ('viewerCnt', {int_or_none}),
            'concurrent_view_count': ('curViewerCnt', {int_or_none}),
            'comment_count': ('commentCnt', {int_or_none}),
            'like_count': ('likeCnt', {int_or_none}),
            'channel': ('channel', 'name', {str}),
            'channel_id': ('channel', 'id', {str}),
            'channel_url': ('channel', 'slug', {lambda x: f'https://ci.me/@{x}' if x else None}),
            'uploader': ('channel', 'name', {str}),
            'uploader_id': ('channel', 'slug', {str}),
            'categories': ('category', 'name', {str}, all),
            'tags': ('tags', ..., 'displayName', {str}),
            'age_limit': ('isAdult', {bool}, {lambda x: 18 if x else 0}),
        })


class CimeIE(CimeBaseIE):
    IE_NAME = 'cime:live'
    IE_DESC = 'ci.me live'
    _VALID_URL = r'https?://(?:www\.)?ci\.me/@(?P<id>[\w-]+)(?:/live)?/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://ci.me/@ttwieonan_angae/live',
        'info_dict': {
            'id': 'ttwieonan_angae',
            'ext': 'mp4',
            'title': str,
            'thumbnail': r're:https?://.+',
            'timestamp': int,
            'upload_date': str,
            'channel': str,
            'channel_id': str,
            'channel_url': 'https://ci.me/@ttwieonan_angae',
            'uploader': str,
            'uploader_id': 'ttwieonan_angae',
            'categories': list,
            'tags': list,
            'age_limit': int,
            'live_status': 'is_live',
            'concurrent_view_count': int,
        },
        'params': {'skip_download': 'livestream'},
        'skip': 'Livestream',
    }, {
        'url': 'https://ci.me/@koyotempest/live',
        'only_matching': True,
    }, {
        'url': 'https://ci.me/@koyotempest',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel = self._match_id(url)
        data = self._call_api(f'channels/{channel}/live', channel)
        if data.get('state') != 'ACTIVE':
            raise UserNotLive(video_id=channel)

        formats, subtitles = self._extract_playback(data.get('playback'), channel, live=True)
        if not formats:
            if data.get('viewAccess'):
                self.raise_login_required()
            self.raise_no_formats('No live playback URL', expected=True, video_id=channel)

        return {
            'id': channel,
            'is_live': True,
            'formats': formats,
            'subtitles': subtitles,
            **self._parse_common(data),
        }


class CimeVODIE(CimeBaseIE):
    IE_NAME = 'cime:vod'
    IE_DESC = 'ci.me VOD'
    _VALID_URL = r'https?://(?:www\.)?ci\.me/@[\w-]+/vods/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://ci.me/@koyotempest/vods/4671',
        'info_dict': {
            'id': '4671',
            'ext': 'mp4',
            'title': '백룸 익스트랙션 w. 스코시즘',
            'thumbnail': r're:https?://.+',
            'duration': 12807.951,
            'timestamp': 1773581479,
            'upload_date': '20260315',
            'view_count': int,
            'comment_count': int,
            'channel': '코요 템페스트',
            'channel_id': '1000164',
            'channel_url': 'https://ci.me/@koyotempest',
            'uploader': '코요 템페스트',
            'uploader_id': 'koyotempest',
            'categories': ['종합게임'],
            'tags': ['스코시즘'],
            'age_limit': 0,
            'live_status': 'was_live',
        },
        'params': {'skip_download': 'm3u8'},
    }, {
        'url': 'https://www.ci.me/@koyotempest/vods/4671',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._call_api(f'videos/{video_id}', video_id)
        formats, subtitles = self._extract_playback(data.get('playback'), video_id)
        if not formats:
            if data.get('viewAccess'):
                self.raise_login_required()
            self.raise_no_formats('No VOD playback URL', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'was_live': True,
            'live_status': 'was_live',
            'formats': formats,
            'subtitles': subtitles,
            **self._parse_common(data),
        }


class CimeClipIE(CimeBaseIE):
    IE_NAME = 'cime:clip'
    IE_DESC = 'ci.me clips'
    _VALID_URL = r'https?://(?:www\.)?ci\.me/clips/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://ci.me/clips/74',
        'md5': 'dfe74b77dafb4b556d861d56b02cdcb8',
        'info_dict': {
            'id': '74',
            'ext': 'mp4',
            'title': '냥냥냥냥',
            'thumbnail': r're:https?://.+',
            'duration': 60.0,
            'timestamp': 1773313867,
            'upload_date': '20260312',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'channel': '니노 선데이',
            'channel_id': '1318',
            'channel_url': 'https://ci.me/@ninosunday',
            'uploader': '니노 선데이',
            'uploader_id': 'ninosunday',
            'categories': ['저스트 채팅'],
            'tags': ['버튜버', 'vtuber', '스코시즘'],
            'age_limit': 0,
        },
    }, {
        'url': 'https://www.ci.me/clips/74',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        clip_id = self._match_id(url)
        data = self._call_api(f'clips/{clip_id}', clip_id)
        formats, subtitles = self._extract_playback(data.get('playback'), clip_id)
        if not formats:
            if data.get('viewAccess'):
                self.raise_login_required()
            self.raise_no_formats('No clip playback URL', expected=True, video_id=clip_id)

        return {
            'id': clip_id,
            'formats': formats,
            'subtitles': subtitles,
            **self._parse_common(data),
        }
