import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    url_or_none,
)


class ViqeoIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'''(?x)
                        (?:
                            viqeo:|
                            https?://cdn\.viqeo\.tv/embed/*\?.*?\bvid=|
                            https?://api\.viqeo\.tv/v\d+/data/startup?.*?\bvideo(?:%5B%5D|\[\])=
                        )
                        (?P<id>[\da-zA-Z]+)
                    '''
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//cdn\.viqeo\.tv/embed/*\?.*?\bvid=[\da-zA-Z]+.*?)\1']
    _TESTS = [{
        'url': 'https://cdn.viqeo.tv/embed/?vid=f4359bf969587c3806a2',
        'md5': '659d9129bcc2e9ee428c949ba3bccd92',
        'info_dict': {
            'id': '-233551398_456416827',
            'ext': 'mp4',
            'title': 'Гидроциклисты загнали русалку на Фонтанке',
            'thumbnail': r're:https?://.+(?:\.jpg|getVideoPreview.*)',
            'duration': 51,
            'timestamp': 1765827796,
            'upload_date': '20251215',
            'uploader': 'OFF the record | video',
            'uploader_id': '-233551398',
            'like_count': int,
            'comment_count': int,
        },
        'add_ie': ['VK'],
    }, {
        'url': 'https://cdn.viqeo.tv/embed/?vid=cde96f09d25f39bee837',
        'md5': 'a169dd1a6426b350dca4296226f21e76',
        'info_dict': {
            'id': 'cde96f09d25f39bee837',
            'ext': 'mp4',
            'title': 'cde96f09d25f39bee837',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 76,
        },
        'skip': 'No media files',
    }, {
        'url': 'viqeo:cde96f09d25f39bee837',
        'only_matching': True,
    }, {
        'url': 'https://api.viqeo.tv/v1/data/startup?video%5B%5D=71bbec412ade45c3216c&profile=112',
        'only_matching': True,
    }]
    _WEBPAGE_TESTS = [{
        'url': 'https://viqeo.tv/',
        'skip': 'webpage sample unavailable',
        'info_dict': {
            'id': 'viqeo',
            'title': 'Viqeo video platform',
            'age_limit': 0,
            'description': 'md5:e8e06e20df92ed66febeaef2533a0d5d',
            'thumbnail': r're:https?://static\.tildacdn\.com/.+\.png',
            'timestamp': 1751479769,
            'upload_date': '20250702',
        },
        'playlist_count': 3,
    }]

    def _vk_url_result(self, media_url, title=None):
        parsed = urllib.parse.urlparse(media_url)
        if not re.search(r'(?:^|\.)vk(?:video)?\.(?:ru|com)$', parsed.netloc):
            return None
        qs = urllib.parse.parse_qs(parsed.query)
        oid, vk_id = (qs.get('oid') or [None])[0], (qs.get('id') or [None])[0]
        if not oid or not vk_id:
            return None
        return self.url_result(
            f'https://vkvideo.ru/video{oid}_{vk_id}', 'VK',
            f'{oid}_{vk_id}', title)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            f'https://cdn.viqeo.tv/embed/?vid={video_id}', video_id)

        data = self._search_json(
            r'window\.DATA\s*=', webpage, 'player data', video_id, default=None)
        if not data:
            data = self._parse_json(
                self._search_regex(
                    r'SLOT_DATA\s*=\s*({.+?})\s*;', webpage, 'slot data'),
                video_id)
        metadata = data.get('metadata') or data

        if metadata.get('isDeleted'):
            raise ExtractorError('This video has been deleted', expected=True)
        if metadata.get('isBanned'):
            raise ExtractorError('This video is blocked', expected=True)

        title = str_or_none(metadata.get('title')) or video_id
        formats = []
        thumbnails = []
        for media_file in metadata.get('mediaFiles') or []:
            if not isinstance(media_file, dict):
                continue
            media_url = url_or_none(media_file.get('url'))
            if not media_url or not media_url.startswith(('http', '//')):
                continue
            vk_result = self._vk_url_result(media_url, title)
            if vk_result:
                return vk_result
            media_type = str_or_none(media_file.get('type'))
            if not media_type:
                continue
            media_kind = media_type.split('/')[0].lower()
            f = {
                'url': media_url,
                'width': int_or_none(media_file.get('width')),
                'height': int_or_none(media_file.get('height')),
            }
            format_id = str_or_none(media_file.get('quality'))
            if media_kind == 'image':
                f['id'] = format_id
                thumbnails.append(f)
            elif media_kind in ('video', 'audio'):
                is_audio = media_kind == 'audio'
                f.update({
                    'format_id': 'audio' if is_audio else format_id,
                    'fps': int_or_none(media_file.get('fps')),
                    'vcodec': 'none' if is_audio else None,
                })
                formats.append(f)

        if not formats:
            raise ExtractorError('No media files', expected=True)

        duration = int_or_none(metadata.get('duration'))

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'thumbnails': thumbnails,
            'formats': formats,
        }
