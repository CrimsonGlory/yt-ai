import base64
import importlib
import io
import json
import os.path
import random
import struct

from .common import InfoExtractor
from ..aes import aes_cbc_decrypt_bytes, aes_ctr_decrypt, aes_ecb_decrypt, inc
from ..dependencies import Cryptodome
from ..downloader import PROTOCOL_MAP
from ..downloader.http import HttpFD
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


def _b64_url_decode(data):
    if not data:
        return b''
    if isinstance(data, str):
        data = data.encode()
    data += b'=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data)


def _aes_ecb_decrypt(data, key):
    if Cryptodome.AES:
        return Cryptodome.AES.new(key, Cryptodome.AES.MODE_ECB).decrypt(data)
    return bytes(aes_ecb_decrypt(list(data), list(key)))


def _unmerge_file_key(key):
    """Split a 32-byte MEGA file key into AES-128 key and CTR IV."""
    parts = struct.unpack('>8I', key)
    aes_key = struct.pack('>4I', *(parts[i] ^ parts[i + 4] for i in range(4)))
    iv = struct.pack('>4I', parts[4], parts[5], 0, 0)
    return aes_key, iv


class _NativeMegaCTR:
    """Streaming AES-128-CTR when pycryptodome is unavailable."""

    def __init__(self, key, iv, offset=0):
        self._key = list(key)
        self._counter = list(iv)
        for _ in range(offset // 16):
            self._counter = inc(self._counter)
        self._skip = offset % 16
        self._pending = b''

    def __call__(self, data):
        if not data:
            return b''
        chunk = self._pending + bytes(data)
        aligned = len(chunk) - (len(chunk) % 16)
        complete, self._pending = chunk[:aligned], chunk[aligned:]
        if not complete:
            return b''
        out = bytes(aes_ctr_decrypt(list(complete), self._key, self._counter))
        for _ in range(len(complete) // 16):
            self._counter = inc(self._counter)
        if self._skip:
            out = out[self._skip :]
            self._skip = 0
        return out

    def finalize(self):
        if not self._pending:
            return b''
        out = bytes(aes_ctr_decrypt(list(self._pending), self._key, self._counter))
        if self._skip:
            out = out[self._skip :]
            self._skip = 0
        self._pending = b''
        return out


def _mega_ctr_decryptor(key, iv, offset=0):
    if Cryptodome.AES:
        ident = getattr(Cryptodome, '_yt_dlp__identifier', 'Cryptodome')
        if ident == 'pycrypto':
            ident = 'Crypto'
        counter_mod = importlib.import_module(f'{ident}.Util.Counter')
        cipher = Cryptodome.AES.new(
            key,
            Cryptodome.AES.MODE_CTR,
            counter=counter_mod.new(128, initial_value=int.from_bytes(iv, 'big') + offset // 16),
        )
        skip = offset % 16
        if skip:
            cipher.decrypt(b'\0' * skip)
        return cipher.decrypt
    return _NativeMegaCTR(key, iv, offset)


class _MegaDecryptWriter:
    def __init__(self, stream, decryptor):
        self._stream = stream
        self._decryptor = decryptor

    def write(self, data):
        if data:
            data = self._decryptor(data)
        if data:
            return self._stream.write(data)
        return 0

    def close(self):
        finalize = getattr(self._decryptor, 'finalize', None)
        if finalize:
            rest = finalize()
            if rest:
                self._stream.write(rest)
        return self._stream.close()

    def flush(self):
        if hasattr(self._stream, 'flush'):
            return self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


class MegaFD(HttpFD):
    """HTTP downloader that AES-128-CTR decrypts MEGA ciphertext as it arrives."""

    FD_NAME = 'mega'

    def real_download(self, filename, info_dict):
        opts = info_dict.get('downloader_options') or {}
        self._mega_key = bytes.fromhex(opts['mega_aes_key'])
        self._mega_iv = bytes.fromhex(opts['mega_aes_iv'])
        return super().real_download(filename, info_dict)

    def sanitize_open(self, filename, open_mode):
        stream, filename = super().sanitize_open(filename, open_mode)
        offset = 0
        if 'a' in open_mode:
            try:
                offset = stream.tell()
            except (OSError, AttributeError, io.UnsupportedOperation):
                offset = 0
        decryptor = _mega_ctr_decryptor(self._mega_key, self._mega_iv, offset)
        return _MegaDecryptWriter(stream, decryptor), filename


PROTOCOL_MAP['mega'] = MegaFD


class MegaIE(InfoExtractor):
    IE_NAME = 'mega.nz'
    IE_DESC = 'MEGA'
    _VALID_URL = (
        r'https?://(?:www\.)?mega(?:\.co)?\.nz/'
        r'(?:'
        r'(?:file|embed)/(?P<file_id>[\w-]+)(?:#(?P<file_key>[\w=-]+))?'
        r'|\#!(?P<legacy_file_id>[\w-]+)(?:!(?P<legacy_file_key>[\w=-]+))?'
        r'|folder/(?P<folder_id>[\w-]+)(?:#(?P<folder_key>[\w=-]+)(?:/file/(?P<folder_file_id>[\w-]+))?)?'
        r'|\#F!(?P<legacy_folder_id>[\w-]+)(?:!(?P<legacy_folder_key>[\w=-]+))?'
        r')'
    )
    _API_URL = 'https://g.api.mega.co.nz/cs'
    _API_ERRORS = {
        -2: 'Invalid arguments',
        -3: 'Temporary MEGA API congestion; try again later',
        -4: 'Rate limited',
        -9: 'File not found',
        -11: 'Access denied',
        -16: 'This file has been blocked',
        -17: 'Over quota',
        -18: 'Temporarily unavailable',
    }
    _TESTS = [
        {
            'url': 'https://mega.nz/file/Wt0F1bpR#WlCGMYlOS_K23Q4wH5isOK7Oin6qsa2uyEAG3C5G3ro',
            'md5': 'de7adf3b89e4930f3d4ea1802f047858',
            'info_dict': {
                'id': 'Wt0F1bpR',
                'ext': 'mkv',
                'title': 'ffplay_2023_06_03_16_59_27_797',
                'filesize': 394690,
            },
        },
        {
            'url': 'https://mega.nz/#!Wt0F1bpR!WlCGMYlOS_K23Q4wH5isOK7Oin6qsa2uyEAG3C5G3ro',
            'only_matching': True,
        },
        {
            'url': 'https://mega.co.nz/file/Wt0F1bpR#WlCGMYlOS_K23Q4wH5isOK7Oin6qsa2uyEAG3C5G3ro',
            'only_matching': True,
        },
        {
            'url': 'https://mega.nz/embed/Wt0F1bpR#WlCGMYlOS_K23Q4wH5isOK7Oin6qsa2uyEAG3C5G3ro',
            'only_matching': True,
        },
        {
            'url': 'https://mega.nz/folder/e4diDZ7T#iJnegBO_m6OXBQp27lHCrg/file/KlVgwR4B',
            'only_matching': True,
        },
        {
            'url': 'https://mega.nz/folder/e4diDZ7T#iJnegBO_m6OXBQp27lHCrg',
            'only_matching': True,
        },
    ]

    def _api_request(self, video_id, payload, folder_id=None, note='Downloading MEGA metadata'):
        if not isinstance(payload, list):
            payload = [payload]
        query = {'id': random.randint(0, 0x0FFFFFFF)}
        if folder_id:
            query['n'] = folder_id
        last_error = None
        for _ in range(3):
            response = self._download_json(
                self._API_URL,
                video_id,
                note,
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'},
                query=query,
            )
            code = None
            if isinstance(response, int):
                code = response
            elif (
                isinstance(response, list)
                and response
                and isinstance(response[0], int)
                and not isinstance(response[0], bool)
            ):
                code = response[0]
            if code == -3:
                last_error = code
                continue
            if code is not None:
                raise ExtractorError(
                    self._API_ERRORS.get(code, f'MEGA API error {code}'), expected=True, video_id=video_id,
                )
            return response[0] if len(payload) == 1 and isinstance(response, list) else response
        raise ExtractorError(
            self._API_ERRORS.get(last_error, 'Temporary MEGA API congestion; try again later'),
            expected=True,
            video_id=video_id,
        )

    def _decrypt_attrs(self, at, aes_key, video_id):
        if not at or not aes_key:
            return {}
        try:
            raw = aes_cbc_decrypt_bytes(_b64_url_decode(at), aes_key, b'\0' * 16)
        except Exception:
            return {}
        if not raw.startswith(b'MEGA'):
            return {}
        try:
            text = raw[4:].rstrip(b'\0').decode('utf-8')
        except UnicodeDecodeError:
            return {}
        return self._parse_json(text, video_id, fatal=False) or {}

    def _node_file_key(self, node, share_key):
        enc = traverse_obj(node, ('k', {str}))
        if not enc or not share_key:
            return None
        enc_b64 = enc.split('/')[-1].split(':', 1)[-1]
        try:
            dec = _aes_ecb_decrypt(_b64_url_decode(enc_b64), share_key)
        except Exception:
            return None
        if len(dec) < 32:
            return None
        return dec[:32]

    def _info_from_file(self, video_id, file_key, api_data):
        if len(file_key) != 32:
            raise ExtractorError('Invalid MEGA file key', expected=True, video_id=video_id)
        aes_key, iv = _unmerge_file_key(file_key)
        attrs = self._decrypt_attrs(traverse_obj(api_data, ('at', {str})), aes_key, video_id)
        filename = traverse_obj(attrs, ('n', {str})) or video_id
        title, ext = os.path.splitext(filename)
        dl_url = traverse_obj(api_data, ('g', {url_or_none}))
        if not dl_url:
            raise ExtractorError('Unable to extract MEGA download URL', video_id=video_id)
        return {
            'id': video_id,
            'title': title or video_id,
            'url': dl_url,
            'ext': determine_ext(filename, default_ext=ext[1:] if ext else 'unknown_video'),
            'filesize': traverse_obj(api_data, ('s', {int_or_none})),
            'protocol': 'mega',
            'downloader_options': {
                'mega_aes_key': aes_key.hex(),
                'mega_aes_iv': iv.hex(),
            },
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        file_id = mobj.group('file_id') or mobj.group('legacy_file_id')
        file_key = mobj.group('file_key') or mobj.group('legacy_file_key')
        folder_id = mobj.group('folder_id') or mobj.group('legacy_folder_id')
        folder_key = mobj.group('folder_key') or mobj.group('legacy_folder_key')
        folder_file_id = mobj.group('folder_file_id')

        if file_id:
            if not file_key:
                raise ExtractorError(
                    'This MEGA URL is missing the decryption key (the part after #)', expected=True, video_id=file_id,
                )
            file_key_bytes = _b64_url_decode(file_key)
            api_data = self._api_request(file_id, {'a': 'g', 'g': 1, 'ssl': 2, 'p': file_id})
            return self._info_from_file(file_id, file_key_bytes, api_data)

        if not folder_id:
            raise ExtractorError('Unable to extract MEGA id', expected=True)
        if not folder_key:
            raise ExtractorError(
                'This MEGA folder URL is missing the decryption key (the part after #)',
                expected=True,
                video_id=folder_id,
            )

        share_key = _b64_url_decode(folder_key)
        listing = self._api_request(
            folder_id, {'a': 'f', 'c': 1, 'r': 1, 'ca': 1}, folder_id=folder_id, note='Downloading MEGA folder listing',
        )
        nodes = traverse_obj(listing, ('f', ..., {dict})) or []
        if folder_file_id:
            node = next((n for n in nodes if n.get('h') == folder_file_id and n.get('t') == 0), None)
            if not node:
                raise ExtractorError('File not found in MEGA folder', expected=True, video_id=folder_file_id)
            file_key_bytes = self._node_file_key(node, share_key)
            if not file_key_bytes:
                raise ExtractorError('Unable to decrypt MEGA file key', expected=True, video_id=folder_file_id)
            api_data = self._api_request(
                folder_file_id, {'a': 'g', 'g': 1, 'ssl': 2, 'n': folder_file_id}, folder_id=folder_id,
            )
            return self._info_from_file(folder_file_id, file_key_bytes, api_data)

        def entries():
            for node in nodes:
                if node.get('t') != 0:
                    continue
                node_id = node.get('h')
                if not node_id:
                    continue
                yield self.url_result(
                    f'https://mega.nz/folder/{folder_id}#{folder_key}/file/{node_id}', self.ie_key(), node_id,
                )

        folder_title = None
        handles = {n.get('h') for n in nodes}
        root = next((n for n in nodes if n.get('t') == 1 and n.get('p') not in handles), None)
        if root and share_key:
            try:
                enc = (root.get('k') or '').split('/')[-1].split(':', 1)[-1]
                root_key = _aes_ecb_decrypt(_b64_url_decode(enc), share_key)
                folder_title = traverse_obj(self._decrypt_attrs(root.get('a'), root_key[:16], folder_id), ('n', {str}))
            except Exception:
                pass
        return self.playlist_result(entries(), folder_id, folder_title)
