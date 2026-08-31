import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    mimetype2ext,
    traverse_obj,
    unified_strdate,
    url_or_none,
)


class VeevIE(InfoExtractor):
    IE_NAME = 'veev'
    IE_DESC = 'Veev.to'
    _VALID_URL = r'https?://(?:www\.)?veev\.to/(?:e|d)/(?P<id>[0-9A-Za-z]+)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?veev\.to/e/[0-9A-Za-z]+)']
    _TESTS = [
        {
            'url': 'https://veev.to/e/3elmmdubhspm',
            'md5': '3c73993cea555ce5b815d84c04fcb202',
            'info_dict': {
                'id': '3elmmdubhspm',
                'ext': 'mp4',
                'title': 'Istri tetangga di toilet 1',
                'thumbnail': r're:https?://.+',
                'upload_date': '20260306',
                'age_limit': 18,
            },
        },
        {
            'url': 'https://veev.to/d/3elmmdubhspm',
            'only_matching': True,
        },
        {
            'url': 'https://veev.to/e/hkb4y1dofk53',
            'only_matching': True,
        },
    ]

    _FC_RE = re.compile(r'''(?:\bfc|_vvto\[[^\]]*\])(?:['\]]+)?\s*[:=]\s*['"]([^'"]+)''')

    @staticmethod
    def _lzw_decode(text):
        if not text:
            return text
        result = []
        table = {}
        n = 256
        prev = text[0]
        result.append(prev)
        for char in text[1:]:
            code = ord(char)
            entry = char if code < 256 else table.get(code, prev + prev[0])
            result.append(entry)
            table[n] = prev + entry[0]
            n += 1
            prev = entry
        return ''.join(result)

    @staticmethod
    def _decode_steps(token):
        chars = list(token or '')
        steps = []
        while chars:
            char = chars.pop(0)
            count = int(char) if char.isdigit() else 0
            if not count:
                break
            current = []
            for _ in range(count):
                if not chars:
                    return steps
                char = chars.pop(0)
                current.insert(0, int(char) if char.isdigit() else 0)
            steps.append(current)
        return steps

    @staticmethod
    def _decode_source(encoded, steps):
        data = encoded
        for step in steps:
            if step == 1:
                data = data[::-1]
            data = bytes.fromhex(data).decode()
            data = data.replace('dXRmOA==', '')
        return data

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = urllib.parse.urlparse(url).hostname or 'veev.to'
        player_url = f'https://{host}/e/{video_id}'
        webpage = self._download_webpage(player_url, video_id)

        headers = {'Referer': player_url, 'Origin': f'https://{host}'}
        file_info = None
        decode_steps = None
        for raw in reversed(self._FC_RE.findall(webpage)):
            challenge = self._lzw_decode(raw)
            if challenge == raw:
                continue
            steps = self._decode_steps(challenge)
            if not steps:
                continue
            api = self._download_json(
                f'https://{host}/dl',
                video_id,
                'Downloading player API JSON',
                headers=headers,
                query={
                    'op': 'player_api',
                    'cmd': 'gi',
                    'file_code': video_id,
                    'ch': challenge,
                    'ie': '1',
                },
            )
            candidate = traverse_obj(api, 'file', expected_type=dict) or {}
            if traverse_obj(candidate, 'file_status') == 'OK':
                file_info, decode_steps = candidate, steps[0]
                break
            status = traverse_obj(candidate, 'file_status', expected_type=str)
            message = traverse_obj(api, 'message', expected_type=str)
            if status == 'deleted' or message == 'file not found':
                raise ExtractorError(message or 'Video has been deleted', expected=True)

        if not file_info:
            raise ExtractorError('Unable to extract video', expected=True)

        formats = []
        for source in traverse_obj(file_info, ('dv', ..., {dict})) or []:
            encoded = source.get('s')
            if not encoded:
                continue
            try:
                media_url = url_or_none(self._decode_source(self._lzw_decode(encoded), decode_steps))
            except (ValueError, UnicodeDecodeError):
                continue
            if media_url:
                formats.append(
                    {
                        'url': media_url,
                        'format_id': 'http',
                        'ext': mimetype2ext(file_info.get('file_mime_type')) or 'mp4',
                    },
                )
        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        subtitles = {}
        for caption in traverse_obj(file_info, ('captions_list', ..., {dict})) or []:
            caption_url = url_or_none(caption.get('src'))
            if not caption_url:
                continue
            lang = caption.get('language') or caption.get('label') or 'und'
            subtitles.setdefault(lang, []).append({'url': caption_url})

        title = traverse_obj(file_info, 'file_title', expected_type=str) or self._html_extract_title(
            webpage, default=None,
        )
        if title:
            title = re.sub(r'(?i)^watch\s+', '', title)
            title = re.sub(r'(?i)\s+-\s+veev\.to$', '', title).strip() or title

        return {
            'id': video_id,
            'title': title or video_id,
            'formats': formats,
            'thumbnail': traverse_obj(
                file_info, 'player_img', 'video_img_url', 'video_thumb_url', expected_type=url_or_none, get_all=False,
            ),
            'upload_date': unified_strdate(traverse_obj(file_info, 'file_created_txt', expected_type=str)),
            'age_limit': 18,
            'subtitles': subtitles,
            'http_headers': headers,
        }
