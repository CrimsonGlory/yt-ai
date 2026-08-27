from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class HuajiaoIE(InfoExtractor):
    IE_DESC = '花椒直播'
    _VALID_URL = r'https?://(?:www\.)?huajiao\.com/l/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.huajiao.com/l/350230246',
        'md5': 'e7d738e01df37b15218d9cc4c6a18d5c',
        'info_dict': {
            'id': '350230246',
            'ext': 'mp4',
            'title': '小白牙...正在直播',
            'duration': 28285,
            'thumbnail': r're:^https?://.*\.(?:jpg|png|jpeg)',
            'timestamp': 1787782322,
            'upload_date': '20260826',
            'uploader': '小白牙🎙️（lucky 版❤️）',
            'uploader_id': '269174777',
            'live_status': 'was_live',
        },
    }, {
        'url': 'http://www.huajiao.com/l/38941232',
        'skip': 'replay gone',
        'info_dict': {
            'id': '38941232',
            'ext': 'mp4',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json(
            'https://live.huajiao.com/feed/getFeedInfo', video_id,
            query={'relateid': video_id})
        data = json_data.get('data') or {}
        feed = data.get('feed') or {}
        if json_data.get('errno') or not feed.get('sn'):
            raise ExtractorError(
                json_data.get('errmsg') or 'This live stream is unavailable',
                expected=True)

        is_live = str(feed.get('replay_status', '0')) == '0'
        formats = []
        m3u8_url = url_or_none(feed.get('m3u8'))
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', live=is_live))

        if is_live or not formats:
            stream = self._download_json(
                'https://live.huajiao.com/live/substream', video_id,
                query={
                    'sn': feed['sn'],
                    'uid': traverse_obj(data, ('author', 'uid', {str})),
                    'liveid': video_id,
                    'encode': feed.get('encode') or 'h265',
                    'version': '1.0.0',
                }, fatal=False)
            stream_data = traverse_obj(stream, ('data', {dict})) or {}
            hls = url_or_none(stream_data.get('pull_m3u8'))
            if hls:
                formats.extend(self._extract_m3u8_formats(
                    hls, video_id, 'mp4', m3u8_id='hls', live=True, fatal=False))
            flv = url_or_none(
                stream_data.get('h264_url') or stream_data.get('main')
                or feed.get('pull_url'))
            if flv:
                formats.append({
                    'url': flv,
                    'format_id': 'flv',
                    'ext': 'flv',
                })

        return {
            'id': video_id,
            'title': feed.get('title') or traverse_obj(data, ('author', 'nickname', {str})),
            'duration': int_or_none(feed.get('duration')) or None,
            'thumbnail': url_or_none(feed.get('image')),
            'timestamp': parse_iso8601(data.get('creatime'), ' '),
            'uploader': traverse_obj(data, ('author', 'nickname', {str})),
            'uploader_id': str_or_none(traverse_obj(data, ('author', 'uid'))),
            'is_live': is_live,
            'was_live': not is_live,
            'formats': formats,
        }
