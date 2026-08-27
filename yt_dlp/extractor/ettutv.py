from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class EttuTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ettu\.tv/(?:(?:live|videos)/(?:-?\d+)|(?:[^/?#]+/)*playerpage)/(?P<id>\d+)'
    _API_URL = 'https://testbackend.stupaevents.com/ott/v1/get_video'
    _API_HEADERS = {
        'Accept': 'application/json',
        'tenant': 'ettu',
        'language': 'en',
    }

    _TESTS = [{
        'url': 'https://www.ettu.tv/live/0/2075',
        'md5': '265b1ff1f67c8fc09bf3d9dc6ef0bbfa',
        'info_dict': {
            'id': '2075',
            'ext': 'mp4',
            'title': '2026 Romstal EC U21 Cluj | Day 5 | 21 June | Table 1',
            'description': '2026 Romstal EC U21 Cluj | Day 5 | 21 June | Table 1',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'timestamp': 1782625753,
            'upload_date': '20260628',
            'view_count': int,
            'is_live': False,
        },
    }, {
        'url': 'https://www.ettu.tv/videos/0/2075',
        'only_matching': True,
    }, {
        'url': 'https://www.ettu.tv/en-int/playerpage/1573849',
        'skip': 'Old playerpage URLs are gone after the site rebuild',
        'md5': '5874b7639a2aa866d1f6c3a4037c7c09',
        'info_dict': {
            'id': '1573849',
            'title': 'Ni Xia Lian - Shao Jieni',
            'description': 'ITTF Europe Top 16 Cup',
            'timestamp': 1677348600,
            'upload_date': '20230225',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://www.ettu.tv/en-int/playerpage/1573753',
        'skip': 'Old playerpage URLs are gone after the site rebuild',
        'md5': '1fc094bf96cf2d5ec0f434d3a6dec9aa',
        'info_dict': {
            'id': '1573753',
            'title': 'Qiu Dang - Jorgic Darko',
            'description': 'ITTF Europe Top 16 Cup',
            'timestamp': 1677423600,
            'upload_date': '20230226',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)',
            'ext': 'mp4',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_data = self._download_json(
            self._API_URL, video_id, headers=self._API_HEADERS, query={
                'video_id': video_id,
            })

        video = traverse_obj(api_data, ('detail', 'data', 0, {dict}))
        if not video:
            raise ExtractorError('Video not found', expected=True)

        is_live = traverse_obj(video, 'stream_status') == 'L'
        raw_stream = traverse_obj(
            video, 'playback_id' if is_live else 'asset_playback_id', 'playback_id', 'source_url')
        stream_url = url_or_none(raw_stream)
        if not stream_url and raw_stream:
            stream_url = f'https://stream.mux.com/{raw_stream}.m3u8'
        if not stream_url:
            raise ExtractorError('No stream available', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            stream_url, video_id, 'mp4', live=is_live)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            'timestamp': traverse_obj(
                video, ('stream_start_time', {unified_timestamp}), ('created_at', {unified_timestamp})),
            **traverse_obj(video, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('thumbnail', {url_or_none}),
                'view_count': ('views', {int_or_none}),
            }),
        }
