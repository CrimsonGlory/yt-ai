import base64
import hashlib
import json

from .common import InfoExtractor
from ..aes import aes_ctr_encrypt
from ..utils import (
    ExtractorError,
    int_or_none,
    join_nonempty,
    parse_resolution,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AbyssIE(InfoExtractor):
    IE_NAME = 'abyss'
    IE_DESC = 'Abyss.to / Hydrax'
    _PLAYER_HOSTS = r'(?:abysscdn\.com|playhydrax\.com|hydrax\.net|zplayer\.io)'
    _VALID_URL = (
        rf'https?://(?:www\.)?(?:'
        rf'(?:{_PLAYER_HOSTS})/(?:embed/?)?(?:\?(?:[^#]*&)?)?v='
        rf'|short\.(?:icu|ink)/'
        rf'|abyss\.to/\?(?:[^#]*&)?v='
        rf')(?P<id>[\w-]+)'
    )
    _EMBED_REGEX = [
        rf'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://(?:www\.)?(?:{_PLAYER_HOSTS})/\?(?:[^#]*&)?v=[\w-]+)\1',
    ]
    _TESTS = [
        {
            'url': 'https://playhydrax.com/?v=HzUikxGb4',
            'md5': 'f268c3440cddec7833309084a2d0edfb',
            'info_dict': {
                'id': 'HzUikxGb4',
                'ext': 'mp4',
                'title': '1.mp4',
            },
            'params': {
                'format': 'best[height=360][vcodec=avc1]',
            },
        },
        {
            'url': 'https://abysscdn.com/?v=HzUikxGb4',
            'only_matching': True,
        },
        {
            'url': 'https://short.icu/HzUikxGb4',
            'only_matching': True,
        },
        {
            'url': 'https://short.ink/HzUikxGb4',
            'only_matching': True,
        },
        {
            'url': 'https://abyss.to/?v=HzUikxGb4',
            'only_matching': True,
        },
    ]
    _FRAGMENT_SIZE = 2 * 1024 * 1024
    _CDN_HEADERS = {
        'Referer': 'https://abysscdn.com/',
        'Origin': 'https://abysscdn.com',
    }
    _VCODEC_MAP = {
        'h264': 'avc1',
        'av1': 'av01',
        'h265': 'hev1',
        'hevc': 'hev1',
    }

    @staticmethod
    def _aes_ctr(data, key):
        return bytes(aes_ctr_encrypt(list(data), list(key), list(key[:16])))

    @classmethod
    def _sora_token(cls, md5_id, res_id, size, index):
        path = f'/mp4/{md5_id}/{res_id}/{size}/{cls._FRAGMENT_SIZE}/{index}'.encode()
        key = hashlib.md5(bytes(int(d) for d in str(size) if d.isdigit())).hexdigest().encode()
        token = cls._aes_ctr(path, key)
        first = base64.b64encode(token).decode().replace('=', '')
        return base64.b64encode(first.encode()).decode().replace('=', '')

    def _decrypt_media(self, payload, video_id):
        media, user_id, slug, md5_id = (
            payload.get('media'),
            payload.get('user_id'),
            payload.get('slug') or video_id,
            payload.get('md5_id'),
        )
        if not media or user_id is None or md5_id is None:
            raise ExtractorError('Encrypted player metadata is missing', expected=True)
        key = hashlib.md5(f'{user_id}:{slug}:{md5_id}'.encode()).hexdigest().encode()
        try:
            plaintext = self._aes_ctr(media.encode('latin-1'), key).decode()
        except UnicodeDecodeError as e:
            raise ExtractorError(f'Unable to decrypt Abyss media metadata: {e}', expected=True)
        return self._parse_json(plaintext, video_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://playhydrax.com/?v={video_id}', video_id, impersonate=True)
        datas_b64 = self._search_regex(r'const\s+datas\s*=\s*"([^"]+)"', webpage, 'player datas')
        payload = json.loads(base64.b64decode(datas_b64).decode('latin-1'))
        media = self._decrypt_media(payload, video_id)
        mp4 = traverse_obj(media, ('mp4', {dict})) or {}
        md5_id = payload.get('md5_id')
        domains = traverse_obj(mp4, ('domains', ..., {str})) or []
        root = next((d.split('.', 1)[1] for d in domains if '.' in d), None)

        formats = []
        for src in traverse_obj(mp4, ('sources', ..., {dict})) or []:
            if src.get('status') is False:
                continue
            sub, res_id, size = src.get('sub'), int_or_none(src.get('res_id')), int_or_none(src.get('size'))
            if not sub or res_id is None or not size:
                continue
            host = next((d for d in domains if d == sub or d.startswith(f'{sub}.')), None)
            if not host:
                host = f'{sub}.{root}' if root else None
            if not host:
                continue
            fragment_count = (size + self._FRAGMENT_SIZE - 1) // self._FRAGMENT_SIZE
            fragments = [
                {
                    'url': f'https://{host}/sora/{size}/{self._sora_token(md5_id, res_id, size, i)}',
                }
                for i in range(fragment_count)
            ]
            codec, label = src.get('codec'), src.get('label')
            formats.append(
                {
                    'format_id': join_nonempty(label, codec, sub),
                    'ext': 'mp4',
                    'protocol': 'http_dash_segments',
                    'url': fragments[0]['url'],
                    'fragments': fragments,
                    'filesize': size,
                    'vcodec': self._VCODEC_MAP.get(codec, codec),
                    'http_headers': self._CDN_HEADERS,
                    **parse_resolution(label),
                },
            )

        hls_url = url_or_none(media.get('hls') if isinstance(media.get('hls'), str) else None) or traverse_obj(
            media, ('hls', 'url', {url_or_none}),
        )
        if hls_url:
            formats.extend(
                self._extract_m3u8_formats(
                    hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False, headers=self._CDN_HEADERS,
                ),
            )

        if not formats:
            raise ExtractorError('No playable Abyss formats found', expected=True)

        return {
            'id': video_id,
            'title': (
                str_or_none(payload.get('title'))
                or str_or_none(media.get('title'))
                or self._html_extract_title(webpage, default=None)
                or video_id
            ),
            'formats': formats,
            'http_headers': self._CDN_HEADERS,
        }
