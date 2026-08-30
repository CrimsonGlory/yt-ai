import base64
import hashlib
import json
import time
import urllib.parse

from .common import InfoExtractor
from ..dependencies import Cryptodome
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    traverse_obj,
)
from ..utils.networking import std_headers


class SyncIE(InfoExtractor):
    IE_NAME = 'sync.com'
    IE_DESC = 'Sync.com'
    _VALID_URL = (
        r'https?://(?:www\.|ln\d+\.)?sync\.com/dl/(?P<id>[0-9a-z]+)'
        r'(?:/(?!view)(?P<linkkey>[0-9A-Za-z-]+))?'
        r'(?:/view/(?P<kind>[^/?#]+)/(?P<file_id>\d+))?'
    )
    _TESTS = [
        {
            'url': 'https://ln5.sync.com/dl/3d719b430/view/video/12212879360005?sync_id=0#yx6btme5-dchjnshf-gwkxn42k-57mv8axd',
            'md5': '3e85067c3bd2c333c4a23c1f3ab48e6a',
            'info_dict': {
                'id': '12212879360005',
                'ext': 'mp4',
                'title': 'LOST S1E19 Deus Ex Machina UNCUT-014',
                'filesize': 2506065487,
                'timestamp': 1650684915,
                'upload_date': '20220423',
                'display_id': '3d719b430',
            },
        },
        {
            'url': 'https://ln5.sync.com/dl/3d719b430#yx6btme5-dchjnshf-gwkxn42k-57mv8axd',
            'only_matching': True,
        },
        {
            'url': 'https://ln1.sync.com/dl/abc123def/view/audio/1',
            'only_matching': True,
        },
    ]
    _APP_VERSION = '3.1.38'
    _COMPAT_PUBKEY = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsRA0ObSDjWc1ErNAQeN5
