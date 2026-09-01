import base64
import hashlib
import json
import os
import re
import time
import urllib.parse

from .common import InfoExtractor
from ..dependencies import Cryptodome
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
    urljoin,
)
from ..utils.traversal import traverse_obj


class HanimeIE(InfoExtractor):
    IE_NAME = 'hanime'
    IE_DESC = 'hanime.tv'
    _VALID_URL = (
        r'https?://(?:www\.)?hanime\.tv/'
        r'(?:videos/hentai|hentai/video|playlists/[0-9a-z]+/video)/'
        r'(?P<id>[\w-]+)')
    _TESTS = [{
        'url': 'https://hanime.tv/videos/hentai/kanojo-x-kanojo-x-kanojo-1',
        'md5': 'dbd458569b79584cae4a7b3c38d1f10e',
        'info_dict': {
            'id': 'kanojo-x-kanojo-x-kanojo-1',
            'ext': 'mp4',
            'title': 'Kanojo x Kanojo x Kanojo 1',
            'description': 'md5:1cc4961cccaac13b35f50d1f0a79ef42',
            'thumbnail': r're:https?://hanime-cdn\.com/.+',
            'duration': 1780,
            'timestamp': 1261699200,
            'upload_date': '20091225',
            'tags': list,
            'age_limit': 18,
        },
        'params': {'format': '720p'},
    }, {
        'url': 'https://hanime.tv/videos/hentai/fuzzy-lips-2',
        'only_matching': True,
    }, {
        'url': 'https://hanime.tv/hentai/video/kanojo-x-kanojo-x-kanojo-1',
        'only_matching': True,
    }, {
        'url': 'https://hanime.tv/playlists/duuilob7bmyefj5kikbx/video/first-love-1',
        'only_matching': True,
    }]
    _SITE = 'https://hanime.tv'
    _HANDSHAKE_URL = 'https://auth.hanime.tv/api/v11/handshake'
    _AES_KEY = bytes.fromhex('5d657a4dcb0bad1c637ff2e221059b10ff17ae39fe855003e846918941f4ebe3')
    _AES_HEADER = b'htv-insecure-v1'

    @staticmethod
    def _b64encode(data):
        return base64.urlsafe_b64encode(data).decode().rstrip('=')

    @staticmethod
    def _b64decode(data):
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64decode(data + b'=' * (-len(data) % 4))

    @classmethod
    def _digest_token(cls, payload):
        iv = os.urandom(12)
        cipher = Cryptodome.AES.new(cls._AES_KEY, Cryptodome.AES.MODE_GCM, nonce=iv)
        cipher.update(cls._AES_HEADER)
        ciphertext, tag = cipher.encrypt_and_digest(json.dumps(payload).encode())
        return cls._b64encode(json.dumps({
            'v': 1,
            'alg': 'AES-256-GCM',
            'iv': cls._b64encode(iv),
            'tag': cls._b64encode(tag),
            'data': cls._b64encode(ciphertext),
        }).encode())

    @classmethod
    def _parse_token(cls, token):
        envelope = json.loads(cls._b64decode(token))
        cipher = Cryptodome.AES.new(
            cls._AES_KEY, Cryptodome.AES.MODE_GCM, nonce=cls._b64decode(envelope['iv']))
        cipher.update(cls._AES_HEADER)
        plaintext = cipher.decrypt_and_verify(
            cls._b64decode(envelope['data']), cls._b64decode(envelope['tag']))
        return json.loads(plaintext)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if not Cryptodome.AES:
            raise ExtractorError(
                'pycryptodomex is required to download from hanime.tv', expected=True)

        ts = int(time.time())
        signature = hashlib.sha256(
            f'{ts},Xkdi29,https://hanime.tv,mn2,{ts}'.encode()).hexdigest()
        payload = self._digest_token({
            'timestamp_unix': ts,
            'directive': 'htv_player_handshake',
            'slug': video_id,
        })
        _, urlh = self._download_webpage_handle(
            self._HANDSHAKE_URL, video_id, 'Downloading video manifest',
            data=json.dumps({'token': payload}).encode(),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Origin': self._SITE,
                'Referer': f'{self._SITE}/',
                'X-Csrf-Token': 'null',
                'X-Signature': signature,
                'X-Signature-Version': 'web2',
                'X-Time': str(ts),
            })
        token = urlh.headers.get('X-Token')
        if not token:
            raise ExtractorError('No X-Token in handshake response', expected=True)
        try:
            manifest = self._parse_token(token)
        except (ValueError, KeyError, TypeError) as e:
            raise ExtractorError(f'Unable to decrypt video manifest: {e}', expected=True)

        formats = []
        headers = {'Referer': f'{self._SITE}/'}
        for source in traverse_obj(manifest, ('sources', ..., {dict})) or []:
            if source.get('kind') != 'normal':
                continue
            src = urljoin(self._SITE, source.get('src'))
            if not src:
                continue
            label = source.get('label') or 'hls'
            media_fmts = self._extract_m3u8_formats(
                src, video_id, 'mp4', m3u8_id=label, fatal=False, headers=headers)
            height, width = int_or_none(source.get('height')), int_or_none(source.get('width'))
            for f in media_fmts:
                f.setdefault('http_headers', headers)
                if height:
                    f.setdefault('height', height)
                if width:
                    f.setdefault('width', width)
            formats.extend(media_fmts)
        if not formats:
            raise ExtractorError('No public video formats found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('id', None)

        return {
            **json_ld,
            'id': video_id,
            'title': (
                self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                or json_ld.get('title') or self._og_search_title(webpage)),
            'description': json_ld.get('description') or self._og_search_description(webpage),
            'thumbnail': json_ld.get('thumbnail') or self._og_search_thumbnail(webpage),
            'tags': orderedSet(urllib.parse.unquote(t) for t in re.findall(
                r'href="/browse/tags/([^"]+)"', webpage)) or None,
            'formats': formats,
            'age_limit': 18,
        }
