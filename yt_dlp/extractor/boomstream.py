import base64

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BoomstreamIE(InfoExtractor):
    IE_NAME = 'boomstream'
    IE_DESC = 'Boomstream'
    _VALID_URL = r'https?://play\.boomstream\.com/(?:player\.html\?(?:[^#]*&)?code=)?(?P<id>[A-Za-z0-9]{8})(?:[/?#]|$)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://play\.boomstream\.com/[A-Za-z0-9]{8}[^"\']*)\1']
    _TESTS = [{
        'url': 'https://play.boomstream.com/VCcNtuiw',
        'md5': '139cedfa14afb297905489c520fe9577',
        'info_dict': {
            'id': 'VCcNtuiw',
            'ext': 'mp4',
            'title': 'Promo Boomstream (RU)',
            'duration': 61.0,
            'thumbnail': r're:https?://cdn-g-img\.boomstream\.com/.+',
            'width': 1280,
            'height': 720,
            'hls_aes': {
                'key': '7146336a337537545034727055476733',
                'iv': '54524334474f34654e4d627072484a35',
            },
        },
    }, {
        'url': 'https://play.boomstream.com/fa11f2il',
        'only_matching': True,
    }, {
        'url': 'https://play.boomstream.com/player.html?code=VCcNtuiw',
        'only_matching': True,
    }, {
        'url': 'https://play.boomstream.com/VCcNtuiw?controls=0',
        'only_matching': True,
    }]
    # Player constants from videojs-hls-boomstream (`_p` / `kp`).
    _XOR_KEY = 'bv17b7v24iedrvzoaihwvugef89ewy7834f35'
    _DEFAULT_TOKEN_TO_DECRYPT = '001a5068005b176d560504'

    @staticmethod
    def _xor_bytes(data, key):
        key = key.encode() if isinstance(key, str) else key
        if isinstance(data, str):
            data = data.encode()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    @classmethod
    def _xor_decrypt_hex(cls, hex_str, key):
        return cls._xor_bytes(bytes.fromhex(hex_str), key).decode('latin-1')

    @classmethod
    def _media_xor_key(cls, media_data):
        return traverse_obj(media_data, ('tokenToDecrypt', {str})) or cls._xor_decrypt_hex(
            cls._DEFAULT_TOKEN_TO_DECRYPT, cls._XOR_KEY)

    @staticmethod
    def _decode_b64(value):
        if not value:
            return None
        try:
            return base64.b64decode(value).decode()
        except (ValueError, TypeError):
            return None

    def _extract_hls_aes(self, media_ready, token, xor_key, api_base, video_id, referer):
        decrypted = self._xor_decrypt_hex(media_ready, xor_key)
        iv = decrypted[20:36].encode('latin-1').hex()
        key_path = self._xor_bytes(decrypted[:20] + token, xor_key).hex()
        key_url = f'{api_base.rstrip("/")}/process/{key_path}'
        urlh = self._request_webpage(
            key_url, video_id, 'Downloading HLS AES key',
            headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': referer,
            })
        aes_key = urlh.read()
        if len(aes_key) not in (16, 24, 32):
            raise ExtractorError('Invalid HLS AES key length')
        return {
            'key': aes_key.hex(),
            'iv': iv,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if 'Video is not found' in webpage:
            raise ExtractorError('Video is not found', expected=True)

        config = self._search_json(
            r'window\.boomstreamConfig\s*=', webpage, 'player config', video_id)

        error = traverse_obj(config, ('error', {dict})) or {}
        if error.get('code'):
            raise ExtractorError(clean_html(
                error.get('translate') or error.get('message')
                or f'Boomstream error {error["code"]}'), expected=True)

        media_data = config.get('mediaData')
        if isinstance(media_data, list):
            media_data = next((
                item for item in media_data
                if traverse_obj(item, ('links', 'hls'))), None)
        record = traverse_obj(media_data, ('records', 0, {dict}))
        if traverse_obj(record, ('links', 'hls')):
            media_data = record
        if not isinstance(media_data, dict):
            media_data = {}

        hls_url = self._decode_b64(traverse_obj(media_data, ('links', 'hls', {str})))
        if not hls_url:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        is_live = bool(config.get('isLive') or media_data.get('isLive'))
        formats = self._extract_m3u8_formats(
            hls_url, video_id, 'mp4', m3u8_id='hls', live=is_live,
            headers={'Referer': url})

        hls_aes = None
        token = self._decode_b64(media_data.get('token'))
        xor_key = self._media_xor_key(media_data)
        api_base = traverse_obj(config, ('bases', 'api', {url_or_none})) or 'https://play.boomstream.com/api'
        if token and formats:
            media_playlist = self._download_webpage(
                formats[0]['url'], video_id, 'Downloading media playlist', fatal=False)
            media_ready = self._search_regex(
                r'#EXT-X-MEDIA-READY:([0-9a-fA-F]+)', media_playlist or '',
                'EXT-X-MEDIA-READY', default=None)
            if media_ready:
                hls_aes = self._extract_hls_aes(
                    media_ready, token, xor_key, api_base, video_id, url)

        return {
            'id': video_id,
            'formats': formats,
            'hls_aes': hls_aes,
            'is_live': is_live,
            'http_headers': {'Referer': url},
            'title': traverse_obj(media_data, ('title', {str})) or traverse_obj(
                config, ('entity', 'title', {str})),
            **traverse_obj(media_data, {
                'duration': ('duration', {float_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'thumbnail': ('posters', -1, 'link', {url_or_none}),
            }),
        }
