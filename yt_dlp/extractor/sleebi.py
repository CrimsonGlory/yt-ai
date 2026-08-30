from .common import InfoExtractor
from ..networking import PUTRequest
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    int_or_none,
    parse_resolution,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class SleebiIE(InfoExtractor):
    IE_NAME = 'sleebi'
    IE_DESC = 'Sleebi'
    _VALID_URL = r'https?://(?:www\.)?sleebi\.net/v/(?!API/)(?P<id>[0-9A-Za-z]+)'
    _TESTS = [{
        'url': 'https://sleebi.net/v/AAAGy',
        'md5': '5f67ddefe75460d47221db994ac60c62',
        'info_dict': {
            'id': 'AAAGy',
            'ext': 'mp4',
            'title': 'ASMR - Royal Sculptor Measures and Draws You, Roleplay',
            'description': 'md5:e5262d8c0b8ff0e9914b448c3f8a1bb9',
            'thumbnail': r're:https?://.+',
            'duration': 2093,
            'upload_date': '20250421',
            'view_count': int,
            'channel': 'Articulate Design ASMR',
            'channel_id': 'AAAH',
            'channel_url': 'https://sleebi.net/c/AAAH',
            'uploader': 'Articulate Design ASMR',
            'uploader_id': 'AAAH',
            'uploader_url': 'https://sleebi.net/c/AAAH',
            'height': 360,
            'vcodec': 'avc1',
            'acodec': 'mp4a',
            'filesize': 79014311,
        },
    }, {
        'url': 'https://www.sleebi.net/v/AAAGy',
        'only_matching': True,
    }, {
        'url': 'https://sleebi.net/v/AAANZ',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._download_json(
            f'https://sleebi.net/v/API/{video_id}', video_id, expected_status=404)
        error = traverse_obj(meta, ('error', {str}))
        if error:
            raise ExtractorError(error, expected=True)

        src_info = self._download_json(
            PUTRequest(f'https://sleebi.net/v/API/{video_id}/src'),
            video_id, 'Downloading video source',
            query={'avc': '1', 'vp9': '1', 'av1': '1', 'hevc': '1'},
            expected_status=(403, 404))
        src_error = traverse_obj(src_info, ('error', {str}))
        if src_error:
            if int_or_none(meta.get('tier')) or 'supporting Sleebi' in src_error:
                self.raise_login_required(src_error)
            raise ExtractorError(src_error, expected=True)

        video_url = traverse_obj(src_info, ('src', {url_or_none}))
        if not video_url:
            self.raise_no_formats('No video source returned', expected=True, video_id=video_id)

        channel_id = traverse_obj(meta, ('channel', 'sleebiId', {str}))
        channel = traverse_obj(meta, ('channel', 'title', {str}))
        channel_url = f'https://sleebi.net/c/{channel_id}' if channel_id else None
        filesize = traverse_obj(src_info, ('MB', {float_or_none}))

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'filesize': int(filesize * 1024 ** 2) if filesize else None,
            **parse_resolution(video_url),
            **traverse_obj(src_info, {
                'vcodec': ('vcodec', {str}),
                'acodec': ('acodec', {str}),
            }),
            **traverse_obj(meta, {
                'title': ('title', {str}),
                'description': ('description', {clean_html}),
                'duration': ('num_duration', {int_or_none}),
                'view_count': ('views', {int_or_none}),
                'upload_date': ('publishDate', {unified_strdate}),
                'thumbnail': ((('thumbnailUrls', ('maxres', 'high', 'medium', 'low')),
                               'fallbackThumbUrl'), {url_or_none}, any),
            }),
            'channel': channel,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'uploader': channel,
            'uploader_id': channel_id,
            'uploader_url': channel_url,
        }


class SleebiChannelIE(InfoExtractor):
    IE_NAME = 'sleebi:channel'
    IE_DESC = 'Sleebi channels'
    _VALID_URL = r'https?://(?:www\.)?sleebi\.net/c/(?!API/)(?P<id>[0-9A-Za-z]+)'
    _TESTS = [{
        'url': 'https://sleebi.net/c/AAAH',
        'info_dict': {
            'id': 'AAAH',
            'title': 'Articulate Design ASMR',
        },
        'playlist_mincount': 15,
    }, {
        'url': 'https://www.sleebi.net/c/AAAH',
        'only_matching': True,
    }]

    def _entries(self, channel_id):
        page = 0
        while True:
            data = self._download_json(
                'https://sleebi.net/q/API/all', channel_id,
                note=f'Downloading channel page {page}',
                query={'channelId': channel_id, 'page': page})
            results = traverse_obj(data, ('results', ..., {dict})) or []
            for video in results:
                video_id = traverse_obj(video, ('sleebiId', {str}))
                if video_id:
                    yield self.url_result(
                        f'https://sleebi.net/v/{video_id}', SleebiIE, video_id,
                        video_title=traverse_obj(video, ('title', {str})))
            if data.get('done') or not results:
                break
            page += 1

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        meta = self._download_json(
            f'https://sleebi.net/c/API/{channel_id}', channel_id, fatal=False)
        return self.playlist_result(
            self._entries(channel_id), channel_id,
            traverse_obj(meta, ('title', {str})))
