import base64
import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    remove_end,
    str_or_none,
    traverse_obj,
    try_get,
    unified_timestamp,
    url_or_none,
)


class GoProIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?gopro\.com/v/(?P<id>[A-Za-z0-9]+)'

    _TESTS = [{
        'url': 'https://gopro.com/v/ZNVvED8QDzR5V',
        'md5': 'cbe57429ecd2ea069e9ab14a52f1a27b',
        'info_dict': {
            'id': 'ZNVvED8QDzR5V',
            'ext': 'mp4',
            'title': 'My GoPro Adventure - 9/19/21',
            'thumbnail': r're:https?://.+',
            'timestamp': 1632071663,
            'upload_date': '20210919',
            'uploader_id': 'cefac45d-9eb2-482f-bf85-36f8e64b7151',
        },
    }, {
        'url': 'https://gopro.com/v/KRm6Vgp2peg4e',
        'skip': 'video gone',
        'info_dict': {
            'id': 'KRm6Vgp2peg4e',
            'title': 'じゃがいも カリカリ オーブン焼き',
            'thumbnail': r're:https?://.+',
            'ext': 'mp4',
            'timestamp': 1607231125,
            'upload_date': '20201206',
            'uploader_id': 'dc9bcb8b-47d2-47c6-afbc-4c48f9a3769e',
            'duration': 45187,
            'track': 'The Sky Machine',
        },
    }, {
        'url': 'https://gopro.com/v/kVrK9wlJvBMwn',
        'md5': 'a5084c90889680050e6d762cd2ad8bfa',
        'info_dict': {
            'id': 'kVrK9wlJvBMwn',
            'ext': 'mp4',
            'title': 'DARKNESS',
            'thumbnail': r're:https?://.+',
            'uploader_id': '55b50340-069e-49c5-8d51-04c76f7694f8',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        metadata = self._search_json(
            r'window\.__reflectData\s*=', webpage, 'metadata', video_id, default={})

        video_info = traverse_obj(metadata, ('collectionMedia', 0, {dict})) or {}
        media_id = video_info.get('id')
        if not media_id:
            # New GoPro share pages embed the media id in the og:image JWT
            for jwt in re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', webpage):
                try:
                    payload = jwt.split('.')[1]
                    payload += '=' * ((4 - len(payload) % 4) % 4)
                    data = json.loads(base64.urlsafe_b64decode(payload))
                except Exception:
                    continue
                media_id = data.get('medium_id')
                if media_id:
                    break
        if not media_id:
            raise ExtractorError('Unable to extract GoPro media id')
        media_data = self._download_json(
            f'https://api.gopro.com/media/{media_id}/download', video_id)

        formats = []
        for fmt in try_get(media_data, lambda x: x['_embedded']['variations']) or []:
            format_url = url_or_none(fmt.get('url'))
            if not format_url:
                continue
            formats.append({
                'url': format_url,
                'format_id': str_or_none(fmt.get('quality')),
                'format_note': str_or_none(fmt.get('label')),
                'ext': str_or_none(fmt.get('type')),
                'width': int_or_none(fmt.get('width')),
                'height': int_or_none(fmt.get('height')),
            })

        title = str_or_none(
            try_get(metadata, lambda x: x['collection']['title'])
            or self._html_search_meta(['og:title', 'twitter:title'], webpage)
            or remove_end(self._html_search_regex(
                r'<title[^>]*>([^<]+)</title>', webpage, 'title', fatal=False), ' | GoPro'))
        if title:
            title = title.replace('\n', ' ')

        duration = int_or_none(video_info.get('source_duration')) or int_or_none(
            try_get(media_data, lambda x: x['_embedded']['variations'][0]['duration']))
        uploader_id = str_or_none(try_get(metadata, lambda x: x['account']['nickname']))
        timestamp = unified_timestamp(try_get(metadata, lambda x: x['collection']['created_at']))
        if not timestamp:
            # JWT thumbnail payload includes thumbnail_updated_date
            for jwt in re.findall(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', webpage):
                try:
                    payload = jwt.split('.')[1]
                    payload += '=' * ((4 - len(payload) % 4) % 4)
                    data = json.loads(base64.urlsafe_b64decode(payload))
                except Exception:
                    continue
                timestamp = unified_timestamp(data.get('thumbnail_updated_date')) or timestamp
                uploader_id = uploader_id or str_or_none(data.get('owner'))
                if timestamp:
                    break

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': url_or_none(
                self._html_search_meta(['og:image', 'twitter:image'], webpage)),
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'duration': duration,
            'artist': str_or_none(
                video_info.get('music_track_artist')) or None,
            'track': str_or_none(
                video_info.get('music_track_name')) or None,
        }
