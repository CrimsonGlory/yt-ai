import base64
import gzip
import hashlib
import hmac
import json
import time
import uuid

from .common import InfoExtractor
from ..dependencies import Cryptodome
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


def _load_des():
    try:
        from Cryptodome.Cipher import DES
        return DES
    except ImportError:
        from Crypto.Cipher import DES
        return DES


class SklandIE(InfoExtractor):
    IE_NAME = 'skland'
    IE_DESC = '森空岛'
    _VALID_URL = r'https?://(?:www\.|m\.)?skland\.com/article\?(?:[^#]*&)?id=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.skland.com/article?id=2944931',
        'md5': '98e6a0e2e27d3768c581bcc719bbbce3',
        'info_dict': {
            'id': '2944931',
            'ext': 'mp4',
            'title': '安乐天使绘画过程~（动态壁纸锐意制作中~！）',
            'thumbnail': r're:https://bbs\.hycdn\.cn/.+',
            'duration': 95,
            'timestamp': 1749022574,
            'upload_date': '20250604',
            'uploader': '小狗神经',
            'uploader_id': '9284252597057',
            'tags': ['明日方舟', '新约能天使', '蕾缪安', '众生行记'],
            'like_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://m.skland.com/article?id=2944931',
        'only_matching': True,
    }]
    _API_BASE = 'https://zonai.skland.com'
    _SM_API = 'https://fp-it.portal101.cn/deviceprofile/v4'
    _SM_ORGANIZATION = 'UWXspnCCJN4sfYlNfqps'
    _SM_PUBLIC_KEY = (
        'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCmxMNr7n8ZeT0tE1R9j/mPixoinPkeM+k4VGIn/'
        's0k7N5rJAfnZ0eMER+QhwFvshzo0LNmeUkpR8uIlU/GEVr8mN28sKmwd2gpygqj0ePnBmOW4v0ZVwbS'
        'YK+izkhVFk2V/doLoMbWy6b+UnA8mkjvg0iYWRByfRsK2gdl7llqCwIDAQAB')
    _DES_RULE = {
        'appId': ('xx', 'uy7mzc4h'),
        'box': ('jf', None),
        'canvas': ('yk', 'snrn887t'),
        'clientSize': ('zx', 'cpmjjgsu'),
        'organization': ('dp', '78moqjfc'),
        'os': ('pj', 'je6vk6t4'),
        'platform': ('gm', 'pakxhcd2'),
        'plugins': ('kq', 'v51m3pzl'),
        'pmf': ('vw', '2mdeslu3'),
        'protocol': ('protocol', None),
        'referer': ('ab', 'y7bmrjlc'),
        'res': ('hf', 'whxqm2a7'),
        'rtype': ('lo', 'x8o2h2bl'),
        'sdkver': ('sc', '9q3dcxp2'),
        'status': ('an', '2jbrxxw4'),
        'subVersion': ('ns', 'eo3i2puh'),
        'svm': ('qr', 'fzj3kaeh'),
        'time': ('nb', 'q2t3odsk'),
        'timezone': ('as', '1uv05lj5'),
        'tn': ('py', 'x9nzj1bp'),
        'trees': ('pi', 'acfs0xo4'),
        'ua': ('bj', 'k92crp1t'),
        'url': ('cf', 'y95hjkoo'),
        'version': ('version', None),
        'vpw': ('ca', 'r9924ab5'),
    }
    _BROWSER_ENV = {
        'plugins': 'MicrosoftEdgePDFPluginPortableDocumentFormatinternal-pdf-viewer1,MicrosoftEdgePDFViewermhjfbmdgcfjbbpaeojofohoefgiehjai1',
        'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
        'canvas': '259ffe69',
        'timezone': -480,
        'platform': 'Win32',
        'url': 'https://www.skland.com/',
        'referer': '',
        'res': '1920_1080_24_1.25',
        'clientSize': '0_0_1080_1920_1920_1080_1920_1080',
        'status': '0011',
    }

    def _real_initialize(self):
        self._did = None
        self._token = ''

    def _require_crypto(self):
        if not Cryptodome.AES or not Cryptodome.RSA or not Cryptodome.PKCS1_v1_5:
            raise ExtractorError(
                'pycryptodomex is required to download from skland.com', expected=True)

    @staticmethod
    def _zero_pad(data, block=8):
        return data + b'\x00' * (block - len(data) % block)

    @classmethod
    def _tn_hash(cls, obj):
        parts = []
        for key in sorted(obj):
            value = obj[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                parts.append(str(int(value * 10000)))
            elif isinstance(value, dict):
                parts.append(cls._tn_hash(value))
            else:
                parts.append(str(value))
        return ''.join(parts)

    def _des_obfuscate(self, obj):
        des = _load_des()
        result = {}
        for key, value in obj.items():
            rule = self._DES_RULE.get(key)
            if not rule:
                result[key] = value
                continue
            name, des_key = rule
            if not des_key:
                result[name] = value
                continue
            cipher = des.new(des_key.encode(), des.MODE_ECB)
            encrypted = cipher.encrypt(self._zero_pad(str(value).encode()))
            result[name] = base64.b64encode(encrypted).decode()
        return result

    def _get_smid(self):
        now = time.localtime()
        time_str = time.strftime('%Y%m%d%H%M%S', now)
        uid_hash = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()
        base = f'{time_str}{uid_hash}00'
        smsk = hashlib.md5(f'smsk_web_{base}'.encode()).hexdigest()[:14]
        return f'{base}{smsk}0'

    def _get_device_id(self, video_id):
        self._require_crypto()
        uid = str(uuid.uuid4()).encode()
        aes_key = hashlib.md5(uid).hexdigest()[:16].encode()
        public_key = Cryptodome.RSA.importKey(base64.b64decode(self._SM_PUBLIC_KEY))
        ep = base64.b64encode(Cryptodome.PKCS1_v1_5.new(public_key).encrypt(uid)).decode()

        now_ms = int(time.time() * 1000)
        payload = {
            **self._BROWSER_ENV,
            'vpw': str(uuid.uuid4()),
            'svm': now_ms,
            'trees': str(uuid.uuid4()),
            'pmf': now_ms,
            'protocol': 102,
            'organization': self._SM_ORGANIZATION,
            'appId': 'default',
            'os': 'web',
            'version': '3.0.0',
            'sdkver': '3.0.0',
            'box': '',
            'rtype': 'all',
            'smid': self._get_smid(),
            'subVersion': '1.0.0',
            'time': 0,
        }
        payload['tn'] = hashlib.md5(self._tn_hash(payload).encode()).hexdigest()

        gzipped = base64.b64encode(gzip.compress(
            json.dumps(self._des_obfuscate(payload), separators=(',', ':'), ensure_ascii=False).encode(),
            compresslevel=2, mtime=0))
        aes = Cryptodome.AES.new(aes_key, Cryptodome.AES.MODE_CBC, b'0102030405060708')
        data = aes.encrypt(self._zero_pad(gzipped, 16)).hex()

        sm_resp = self._download_json(
            self._SM_API, video_id, 'Fetching Skland device id',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'appId': 'default',
                'compress': 2,
                'data': data,
                'encode': 5,
                'ep': ep,
                'organization': self._SM_ORGANIZATION,
                'os': 'web',
            }, separators=(',', ':')).encode())
        device_id = traverse_obj(sm_resp, ('detail', 'deviceId', {str}))
        if sm_resp.get('code') != 1100 or not device_id:
            raise ExtractorError(
                f'Unable to obtain Skland device id: {sm_resp.get("message") or sm_resp.get("code")}',
                expected=True)
        return f'B{device_id}'

    def _signed_headers(self, path, query=''):
        if not self._did:
            return {}
        timestamp = str(int(time.time()) - 2)
        header_ca = {
            'platform': '3',
            'timestamp': timestamp,
            'dId': self._did,
            'vName': '1.0.0',
        }
        raw = f'{path}{query}{timestamp}{json.dumps(header_ca, separators=(",", ":"))}'
        digest = hmac.new((self._token or '').encode(), raw.encode(), hashlib.sha256).hexdigest()
        return {
            'Referer': 'https://www.skland.com/',
            'Origin': 'https://www.skland.com',
            'sign': hashlib.md5(digest.encode()).hexdigest(),
            **header_ca,
        }

    def _call_api(self, path, video_id, query='', note=None):
        url = f'{self._API_BASE}{path}'
        if query:
            url = f'{url}?{query}'
        return self._download_json(
            url, video_id, note=note, headers=self._signed_headers(path, query),
            expected_status=(400, 401))

    def _refresh_token(self, video_id):
        resp = self._call_api('/web/v1/auth/refresh', video_id, note='Refreshing Skland token')
        token = traverse_obj(resp, ('data', 'token', {str}))
        if resp.get('code') != 0 or not token:
            raise ExtractorError(
                f'Unable to refresh Skland token: {resp.get("message") or resp.get("code")}',
                expected=True)
        self._token = token

    def _download_item(self, video_id):
        if not self._did:
            self._did = self._get_device_id(video_id)
        query = f'id={video_id}'
        for attempt in range(2):
            if not self._token:
                self._refresh_token(video_id)
            resp = self._call_api(
                '/web/v2/item', video_id, query, note='Downloading article JSON')
            code = resp.get('code')
            if code == 0:
                return traverse_obj(resp, ('data', {dict})) or {}
            if code in (10000, 10003) and attempt == 0:
                self._token = ''
                continue
            if code == 10002:
                self.raise_login_required(resp.get('message') or 'Login required')
            raise ExtractorError(
                resp.get('message') or f'Skland API error {code}', expected=True)
        raise ExtractorError('Unable to download Skland article', expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_item(video_id)
        item = traverse_obj(data, ('item', {dict})) or {}

        video = None
        for candidate in traverse_obj(item, ('videoList', ..., {dict})) or []:
            status = candidate.get('status')
            if status == 'transcoded':
                video = candidate
                break
            if status == 'transcoding' and video is None:
                video = candidate
        if not video:
            raise ExtractorError('This post does not contain a video', expected=True)
        if video.get('status') == 'transcoding':
            raise ExtractorError('This video is still transcoding', expected=True)
        if video.get('status') == 'transcode_failed':
            raise ExtractorError('Skland failed to transcode this video', expected=True)

        formats, subtitles = [], {}
        for stream in traverse_obj(video, ('infos', lambda _, v: url_or_none(v.get('url')))):
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                stream['url'], video_id, 'mp4', m3u8_id=stream.get('resolution'),
                fatal=False)
            for fmt in fmts:
                fmt.setdefault('width', int_or_none(stream.get('width')))
                fmt.setdefault('height', int_or_none(stream.get('height')))
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if not formats:
            raise ExtractorError('No video formats found', video_id=video_id)

        return {
            'id': str_or_none(item.get('id')) or video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': traverse_obj(
                item,
                ('videoList', 0, 'cover', 'url', {url_or_none}),
                ('imageList', 0, 'url', {url_or_none})),
            **traverse_obj(item, {
                'title': ('title', {str}),
                'timestamp': (('publishedAtTs', 'createdAtTs'), {int_or_none}, any),
                'duration': ('videoList', 0, 'infos', 0, 'duration', {int_or_none(scale=1000)}),
            }),
            **traverse_obj(data, {
                'uploader': ('user', 'nickname', {str}),
                'uploader_id': ('user', 'id', {str_or_none}),
                'tags': ('tags', ..., 'name', {str}, all),
                'like_count': ('itemRts', 'liked', {int_or_none}),
                'comment_count': ('itemRts', 'commented', {int_or_none}),
            }),
        }
