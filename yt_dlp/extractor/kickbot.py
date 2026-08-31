from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    str_or_none,
    traverse_obj,
    url_or_none,
)
from ..utils.jslib import devalue


class KickBotIE(InfoExtractor):
    IE_NAME = 'kickbot'
    IE_DESC = 'KickBot'
    _VALID_URL = r'https?://(?:www\.)?kickbot\.(?:app|com)/clip/(?P<id>[\w-]+)'
    _CDN_BASE = 'https://clips.kickbotcdn.com'
    _R2_PREFIX = 'https://pub-5ff6af9ebca741508e1748fe1a3cf9f5.r2.dev'
    _TESTS = [{
        'url': 'https://www.kickbot.app/clip/cnzxv42vrekk',
        'md5': '6bb6852eea79b18f72d07ab1fc928737',
        'info_dict': {
            'id': 'cnzxv42vrekk',
            'ext': 'mp4',
            'title': 'ZingoSquad clipped by Mask2424',
            'thumbnail': 'https://clips.kickbotcdn.com/kickbot-hls/cnzxv42vrekk/first_frame.jpg',
            'duration': 86,
            'timestamp': 1788067500,
            'upload_date': '20260830',
            'uploader': 'Mask2424',
            'channel': 'zingosquad',
            'channel_id': '65704',
            'channel_follower_count': int,
            'view_count': int,
        },
    }, {
        'url': 'https://www.kickbot.app/clip/wmb9ove4yif6',
        'info_dict': {
            'id': 'wmb9ove4yif6',
            'ext': 'mp4',
            'title': 'Batslayz clipped by Greenbear63',
            'thumbnail': 'https://clips.kickbotcdn.com/kickbot-hls/wmb9ove4yif6/first_frame.jpg',
            'duration': 30,
            'timestamp': 1698360012,
            'upload_date': '20231026',
            'uploader': 'Greenbear63',
            'channel': 'batslayz',
            'channel_id': '8271',
            'channel_follower_count': int,
            'view_count': int,
        },
        'params': {'skip_download': 'm3u8'},
    }, {
        'url': 'https://www.kickbot.com/clip/wmb9ove4yif6',
        'only_matching': True,
    }, {
        'url': 'https://kickbot.com/clip/cnzxv42vrekk',
        'only_matching': True,
    }, {
        'url': 'https://www.kickbot.com/clip/ncjvunj6og',
        'only_matching': True,
    }]

    def _parse_clip_page(self, data, video_id):
        for node in traverse_obj(data, ('nodes', ..., {dict})):
            payload = node.get('data')
            if not payload:
                continue
            try:
                parsed = devalue.parse(payload)
            except (TypeError, ValueError, IndexError):
                continue
            if isinstance(parsed, dict) and 'clip' in parsed:
                return parsed
        raise ExtractorError('Unable to extract clip data', video_id=video_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            f'https://www.kickbot.com/clip/{video_id}/__data.json', video_id)
        page = self._parse_clip_page(data, video_id)
        clip = page.get('clip')
        if not isinstance(clip, dict):
            raise ExtractorError('Clip not found', expected=True, video_id=video_id)

        formats = []
        r2_url = traverse_obj(clip, ('r2_link', {url_or_none}))
        if r2_url:
            formats.append({
                'url': r2_url.replace(self._R2_PREFIX, self._CDN_BASE),
                'ext': 'mp4',
                'quality': 1,
            })
        else:
            formats.extend(self._extract_m3u8_formats(
                f'{self._CDN_BASE}/kickbot-hls/{video_id}/playlist.m3u8',
                video_id, 'mp4', m3u8_id='hls'))
            if clip.get('download_exists'):
                formats.append({
                    'url': f'{self._CDN_BASE}/kickbot-hls/{video_id}/{video_id}.mp4',
                    'ext': 'mp4',
                    'quality': 1,
                })

        duration = int_or_none(clip.get('length'))
        if duration is None:
            start_time, end_time = clip.get('start_time'), clip.get('end_time')
            if isinstance(start_time, (int, float)) and isinstance(end_time, (int, float)):
                duration = int(end_time - start_time)

        return {
            'id': video_id,
            'formats': formats,
            'title': (
                traverse_obj(page, ('og_title', {str}))
                or traverse_obj(clip, ('clip_name', {str}))
                or join_nonempty(
                    traverse_obj(clip, ('streamer', 'kick_username', {str})),
                    traverse_obj(clip, ('clipper_username', {str})),
                    delim=' clipped by ')),
            'duration': duration,
            'thumbnail': f'{self._CDN_BASE}/kickbot-hls/{video_id}/first_frame.jpg',
            **traverse_obj(clip, {
                'timestamp': ('created_at', {parse_iso8601}),
                'view_count': ('views', {int_or_none}),
                'uploader': ('clipper_username', {str}),
                'channel': ('streamer', 'kick_slug', {str}),
                'channel_id': ('streamer', 'id', {int_or_none}, {str_or_none}),
                'channel_follower_count': ('streamer', 'kick_followers', {int_or_none}),
            }),
        }
