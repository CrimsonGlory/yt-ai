from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    str_or_none,
    unified_timestamp,
    urljoin,
)
from ..utils.traversal import traverse_obj


class EbaumsWorldIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ebaumsworld\.com/videos/[^/?#]+/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.ebaumsworld.com/videos/a-giant-python-opens-the-door/83367677/',
        'md5': '3ce5f96d34ecb96eff3159fd89c3c2ce',
        'info_dict': {
            'id': '83367677',
            'ext': 'mp4',
            'title': 'A Giant Python Opens The Door',
            'description': 'This is how nightmares start...',
            'uploader': 'jihadpizza',
            'uploader_id': '1022869',
            'duration': 12,
            'timestamp': 1371589200,
            'upload_date': '20130618',
            'thumbnail': r're:https?://cdn\.ebaumsworld\.com/.+\.jpg',
            'average_rating': float,
            'like_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        media = self._search_json(
            r'window\.media\s*=\s*\{\s*params:\s*', webpage, 'media data', video_id).get('media') or {}

        formats, thumbnails = [], []
        for f in traverse_obj(media, ('files', lambda _, v: v.get('path'))):
            file_url = urljoin('https://cdn.ebaumsworld.com', f['path'])
            ext = determine_ext(file_url)
            mime = f.get('mime_type') or ''
            if mime.startswith('video/') or ext in ('mp4', 'flv', 'webm', 'mov', 'm4v'):
                formats.append({
                    'url': file_url,
                    'ext': ext,
                    'width': int_or_none(f.get('width')),
                    'height': int_or_none(f.get('height')),
                    'filesize': int_or_none(f.get('size')),
                    'format_id': {1: 'original', 2: 'http'}.get(f.get('type')),
                })
            elif mime.startswith('image/') or ext in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
                thumbnails.append({
                    'url': file_url,
                    'width': int_or_none(f.get('width')),
                    'height': int_or_none(f.get('height')),
                })

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
            'thumbnails': thumbnails,
            **traverse_obj(media, {
                'title': 'title',
                'description': 'description_short',
                'uploader': ('user', 'username'),
                'uploader_id': ('user', 'id', {str_or_none}),
                'timestamp': ('publish_date', {unified_timestamp}),
                'duration': ('files', ..., 'length', {int_or_none}, filter, any),
                'average_rating': ('avg_rating', {float_or_none}),
                'like_count': ('favorited', {int_or_none}),
            }),
        }
