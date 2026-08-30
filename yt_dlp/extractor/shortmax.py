from .common import InfoExtractor
from ..aes import aes_cbc_decrypt_bytes, unpad_pkcs7
from ..downloader import PROTOCOL_MAP
from ..downloader.hls import HlsFD
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ShortMaxHlsFD(HlsFD):
    """Native HLS downloader that unwraps ShortMax's custom TS segment encryption."""

    FD_NAME = 'shortmaxhls'

    _HEADER_SIZE = 0x400
    _IV = b'shortmax00000000'

    @classmethod
    def decrypt_segment(cls, data):
        if not data or not data.startswith(b'shortmax') or len(data) < cls._HEADER_SIZE + 16:
            return data
        try:
            key_offset = int(data[0x10:0x14].decode('ascii'))
            encrypted_length = int(data[0x14:0x18].decode('ascii'))
        except (UnicodeDecodeError, ValueError):
            return data
        key = data[key_offset : key_offset + 16]
        enc_end = cls._HEADER_SIZE + encrypted_length
        if len(key) != 16 or len(data) < enc_end:
            return data
        decrypted = unpad_pkcs7(aes_cbc_decrypt_bytes(data[cls._HEADER_SIZE : enc_end], key, cls._IV))
        return decrypted + data[enc_end:]

    def decrypter(self, info_dict):
        parent_decrypt = super().decrypter(info_dict)

        def decrypt_fragment(fragment, frag_content):
            if frag_content is None:
                return
            frag_content = parent_decrypt(fragment, frag_content)
            return self.decrypt_segment(frag_content)

        return decrypt_fragment


PROTOCOL_MAP['shortmaxhls'] = ShortMaxHlsFD


class ShortMaxIE(InfoExtractor):
    IE_NAME = 'shortmax'
    IE_DESC = 'ShortMax'
    _VALID_URL = (
        r'https?://(?:www\.)?shorttv\.live/(?:[a-z]{2}(?:-[A-Za-z]+)?/)?'
        r'episode/(?P<slug>[^/?#]+)-(?P<id>(?P<series_id>\d+)-(?P<episode>\d+))/?(?:[?#]|$)'
    )
    _TESTS = [
        {
            'url': 'https://www.shorttv.live/episode/dont-mess-with-the-beggar-17376-1',
            'md5': 'ca97fabfdd8785f3b654ad4c9fff61ad',
            'info_dict': {
                'id': '17376-1',
                'ext': 'mp4',
                'title': "Don't Mess with  the Beggar - Episode 1",
                'display_id': 'dont-mess-with-the-beggar',
                'description': 'md5:c5443c4ee516f5759050b2ced64766dd',
                'thumbnail': r're:https://akamai-static\.shorttv\.live/images/cover/.+\.jpg',
                'view_count': int,
                'episode_number': 1,
                'episode': 'Episode 1',
                'series': "Don't Mess with  the Beggar",
                'series_id': '17376',
                'categories': ['Urban Stories', 'Underdog Story'],
                'tags': ['Modern', 'Unwanted Son-in-Law'],
            },
        },
        {
            'url': 'https://www.shorttv.live/es/episode/ese-mendigo-no-es-com%C3%BAn-17373-1',
            'only_matching': True,
        },
        {
            'url': 'https://www.shorttv.live/zh-Hant/episode/%E9%80%99%E5%80%8B%E4%B9%9E%E4%B8%80%E4%B8%8D%E5%A5%BD%E6%83%B9-17377-1',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        slug, video_id, series_id, episode = self._match_valid_url(url).group('slug', 'id', 'series_id', 'episode')
        episode_num = int(episode)
        webpage = self._download_webpage(url, video_id)
        nuxt = self._search_nuxt_json(webpage, video_id)
        play = traverse_obj(
            nuxt,
            (
                'data',
                (
                    f'shortPlay-{series_id}',
                    lambda _, v: str_or_none(traverse_obj(v, ('data', 'shortPlayId'))) == series_id,
                ),
                'data',
                {dict},
                any,
            ),
        )
        if not play:
            raise ExtractorError('Unable to extract ShortMax play data', video_id=video_id)

        episode_info = traverse_obj(
            play, ('episodeList', lambda _, v: int_or_none(v.get('episodeNum')) == episode_num, any),
        )
        if not episode_info:
            raise ExtractorError('Unable to extract episode metadata', video_id=video_id)

        video_urls = episode_info.get('encryptedVideoUrl')
        if isinstance(video_urls, str) and video_urls:
            video_urls = self._parse_json(video_urls, video_id, fatal=False)
        if not isinstance(video_urls, dict):
            video_urls = {}

        formats = []
        for quality, m3u8_url in video_urls.items():
            if not url_or_none(m3u8_url):
                continue
            height = int_or_none(str(quality).replace('video_', ''))
            formats.append(
                {
                    'url': m3u8_url,
                    'ext': 'mp4',
                    'protocol': 'shortmaxhls',
                    'format_id': f'hls-{height}' if height else quality,
                    'height': height,
                },
            )
        if not formats:
            self.raise_login_required('This episode is locked', metadata_available=True, method='cookies')

        title = traverse_obj(play, 'lanShortPlayName', 'shortPlayName', 'rawName', expected_type=str)
        if title:
            title = f'{title} - Episode {episode_num}'

        return {
            'id': video_id,
            'display_id': slug,
            'title': title or self._og_search_title(webpage, default=None),
            'description': traverse_obj(play, 'lanShortPlayDescription', 'summary', expected_type=str),
            'thumbnail': (
                traverse_obj(episode_info, 'frameExtractionCover', 'coverId', expected_type=url_or_none)
                or traverse_obj(play, 'coverId', 'horizontalCoverId', expected_type=url_or_none)
                or self._og_search_thumbnail(webpage, default=None)
            ),
            'view_count': traverse_obj(play, 'playNum', expected_type=int_or_none),
            'episode_number': episode_num,
            'series': traverse_obj(play, 'lanShortPlayName', 'shortPlayName', 'rawName', expected_type=str),
            'series_id': series_id,
            'categories': traverse_obj(play, ('classList', ..., 'displayName', {str})),
            'tags': traverse_obj(play, ('labelList', ..., 'displayName', {str})),
            'formats': formats,
            'http_headers': {'Referer': 'https://www.shorttv.live/'},
        }
