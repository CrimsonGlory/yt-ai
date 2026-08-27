import base64
import hashlib
import re
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class MeipaiIE(InfoExtractor):
    IE_DESC = '美拍'
    _VALID_URL = r'https?://(?:www\.)?meipai\.com/media/(?P<id>[0-9]+)'
    _API_URL = 'https://api.meipai.com/medias/show.json'
    _SIG_SALT = 'bdaefd747c7d594f'
    _SIG_KEY = 'Tw5AY783H@EU3#XC'
    _TESTS = [
        {
            # regular uploaded video
            'url': 'http://www.meipai.com/media/531697625',
            'md5': 'e3e9600f9e55a302daecc90825854b4f',
            'info_dict': {
                'id': '531697625',
                'ext': 'mp4',
                'title': '#葉子##阿桑##余姿昀##超級女聲#',
                'description': '#葉子##阿桑##余姿昀##超級女聲#',
                'thumbnail': r're:^https?://.+',
                'duration': 152,
                'timestamp': 1465492420,
                'upload_date': '20160609',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'creator': '她她-TATA',
                'creators': ['她她-TATA'],
                'uploader': '她她-TATA',
                'uploader_id': '1024924944',
                'tags': ['葉子', '阿桑', '余姿昀', '超級女聲'],
            },
        },
        {
            # record of live streaming
            'url': 'http://www.meipai.com/media/585526361',
            'md5': 'ff7d6afdbc6143342408223d4f5fb99a',
            'info_dict': {
                'id': '585526361',
                'ext': 'mp4',
                'title': '姿昀和善願 練歌練琴啦😁😁😁',
                'description': '姿昀和善願 練歌練琴啦😁😁😁',
                'thumbnail': r're:^https?://.+',
                'duration': 5975,
                'timestamp': 1474311799,
                'upload_date': '20160919',
                'view_count': int,
                'creator': '她她-TATA',
            },
            'skip': 'video under review',
        },
    ]

    def _signed_query(self, video_id):
        sig_time = str(int(time.time() * 1000))
        query = {
            'id': video_id,
            'sigTime': sig_time,
            'sigVersion': '1.3',
        }
        # App signing skips every key whose name contains "sig"
        # (sig, sigTime, sigVersion); sigTime is appended separately.
        values = ''.join(sorted(urllib.parse.unquote_plus(str(v)) for k, v in query.items() if 'sig' not in k))
        digest = hashlib.md5(
            f'medias/show.json{values}{self._SIG_SALT}{sig_time}{self._SIG_KEY}'.encode(),
        ).hexdigest()
        query['sig'] = ''.join(digest[i + 1] + digest[i] for i in range(0, len(digest), 2))
        return query

    @staticmethod
    def _decode_video_url(encoded):
        if not encoded:
            return None
        if encoded.startswith('//'):
            return f'https:{encoded}'
        if encoded.startswith(('http://', 'https://')):
            return encoded

        def strip_chunk(src, start, length):
            start, length = int(start), int(length)
            chunk = src[start : start + length]
            return src[:start] + src[start:].replace(chunk, '', 1)

        try:
            payload = encoded[4:]
            dec = str(int(encoded[:4][::-1], 16))
            mid = strip_chunk(payload, dec[0], dec[1])
            decoded = base64.b64decode(strip_chunk(mid, len(mid) - int(dec[2]) - int(dec[3]), dec[3])).decode()
        except (IndexError, TypeError, ValueError, UnicodeDecodeError, OSError):
            return None
        if decoded.startswith('//'):
            return f'https:{decoded}'
        return url_or_none(decoded) or decoded

    def _extract_video_formats(self, video_url, video_id):
        video_url = self._decode_video_url(video_url)
        if not video_url:
            return []
        if determine_ext(video_url) == 'm3u8':
            return self._extract_m3u8_formats(
                video_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False,
            )
        return [
            {
                'url': video_url,
                'format_id': 'http',
            },
        ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media = self._download_json(
            f'{self._API_URL}?{urllib.parse.urlencode(self._signed_query(video_id))}',
            video_id,
            fatal=False,
            expected_status=400,
        )

        formats = self._extract_video_formats(
            traverse_obj(media, 'video', 'dispatch_video', ('video_list', 'sourceUrl'), get_all=False), video_id,
        )

        if not formats:
            webpage = self._download_webpage(url, video_id)
            m3u8_url = self._html_search_regex(
                r'file:\s*encodeURIComponent\((["\'])(?P<url>(?:(?!\1).)+)\1\)',
                webpage,
                'm3u8 url',
                group='url',
                default=None,
            )
            video_url = m3u8_url or self._search_regex(
                r'data-video=(["\'])(?P<url>(?:(?!\1).)+)\1', webpage, 'video url', group='url', default=None,
            )
            formats = self._extract_video_formats(video_url, video_id)

        if not formats:
            error = traverse_obj(media, 'error', expected_type=str)
            if error:
                raise ExtractorError(error, expected=True)

        caption = traverse_obj(media, 'caption', expected_type=str)
        return {
            'id': video_id,
            'formats': formats,
            'title': caption,
            'description': caption,
            'tags': re.findall(r'#([^#]+)#', caption or '') or None,
            **traverse_obj(
                media,
                {
                    'thumbnail': ('cover_pic', {url_or_none}),
                    'duration': ('time', {int_or_none}),
                    'timestamp': ('created_at', {int_or_none}),
                    'view_count': ('plays_count', {int_or_none}),
                    'like_count': ('likes_count', {int_or_none}),
                    'comment_count': ('comments_count', {int_or_none}),
                    'creator': ('user', 'screen_name', {str}),
                    'uploader': ('user', 'screen_name', {str}),
                    'uploader_id': ('user', 'id', {str_or_none}),
                },
            ),
        }
