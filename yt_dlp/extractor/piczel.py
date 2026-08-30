from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    UserNotLive,
    int_or_none,
    parse_iso8601,
    parse_qs,
    str_or_none,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PiczelIE(InfoExtractor):
    IE_NAME = 'piczel'
    IE_DESC = 'Piczel.tv live streams and recordings'
    _VALID_URL = r'https?://(?:www\.)?piczel\.tv/watch/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://piczel.tv/watch/Nifffi?recording=512592',
        'md5': '99320eb7aa3e9a9e30f10bb4a4486f03',
        'info_dict': {
            'id': '512592',
            'ext': 'mp4',
            'display_id': 'Nifffi',
            'title': 'drawing cutes',
            'description': 'https://linktr.ee/nifffi',
            'thumbnail': 'https://recordings-production.piczel.tv/60996/stream_thnUZI3BTdlgG69e.webp',
            'channel': 'Nifffi',
            'channel_id': '60996',
            'channel_url': 'https://piczel.tv/watch/Nifffi',
            'channel_follower_count': int,
            'uploader': 'Nifffi',
            'uploader_id': '66540',
            'uploader_url': 'https://piczel.tv/watch/Nifffi',
            'age_limit': 18,
            'tags': [],
            'live_status': 'was_live',
        },
    }, {
        'url': 'https://piczel.tv/watch/feedfancier',
        'info_dict': {
            'id': 'feedfancier',
            'ext': 'mp4',
            'display_id': 'feedfancier',
            'title': r're:^Stream',
            'thumbnail': r're:https?://.+',
            'timestamp': int,
            'upload_date': r're:\d{8}',
            'view_count': int,
            'channel': 'feedfancier',
            'channel_id': '30624',
            'channel_url': 'https://piczel.tv/watch/feedfancier',
            'channel_follower_count': int,
            'uploader': 'feedfancier',
            'uploader_id': '32848',
            'uploader_url': 'https://piczel.tv/watch/feedfancier',
            'age_limit': 0,
            'is_live': True,
            'live_status': 'is_live',
        },
        'skip': 'Livestream',
    }, {
        'url': 'https://piczel.tv/watch/Chrisceon',
        'only_matching': True,
    }, {
        'url': 'https://www.piczel.tv/watch/Zyii',
        'only_matching': True,
    }]

    def _extract_stream(self, channel):
        data = self._download_json(f'https://piczel.tv/api/streams/{channel}', channel)
        if traverse_obj(data, 'status') == 'error':
            raise ExtractorError(
                traverse_obj(data, 'message', {str}) or 'Unable to find stream',
                expected=True)

        stream = traverse_obj(data, (
            'data', lambda _, v: (
                str_or_none(v.get('slug')) or str_or_none(v.get('username')) or ''
            ).lower() == channel.lower(), {dict}), get_all=False)
        if not stream:
            raise ExtractorError('Unable to find stream', expected=True)
        return stream

    def _stream_info(self, stream, channel):
        username = traverse_obj(stream, 'username', {str}) or channel
        adult = traverse_obj(stream, 'adult')
        return {
            'display_id': channel,
            'title': strip_or_none(traverse_obj(stream, 'title', {str})) or username,
            'description': strip_or_none(traverse_obj(stream, 'description', {str})),
            'thumbnail': traverse_obj(stream, (
                (('preview', 'url'), ('offline_image', 'url'), ('user', 'avatar', 'url')),
                {url_or_none}), get_all=False),
            'timestamp': traverse_obj(stream, ('live_since', {parse_iso8601})),
            'view_count': traverse_obj(stream, ('viewers', {int_or_none})),
            'channel': username,
            'channel_id': traverse_obj(stream, ('id', {str_or_none})),
            'channel_url': f'https://piczel.tv/watch/{channel}',
            'channel_follower_count': traverse_obj(stream, ('follower_count', {int_or_none})),
            'uploader': username,
            'uploader_id': traverse_obj(stream, ('user', 'id', {str_or_none})),
            'uploader_url': f'https://piczel.tv/watch/{channel}',
            'age_limit': 18 if adult else 0 if adult is False else None,
            'tags': traverse_obj(stream, ('tags', ..., 'title', {str})),
        }

    def _real_extract(self, url):
        channel = self._match_id(url)
        recording_id = traverse_obj(parse_qs(url), ('recording', -1, {int_or_none}))
        stream = self._extract_stream(channel)
        info = self._stream_info(stream, channel)

        if traverse_obj(stream, 'is_private') or traverse_obj(
                stream, ('settings', 'private', 'enabled')):
            self.raise_login_required('This stream is private')

        if recording_id is not None:
            recording = traverse_obj(stream, (
                'recordings', lambda _, v: v.get('id') == recording_id, {dict}),
                get_all=False)
            if not recording:
                raise ExtractorError('Requested recording is unavailable', expected=True)
            if recording.get('private'):
                self.raise_login_required('This recording is private')
            rec_url = traverse_obj(recording, ('url', {url_or_none}))
            if not rec_url:
                raise ExtractorError('Recording has no download URL', expected=True)
            info.pop('timestamp', None)
            info.pop('view_count', None)
            return {
                **info,
                'id': str(recording_id),
                'url': rec_url,
                'ext': 'mp4',
                'thumbnail': traverse_obj(recording, ('thumb', {url_or_none})) or info.get('thumbnail'),
                'is_live': False,
                'live_status': 'was_live',
            }

        if not stream.get('live'):
            raise UserNotLive(video_id=channel)

        stream_id = traverse_obj(stream, ('id', {str_or_none})) or channel
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'https://playback.piczel.tv/live/{stream_id}/llhls.m3u8?_HLS_legacy=YES',
            channel, 'mp4', m3u8_id='hls', live=True)

        return {
            **info,
            'id': channel,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }
