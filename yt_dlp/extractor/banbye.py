import math
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    InAdvancePagedList,
    determine_ext,
    format_field,
    int_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class BanByeBaseIE(InfoExtractor):
    _API_BASE = 'https://banbye.com/api'
    _VIDEO_BASE = 'https://banbye.com/watch'

    @staticmethod
    def _extract_playlist_id(url, param='playlist'):
        return urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query).get(param, [None])[0]

    def _extract_playlist(self, playlist_id):
        data = self._download_json(f'{self._API_BASE}/playlists/{playlist_id}', playlist_id)
        video_ids = (
            traverse_obj(data, ('items', ..., 'id', {str}))
            or traverse_obj(data, ('videoIds', ..., {str}))
            or [])
        return self.playlist_result([
            self.url_result(f'{self._VIDEO_BASE}/{video_id}', BanByeIE)
            for video_id in video_ids], playlist_id, data.get('name'))


class BanByeIE(BanByeBaseIE):
    _VALID_URL = r'https?://(?:www\.)?banbye\.com/(?:en/)?watch/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://banbye.com/watch/v_ytfmvkVYLE8T',
        'skip': 'playback unavailable',
        'md5': '2f4ea15c5ca259a73d909b2cfd558eb5',
        'info_dict': {
            'id': 'v_ytfmvkVYLE8T',
            'ext': 'mp4',
            'title': 'md5:5ec098f88a0d796f987648de6322ba0f',
            'description': 'md5:4d94836e73396bc18ef1fa0f43e5a63a',
            'uploader': 'wRealu24',
            'channel_id': 'ch_wrealu24',
            'channel_url': 'https://banbye.com/channel/ch_wrealu24',
            'timestamp': 1647604800,
            'upload_date': '20220318',
            'duration': 1931,
            'thumbnail': r're:https?://.*\.webp',
            'tags': 'count:5',
            'like_count': int,
            'dislike_count': int,
            'view_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://banbye.com/watch/v_zEgOnF0Ik4W7',
        'info_dict': {
            'id': 'v_zEgOnF0Ik4W7',
            'ext': 'mp4',
            'title': 'md5:d18345134d3d0d9f1b52c37fdc80c43c',
            'description': 'md5:3881923463cbb6799d2df3f43bbf17c6',
            'uploader': 'wRealu24',
            'channel_id': 'ch_wrealu24',
            'channel_url': 'https://banbye.com/channel/ch_wrealu24',
            'timestamp': 1791181520,
            'upload_date': '20261005',
            'duration': 404,
            'thumbnail': r're:https?://media\.banbye\.net/video/v_zEgOnF0Ik4W7/.+\.webp',
            'tags': ['waldemar', 'krysiak', 'myslozbir', 'bloger', 'youtuber'],
            'like_count': int,
            'dislike_count': int,
            'view_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://banbye.com/watch/v_2JjQtqjKUE_F?playlistId=p_Ld82N6gBw_OJ',
        'info_dict': {
            'title': 'Krzysztof Karoń',
            'id': 'p_Ld82N6gBw_OJ',
        },
        'playlist_mincount': 9,
    }, {
        'url': 'https://banbye.com/watch/v_kb6_o1Kyq-CD',
        'skip': 'playback unavailable',
        'params': {'format': '144'},
        'info_dict': {
            'id': 'v_kb6_o1Kyq-CD',
            'ext': 'mp4',
            'title': 'Co tak naprawdę dzieje się we Francji?! Czy Warszawa a potem cała Polska będzie drugim Paryżem?!🤔🇵🇱',
            'description': 'md5:82be4c0e13eae8ea1ca8b9f2e07226a8',
            'uploader': 'Marcin Rola - MOIM ZDANIEM!🇵🇱',
            'channel_id': 'ch_QgWnHvDG2fo5',
            'channel_url': 'https://banbye.com/channel/ch_QgWnHvDG2fo5',
            'duration': 597,
            'timestamp': 1688642656,
            'upload_date': '20230706',
            'thumbnail': 'https://cdn.banbye.com/video/v_kb6_o1Kyq-CD/96.webp',
            'tags': ['Paryż', 'Francja', 'Polska', 'Imigranci', 'Morawiecki', 'Tusk'],
            'like_count': int,
            'dislike_count': int,
            'view_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://banbye.com/watch/v_a_gPFuC9LoW5',
        'skip': 'playback unavailable',
        'info_dict': {
            'id': 'v_a_gPFuC9LoW5',
            'ext': 'mp4',
            'title': 'md5:183524056bebdfa245fd6d214f63c0fe',
            'description': 'md5:943ac87287ca98d28d8b8797719827c6',
            'uploader': 'wRealu24',
            'channel_id': 'ch_wrealu24',
            'channel_url': 'https://banbye.com/channel/ch_wrealu24',
            'upload_date': '20231113',
            'timestamp': 1699874062,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'thumbnail': 'https://cdn.banbye.com/video/v_a_gPFuC9LoW5/96.webp',
            'tags': ['jaszczur', 'sejm', 'lewica', 'polska', 'ukrainizacja', 'pierwszeposiedzeniesejmu'],
        },
        'expected_warnings': ['Failed to download m3u8'],
    }, {
        'url': 'https://banbye.com/watch/v_B0rsKWsr-aaa',
        'skip': 'playback unavailable',
        'info_dict': {
            'id': 'v_B0rsKWsr-aaa',
            'ext': 'mp4',
            'title': 'md5:00b254164b82101b3f9e5326037447ed',
            'description': 'md5:3fd8b48aa81954ba024bc60f5de6e167',
            'uploader': 'PSTV Piotr Szlachtowicz ',
            'channel_id': 'ch_KV9EVObkB9wB',
            'channel_url': 'https://banbye.com/channel/ch_KV9EVObkB9wB',
            'upload_date': '20240629',
            'timestamp': 1719646816,
            'duration': 2377,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'thumbnail': 'https://cdn.banbye.com/video/v_B0rsKWsr-aaa/96.webp',
            'tags': ['Biden', 'Trump', 'Wybory', 'USA'],
        },
    }]

    def _extract_playback(self, video_id, playback):
        playback = playback or {}
        if not traverse_obj(playback, ('urls', ..., {url_or_none})) and not playback.get('blocker'):
            session = self._download_json(
                f'{self._API_BASE}/videos/{video_id}/playback', video_id,
                'Downloading playback session', data=b'{}',
                headers={'Content-Type': 'application/json'})
            playback = traverse_obj(session, ('playback', {dict})) or playback

        blocker = playback.get('blocker')
        if blocker:
            raise ExtractorError(f'Video is not playable ({blocker})', expected=True)

        formats = []
        fmt = playback.get('format')
        for play_url in traverse_obj(playback, ('urls', ..., {url_or_none})):
            if fmt == 'hls' or determine_ext(play_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    play_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': play_url,
                    'ext': determine_ext(play_url, 'mp4'),
                    'format_id': fmt,
                })

        for quality in traverse_obj(playback, ('qualities', ..., {dict})):
            height = int_or_none(quality.get('shortSide') or quality.get('height') or quality.get('name'))
            for qurl in traverse_obj(quality, ('urls', ..., {url_or_none})):
                formats.append({
                    'url': qurl,
                    'format_id': str(quality.get('name') or height or 'mp4'),
                    'height': height,
                    'width': int_or_none(quality.get('width')),
                })
        self._remove_duplicate_formats(formats)
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        playlist_id = self._extract_playlist_id(url, 'playlistId')

        if self._yes_playlist(playlist_id, video_id):
            return self._extract_playlist(playlist_id)

        data = self._download_json(f'{self._API_BASE}/videos/{video_id}', video_id)
        formats = self._extract_playback(video_id, traverse_obj(data, ('playback', {dict})))
        if not formats:
            self.raise_no_formats('No playback URL', expected=True, video_id=video_id)

        thumbnails = []
        for part in (traverse_obj(data, ('thumbnail', 'srcSet', {str})) or '').split(','):
            part = part.strip()
            if not part:
                continue
            thumb_url, _, width = part.partition(' ')
            thumbnails.append({
                'url': thumb_url,
                'width': int_or_none((width or '').rstrip('w')),
            })
        if not thumbnails:
            thumb_url = traverse_obj(data, ('thumbnail', 'src', {url_or_none}))
            if thumb_url:
                thumbnails.append({'url': thumb_url})

        channel_id = traverse_obj(data, ('channel', 'id', {str})) or data.get('channelId')
        return {
            'id': video_id,
            'title': data.get('title'),
            'description': data.get('description') or data.get('desc'),
            'uploader': traverse_obj(data, ('channel', 'name')),
            'channel_id': channel_id,
            'channel_url': format_field(channel_id, None, 'https://banbye.com/channel/%s'),
            'timestamp': unified_timestamp(data.get('publishedAt')),
            'duration': int_or_none(data.get('durationSeconds') or data.get('duration')),
            'tags': data.get('tags'),
            'formats': formats,
            'thumbnails': thumbnails,
            'like_count': data.get('likes'),
            'dislike_count': data.get('dislikes'),
            'view_count': data.get('views'),
            'comment_count': data.get('commentCount'),
        }


class BanByeChannelIE(BanByeBaseIE):
    _VALID_URL = r'https?://(?:www\.)?banbye\.com/(?:en/)?(?:channel|c)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://banbye.com/channel/ch_wrealu24',
        'info_dict': {
            'title': 'wRealu24',
            'id': 'ch_wrealu24',
            'description': 'md5:3982f98a3f8bed1b30c872113cedc39a',
        },
        'playlist_mincount': 791,
    }, {
        'url': 'https://banbye.com/channel/ch_wrealu24?playlist=p_Ld82N6gBw_OJ',
        'info_dict': {
            'title': 'Krzysztof Karoń',
            'id': 'p_Ld82N6gBw_OJ',
        },
        'playlist_mincount': 9,
    }]
    _PAGE_SIZE = 50

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        playlist_id = self._extract_playlist_id(url)

        if playlist_id:
            return self._extract_playlist(playlist_id)

        def page_func(page_num):
            data = self._download_json(f'{self._API_BASE}/videos', channel_id, query={
                'channelId': channel_id,
                'sort': 'new',
                'limit': self._PAGE_SIZE,
                'offset': page_num * self._PAGE_SIZE,
            }, note=f'Downloading page {page_num + 1}')
            return [
                self.url_result(f'{self._VIDEO_BASE}/{video_id}', BanByeIE)
                for video_id in traverse_obj(data, ('items', ..., 'id', {str}))
            ]

        channel_data = self._download_json(f'{self._API_BASE}/channels/{channel_id}', channel_id)
        entries = InAdvancePagedList(
            page_func,
            math.ceil(channel_data['videoCount'] / self._PAGE_SIZE),
            self._PAGE_SIZE)

        return self.playlist_result(
            entries, channel_data.get('id') or channel_id,
            channel_data.get('name'), channel_data.get('description'))