9WJLFNTBLHP5pGsDnRNXJfX0GkGB/PRV3vTv7OOUllZgy2J4sSnc/lZit50DcuNk
TAFU3BvNxh2qJfdVxhzdSPRw2hFnnEz4rN9+VuCbEcz4QGiVX2j3jqZLJyioJr5Q
ei+UeAcOnjHBP47H2On4sMdDyec2pSjTCsh0ZzfqSJRPRgzPJnDwwjCuBTbrV4XK
z/wfw9zFoNmwouu4z72Yg8JPO7DS0jmHR1z1CZwKdoq1BXyg9F3w+eRfaV9lQZ2e
SGbUGps3CYiHYrgqTwAfHEH1CK7ENGQW6Dd41k27N1EJyZKEN56c6G/+lHEGts20
FQIDAQAB
-----END PUBLIC KEY-----'''
    _MIME_TYPES = {
        '3gp': 'video/3gpp',
        'aac': 'audio/aac',
        'asf': 'video/x-ms-asf',
        'avi': 'video/avi',
        'flv': 'video/x-flv',
        'm4a': 'audio/mp4',
        'm4p': 'video/mp4',
        'm4v': 'video/mp4',
        'mkv': 'video/x-matroska',
        'mov': 'video/quicktime',
        'mp3': 'audio/mp3',
        'mp4': 'video/mp4',
        'mpeg': 'video/mpeg',
        'mpg': 'video/mpeg',
        'ogg': 'video/ogg',
        'ogv': 'video/ogg',
        'wav': 'audio/wav',
        'webm': 'video/webm',
        'wmv': 'video/wmv',
    }

    def _user_agent(self):
        return traverse_obj(self.get_param('http_headers'), 'User-Agent', {str}) or std_headers['User-Agent']

    def _call_api(self, host, command, video_id, data, note):
        response = self._download_json(
            f'https://{host}/api/v1/{command}',
            video_id,
            note,
            data=json.dumps(data).encode(),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Origin': f'https://{host}',
            },
            expected_status=(400, 403, 404),
        )
        if traverse_obj(response, 'success'):
            return response
        error_code = traverse_obj(response, 'error_code', {int})
        message = traverse_obj(response, ('errors', 0, 'error_msg'), {str}) or 'API error'
        if error_code == 8018:
            raise ExtractorError('Password-protected share, use --video-password', expected=True)
        if error_code == 8019:
            raise ExtractorError('Incorrect share password', expected=True)
        if error_code == 8020:
            raise ExtractorError('This share link has expired', expected=True)
        raise ExtractorError(f'{self.IE_NAME} said: {message}', expected=True)

    def _require_crypto(self):
        if not Cryptodome.AES or not Cryptodome.RSA or not Cryptodome.PKCS1_v1_5:
            raise ExtractorError('pycryptodomex is required to download from Sync.com', expected=True)

    def _aes_gcm_decrypt(self, key, blob):
        iv, rest = blob[:12], blob[12:]
        return Cryptodome.AES.new(
            key,
            Cryptodome.AES.MODE_GCM,
            nonce=iv,
            mac_len=12,
        ).decrypt_and_verify(rest[:-12], rest[-12:])

    def _rsa_encrypt(self, plaintext):
        cipher = Cryptodome.PKCS1_v1_5.new(Cryptodome.RSA.importKey(self._COMPAT_PUBKEY))
        for _ in range(20):
            encrypted = base64.b64encode(cipher.encrypt(plaintext.encode())).decode()
            if len(encrypted) == 344:
                return encrypted
        raise ExtractorError('Unable to encrypt Sync.com download key')

    def _share_key(self, password, meta):
        if int_or_none(meta.get('linkversion'), default=2) == 2:
            salt = bytes.fromhex(meta['salt'])
            iterations = int_or_none(meta.get('iterations')) or 10000
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations, dklen=64)
        try:
            key = base64.b64decode(password)
        except (ValueError, TypeError):
            key = b''
        if len(key) != 64:
            raise ExtractorError('Unable to derive Sync.com share key', expected=True)
        return key

    def _decrypt_name(self, enc_share_name, share_key):
        blob = base64.b64decode(enc_share_name.split(':', 1)[-1])
        return self._aes_gcm_decrypt(share_key[32:], blob).decode()

    def _decrypt_datakey(self, enc_data_key, share_key):
        blob = base64.b64decode(enc_data_key.split(':', 1)[-1])
        return self._aes_gcm_decrypt(share_key[:32], blob)

    def _b64(self, data):
        return base64.b64encode(data if isinstance(data, bytes) else data.encode()).decode().rstrip('=')

    def _compat_url(self, host, item, meta, data_key, video_id, filename, mime_type):
        ua = self._user_agent()
        page_url = f"https://{host}/dl/{item['link_id']}"
        header2 = (
            f'Content-Disposition: attachment; filename="{urllib.parse.quote(filename)}";'
            f"filename*=UTF-8''{urllib.parse.quote(filename)};"
        )
        signed = self._call_api(
            host,
            'linksignrequest',
            video_id,
            {
                'req': {
                    'sharelink_id': item['sync_id'],
                    'linkoid': meta['oid'],
                    'linkcachekey': item['link_id'],
                    'mode': 101,
                    'datakey': self._rsa_encrypt(base64.b64encode(data_key).decode()).replace('=', ''),
                    'header1': self._b64(f'Content-Type: {mime_type}'),
                    'header2': self._b64(header2),
                    'uagent': hashlib.sha1(ua.encode()).hexdigest(),
                    'ipaddress': 's',
                    'errurl': self._rsa_encrypt(base64.b64encode(page_url.encode()).decode()).replace('=', ''),
                    'timestamp': int(time.time() * 1000),
                    'engine': f'ln-{self._APP_VERSION}',
                },
            },
            'Signing download request',
        )
        params = traverse_obj(signed, ('response', {dict}))
        if not params:
            raise ExtractorError('Unable to sign Sync.com download request')
        query = '&'.join(f'{key}={value}' for key, value in params.items())
        pltoken = traverse_obj(signed, 'pltoken', {str})
        if pltoken:
            query += f'&pltoken={pltoken}'
        dl_host = traverse_obj(meta, ('servers_compat', 0), ('servers_web', 0), {str})
        if not dl_host:
            raise ExtractorError('Unable to determine Sync.com download host')
        return f"https://{dl_host}/p/{urllib.parse.quote(filename)}?{query}&cachekey={item['cachekey']}"

    def _extract_file(self, host, item, meta, share_key, datakeys, video_id):
        filename = item['name']
        ext = determine_ext(filename, default_ext='mp4')
        mime_type = self._MIME_TYPES.get(ext, 'application/octet-stream')
        enc_data_key = traverse_obj(datakeys, (str(item['sync_id']), 'enc_data_key', {str}))
        if not enc_data_key:
            raise ExtractorError('Unable to extract Sync.com file key')
        data_key = self._decrypt_datakey(enc_data_key, share_key)
        url = self._compat_url(host, item, meta, data_key, video_id, filename, mime_type)
        timestamp = int_or_none(item.get('date'), scale=1000)
        return {
            'id': str(item['sync_id']),
            'display_id': item['link_id'],
            'title': filename.rsplit('.', 1)[0] if '.' in filename else filename,
            'ext': ext,
            'filesize': int_or_none(item.get('size')),
            'timestamp': timestamp,
            'url': url,
            'http_headers': {
                'User-Agent': self._user_agent(),
                'Referer': f"https://{host}/dl/{item['link_id']}",
            },
        }

    def _real_extract(self, url):
        self._require_crypto()
        urlp = urllib.parse.urlparse(url)
        mobj = self._match_valid_url(url)
        link_id = mobj.group('id')
        file_id = mobj.group('file_id')
        host = urlp.netloc
        share_password = self._search_regex(
            r'[^0-9A-Za-z-]*([0-9A-Za-z-]+)', mobj.group('linkkey') or urlp.fragment or '', 'share key', default=None,
        )
        if not share_password:
            raise ExtractorError(
                'This Sync.com share requires the secret key from the URL fragment (after #)', expected=True,
            )

        query = urllib.parse.parse_qs(urlp.query)
        api_sync_id = int_or_none(file_id) or int_or_none(traverse_obj(query, ('sync_id', 0))) or 0
        passwordlock = None
        video_password = self.get_param('videopassword')
        if video_password:
            passwordlock = hashlib.sha1(video_password.encode()).hexdigest()

        payload = {'publink_id': link_id, 'sync_id': api_sync_id}
        if passwordlock:
            payload['passwordlock'] = passwordlock
        meta = self._call_api(host, 'linkpathlist', file_id or link_id, payload, 'Downloading share metadata')

        share_key = self._share_key(share_password, meta)
        files = []
        for item in traverse_obj(meta, ('pathitems', ..., {dict})) or []:
            if item.get('type') and item.get('type') != 'file':
                continue
            enc_name = item.get('enc_share_name')
            if not enc_name:
                continue
            try:
                name = self._decrypt_name(enc_name, share_key)
            except (ValueError, TypeError, KeyError):
                self.report_warning(f"Unable to decrypt filename for {item.get('sync_id')}")
                continue
            files.append(
                {
                    **item,
                    'name': name,
                    'link_id': link_id,
                    'sync_id': item.get('sync_id') or item.get('id'),
                },
            )
        if not files:
            raise ExtractorError('No files found in this Sync.com share', expected=True)

        if file_id:
            files = [item for item in files if str(item.get('sync_id')) == str(file_id)]
            if not files:
                raise ExtractorError('Requested file was not found in this share', expected=True)

        pathdata = self._call_api(
            host,
            'pathdata',
            file_id or link_id,
            {
                'pathitems': [
                    {
                        'share_id': item.get('share_id'),
                        'blob_id': item.get('blob_id'),
                        'sync_id': item.get('sync_id'),
                        'ext': self._b64(determine_ext(item['name'], default_ext='bin')),
                        'link_cachekey': link_id,
                        'size': item.get('size'),
                        'user_id': None,
                    }
                    for item in files
                ],
            },
            'Downloading file keys',
        )
        datakeys = traverse_obj(pathdata, ('datakeys', {dict})) or {}

        if len(files) == 1:
            return self._extract_file(host, files[0], meta, share_key, datakeys, files[0]['sync_id'])

        return self.playlist_result(
            (self._extract_file(host, item, meta, share_key, datakeys, item['sync_id']) for item in files), link_id,
        )
