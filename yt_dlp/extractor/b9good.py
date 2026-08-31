import base64
import hashlib
import random
import string
import time

from .common import InfoExtractor
from ..aes import aes_gcm_decrypt_and_verify_bytes
from ..utils import (
    ExtractorError,
    parse_iso8601,
    urljoin,
)
from ..utils.networking import std_headers
from ..utils.traversal import traverse_obj


class B9GoodIE(InfoExtractor):
    IE_NAME = 'b9good'
    IE_DESC = 'B9GOOD'
    _VALID_URL = r'https?://(?:www\.)?b9good\.org/anime/(?P<id>\d+)(?:\.html)?'
    _EMBED_HOST = 'https://korxime.guru'
    _KORXIME_SECRET = '732d2574bd7fdf58b5916136'
    _KORXIME_AES_KEY = bytes.fromhex('442e06c44c8aff31e87604463d83ae4481e722e7d99c47f52b91b8d58fd94e6c')
    _TESTS = [
        {
            'url': 'https://b9good.org/anime/126946.html',
            'md5': 'e52c1afd4a2f2a58aa483ffa0f1167e7',
            'info_dict': {
                'id': '126946',
                'ext': 'mp4',
                'title': 'アズールレーン びそくぜんしんっ！にっ！！　第9話 B9 Dailymotion',
                'description': 'アズールレーン びそくぜんしんっ！にっ！！　第9話 B9 Dailymotion',
                'timestamp': 1788139659,
                'upload_date': '20260831',
                'categories': ['アズールレーン びそくぜんしんっ！にっ！！'],
            },
        },
        {
            'url': 'https://b9good.org/anime/15852.html',
            'only_matching': True,
        },
    ]

    def _user_agent(self):
        return traverse_obj(self.get_param('http_headers'), 'User-Agent', {str}) or std_headers['User-Agent']

    def _korxime_hash(self, playlist_id, user_agent):
        timestamp = str(int(time.time() * 1000))
        salt = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        payload = (
            self._KORXIME_SECRET
            + timestamp[::-1]
            + salt[::-1]
            + user_agent[::-1]
            + self._KORXIME_SECRET
            + playlist_id[::-1]
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return base64.b64encode(f'{timestamp}:{digest}:{salt}'.encode()).decode()

    @staticmethod
    def _b64decode(value):
        return base64.b64decode(value + '=' * ((4 - len(value) % 4) % 4))

    def _decrypt_playlist(self, blob):
        try:
            iv_b64, ciphertext_b64, tag_b64 = blob.split(':')
        except ValueError:
            raise ExtractorError('Unexpected korxime playlist blob', expected=True)
        try:
            return aes_gcm_decrypt_and_verify_bytes(
                self._b64decode(ciphertext_b64),
                self._KORXIME_AES_KEY,
                self._b64decode(tag_b64),
                self._b64decode(iv_b64),
            ).decode()
        except (ValueError, TypeError) as e:
            raise ExtractorError(f'Unable to decrypt korxime playlist: {e}')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        embed_url = self._search_regex(
            r'<iframe[^>]+\bsrc="(https?://korxime\.guru/embed/[^"]+)"', webpage, 'embed url',
        )
        user_agent = self._user_agent()
        embed_headers = {
            'Referer': url,
            'User-Agent': user_agent,
        }
        embed_page = self._download_webpage(embed_url, video_id, 'Downloading embed page', headers=embed_headers)
        playlist_id = self._search_regex(r'getPlaylist\(\s*[`\'"]([0-9a-f]{32})[`\'"]', embed_page, 'playlist id')
        player_headers = {
            'Referer': embed_url,
            'Origin': self._EMBED_HOST,
            'User-Agent': user_agent,
        }
        sources = self._download_json(
            f'{self._EMBED_HOST}/ajax/getSources',
            video_id,
            'Downloading korxime sources',
            query={'id': playlist_id},
            headers={
                **player_headers,
                'Accept': 'application/json',
                'x-hash': self._korxime_hash(playlist_id, user_agent),
            },
            expected_status=(400, 403),
        )
        if not isinstance(sources, dict):
            raise ExtractorError('Invalid korxime sources response', expected=True)
        if sources.get('error'):
            raise ExtractorError(f"korxime said: {sources['error']}", expected=True)
        playlist = sources.get('playlist')
        if not playlist:
            self.raise_no_formats('No korxime playlist', expected=True, video_id=video_id)
        m3u8_url = urljoin(self._EMBED_HOST, self._decrypt_playlist(playlist))
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', headers=player_headers,
        )
        for track in traverse_obj(sources, ('tracks', ..., {dict})) or []:
            src = track.get('file') or track.get('src')
            if not src:
                continue
            track_url = urljoin(self._EMBED_HOST, src)
            lang = track.get('label') or track.get('srclang') or 'und'
            subtitles.setdefault(lang, []).append(
                {
                    'url': track_url,
                    'name': track.get('label'),
                },
            )
        category = self._html_search_meta('article:section', webpage, default=None)
        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'timestamp': parse_iso8601(self._html_search_meta('article:published_time', webpage, default=None)),
            'categories': [category] if category else None,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': player_headers,
        }
