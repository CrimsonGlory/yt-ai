import datetime as dt
import re

from .common import InfoExtractor
from ..utils import (
    MEDIA_EXTENSIONS,
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    traverse_obj,
)
from ..utils.jslib import devalue


class PillowsIE(InfoExtractor):
    IE_NAME = 'pillows'
    IE_DESC = 'pillows.su'
    _VALID_URL = r'https?://(?:www\.)?pillows\.su/f/(?P<id>[0-9a-fA-F]{32})'
    _API_BASE = 'https://api.pillows.su'
    _TESTS = [{
        'url': 'https://pillows.su/f/b045c1a41737aa2e7ddabf0520266547',
        'md5': '606630a28ea8c7bdd5b02732327ddddd',
        'info_dict': {
            'id': 'b045c1a41737aa2e7ddabf0520266547',
            'ext': 'mp3',
            'title': '1st Off .... (6minfreestyle Remix) [prod. 2sided].mp3',
            'thumbnail': 'https://api.pillows.su/api/cover/b045c1a41737aa2e7ddabf0520266547.webp',
            'filesize': 3725188,
            'timestamp': 1708646150,
            'upload_date': '20240222',
            'view_count': int,
            'duration': 209.71102040816328,
            'artists': ['Yeat Archive'],
            'vcodec': 'none',
        },
    }, {
        'url': 'https://pillows.su/f/70abc523d7f87741e0875b11dabcdc55',
        'md5': '2f434d74951601c0850799a3eaad6146',
        'info_dict': {
            'id': '70abc523d7f87741e0875b11dabcdc55',
            'ext': 'mp4',
            'title': 'get busy master 4k.MP4',
            'filesize': 219729173,
            'timestamp': 1776473420,
            'upload_date': '20260418',
            'view_count': int,
            'duration': 163.072,
        },
    }, {
        'url': 'https://pillows.su/f/8fbb48ca8eeb6c7210db80712b5f3e27',
        'only_matching': True,
    }, {
        'url': 'https://pillows.su/f/549b9766a8b4c2d9967a78a96eb45b08',
        'only_matching': True,
    }]

    def _parse_svelte_file(self, data, video_id):
        for node in traverse_obj(data, ('nodes', ...)):
            if traverse_obj(node, 'type') == 'error':
                raise ExtractorError(
                    traverse_obj(node, ('error', 'message', {str})) or 'File not found',
                    expected=True, video_id=video_id)
            payload = node.get('data') if isinstance(node, dict) else None
            if not payload:
                continue
            try:
                parsed = devalue.parse(payload)
            except (TypeError, ValueError, IndexError):
                continue
            if isinstance(parsed, dict) and parsed.get('filename'):
                return parsed
        return {}

    def _parse_metadata_txt(self, video_id):
        metadata = self._download_webpage(
            f'{self._API_BASE}/api/metadata/{video_id}.txt', video_id,
            'Downloading file metadata', fatal=False)
        if not metadata:
            return {}

        def field(name):
            value = self._search_regex(
                rf'^{re.escape(name)}:\s*(.+)$', metadata, name, default=None, flags=re.M)
            if not value or value.strip().lower() in ('unknown', 'null'):
                return None
            return value.strip()

        artist = field('ARTIST')
        album = field('ALBUM')
        return {
            'duration': float_or_none(self._search_regex(
                r'^DURATION:\s*([0-9.]+)s', metadata, 'duration', default=None, flags=re.M)),
            'artists': [artist] if artist else None,
            'album': album,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            f'https://pillows.su/f/{video_id}/__data.json', video_id,
            'Downloading SvelteKit data')
        file_info = self._parse_svelte_file(data, video_id)
        if not file_info:
            raise ExtractorError('Unable to extract file metadata', video_id=video_id)

        filename = file_info['filename']
        ext = determine_ext(filename, default_ext='').lower()
        if ext not in (*MEDIA_EXTENSIONS.video, *MEDIA_EXTENSIONS.audio):
            raise ExtractorError('No video/audio found at provided URL.', expected=True)

        def timestamp(value):
            if isinstance(value, dt.datetime):
                return int(value.timestamp())

        info = {
            'id': video_id,
            'title': filename,
            'url': f'{self._API_BASE}/api/download/{video_id}',
            'ext': ext,
            'http_headers': {'Referer': 'https://pillows.su/'},
            **self._parse_metadata_txt(video_id),
            **traverse_obj(file_info, {
                'filesize': ('fileSize', {int_or_none}),
                'view_count': ('views', {int_or_none}),
                'timestamp': ('date', {timestamp}),
            }),
        }
        if file_info.get('cover'):
            info['thumbnail'] = f'{self._API_BASE}/api/cover/{video_id}.webp'
        if ext in MEDIA_EXTENSIONS.audio:
            info['vcodec'] = 'none'
            info['abr'] = int_or_none(file_info.get('bitrate'), scale=1000)
        return info
