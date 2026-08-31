import base64
import datetime
import hashlib
import json
import re
import time

from .common import InfoExtractor
from ..aes import aes_cbc_decrypt_bytes, unpad_pkcs7
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    join_nonempty,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class OlevodIE(InfoExtractor):
    IE_NAME = 'olevod'
    IE_DESC = 'Olevod (欧乐影院)'
    _VALID_URL = [
        r'https?://(?:www\.)?olevod\.com/index\.php/vod/play/id/(?P<id>\d+)/sid/\d+/nid/(?P<episode>\d+)(?:\.html)?',
        r'https?://(?:www\.)?olevod\.com/player/vod/\d+[-/](?P<id>\d+)[-/](?P<episode>\d+)(?:\.html)?',
        r'https?://(?:www\.)?olevod\.com/(?:index\.php/vod/detail/id/|details(?:-\d+-|/\d+/))(?P<id>\d+)(?:\.html)?',
    ]
    _API_BASE = 'https://api.olelive.com'
    _IMAGE_BASE = 'https://static.olelive.com/'
    _TESTS = [{
        'url': 'https://www.olevod.com/index.php/vod/play/id/54033/sid/1/nid/17.html',
        'md5': '596a7f8f684e641be0a6c5501f8299c4',
        'info_dict': {
            'id': '54033-17',
            'ext': 'mp4',
            'title': '紫川·光明三杰 第17集',
            'description': 'md5:089c0f5702f7a3eae2d974d960fb94f8',
            'thumbnail': 'https://static.olelive.com/upload/vod/20240227-1/46e3dc0cfc76abb597ed6fcf0c3281d9.jpg',
            'timestamp': 1709037048,
            'upload_date': '20240227',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'average_rating': float,
            'release_year': 2024,
            'categories': ['国产剧', '连续剧'],
            'cast': ['杨旭文', '刘宇宁', '张铭恩', '李墨之', '蔡卓音', '马少骅', '修庆', '张帆', '黄昊月', '郝汉', '刘星鹤', '张译文', '吴赫伦', '陈泇文', '李果'],
            'creators': ['张萌', '卫立洲'],
            'series': '紫川·光明三杰',
            'series_id': '54033',
            'episode': '第17集',
            'episode_number': 17,
            'age_limit': 0,
        },
    }, {
        'url': 'https://www.olevod.com/player/vod/2-54033-17.html',
        'only_matching': True,
    }, {
        'url': 'https://www.olevod.com/player/vod/2/54033/17',
        'only_matching': True,
    }, {
        'url': 'https://www.olevod.com/index.php/vod/detail/id/54033.html',
        'only_matching': True,
    }, {
        'url': 'https://www.olevod.com/details-2-54033.html',
        'only_matching': True,
    }, {
        'url': 'https://www.olevod.com/details/2/54033',
        'only_matching': True,
    }]

    @staticmethod
    def _sign_ts(ts):
        text = str(int(ts))
        rows = ['', '', '', '']
        for ch in text:
            bits = format(ord(ch), 'b')
            rows[0] += bits[2:3]
            rows[1] += bits[3:4]
            rows[2] += bits[4:5]
            rows[3] += bits[5:]
        injected = []
        for row in rows:
            hex_part = format(int(row, 2), 'x') if row else ''
            injected.append(hex_part.zfill(3) if len(hex_part) < 3 else hex_part)
        digest = hashlib.md5(text.encode()).hexdigest()
        return (
            digest[:3] + injected[0]
            + digest[6:11] + injected[1]
            + digest[14:19] + injected[2]
            + digest[22:27] + injected[3]
            + digest[30:])

    @staticmethod
    def _decrypt_payload(data):
        day = datetime.date.today().strftime('%Y-%m-%d')
        key_iv = hashlib.md5(day.encode()).hexdigest()[8:24].encode()
        try:
            return json.loads(unpad_pkcs7(aes_cbc_decrypt_bytes(
                base64.b64decode(data), key_iv, key_iv)).decode())
        except (ValueError, TypeError, json.JSONDecodeError):
            return None

    @staticmethod
    def _split_names(value):
        if not value or not isinstance(value, str):
            return None
        names = [part.strip() for part in re.split(r'[/、,，]', value) if part.strip()]
        return names or None

    def _call_api(self, path, video_id, **kwargs):
        data = self._download_json(
            f'{self._API_BASE}{path}', video_id,
            query={'_vv': self._sign_ts(time.time())},
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://www.olevod.com',
                'Referer': 'https://www.olevod.com/',
            }, **kwargs)
        if traverse_obj(data, 'code') not in (0, None):
            raise ExtractorError(
                traverse_obj(data, 'msg', {str}) or 'Olevod API error', expected=True)
        payload = data.get('data')
        if isinstance(payload, str):
            payload = self._decrypt_payload(payload)
        if not isinstance(payload, dict):
            raise ExtractorError('Unable to parse Olevod API response', expected=True)
        return payload

    def _extract_media(self, media_url, video_id):
        media_url = url_or_none(media_url)
        if not media_url:
            return [], {}
        ext = determine_ext(media_url, 'mp4')
        if ext == 'm3u8':
            return self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls',
                headers={'Referer': 'https://www.olevod.com/'})
        if ext == 'mpd':
            return self._extract_mpd_formats_and_subtitles(
                media_url, video_id, mpd_id='dash',
                headers={'Referer': 'https://www.olevod.com/'})
        return [{
            'url': media_url,
            'ext': ext,
            'http_headers': {'Referer': 'https://www.olevod.com/'},
        }], {}

    def _episode_info(self, vod, episode, display_id, n_eps):
        ep_title = traverse_obj(episode, 'title', {str})
        name = traverse_obj(vod, 'name', {str})
        formats, subtitles = self._extract_media(episode.get('url'), display_id)
        if not formats:
            vip_url = traverse_obj(episode, ('vip_urls', 0, 'url', {url_or_none}))
            if vip_url:
                self.raise_login_required('This quality requires a VIP membership')
            elif episode.get('vip') or vod.get('vip'):
                self.raise_login_required('This video requires a VIP membership')
            self.raise_no_formats('No video URL', expected=True, video_id=display_id)

        thumb = traverse_obj(vod, (('pic', 'picThumb', 'picSlide'), {str}, any))
        type_id1 = int_or_none(vod.get('typeId1'))
        return {
            'id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': join_nonempty(name, ep_title if n_eps > 1 else None, delim=' '),
            'age_limit': 18 if type_id1 == 5 else 0,
            'series': name if n_eps > 1 else None,
            'series_id': str_or_none(vod.get('id')) if n_eps > 1 else None,
            'episode': ep_title if n_eps > 1 else None,
            'episode_number': int_or_none(episode.get('index')) if n_eps > 1 else None,
            'thumbnail': urljoin(self._IMAGE_BASE, thumb) if thumb else None,
            **traverse_obj(vod, {
                'description': (('content', 'blurb'), {str}, filter, any),
                'timestamp': ('timeAdd', {int_or_none}),
                'view_count': ('hits', {int_or_none}),
                'like_count': ('up', {int_or_none}),
                'comment_count': ('commentTotal', {int_or_none}),
                'average_rating': ('score', {float_or_none}),
                'release_year': ('year', {int_or_none}),
                'categories': (('typeIdName', 'typeId1Name'), {str}, filter, all),
            }),
            'cast': self._split_names(vod.get('actor')),
            'creators': self._split_names(vod.get('director')),
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        vod_id = mobj.group('id')
        episode_number = int_or_none(mobj.groupdict().get('episode'))
        vod = self._call_api(f'/v1/pub/vod/detail/{vod_id}/true', vod_id)
        episodes = traverse_obj(vod, ('urls', ..., {dict})) or []
        if not episodes:
            if vod.get('vip') or vod.get('lock'):
                self.raise_login_required('This video requires a VIP membership')
            raise ExtractorError('No episodes found', expected=True)

        if episode_number is None:
            type_id1 = int_or_none(vod.get('typeId1')) or 1
            return self.playlist_result((
                self.url_result(
                    f'https://www.olevod.com/player/vod/{type_id1}-{vod_id}-{ep.get("index")}.html',
                    ie=self.ie_key(), video_id=f'{vod_id}-{ep.get("index")}',
                    video_title=join_nonempty(vod.get('name'), ep.get('title'), delim=' '))
                for ep in episodes if ep.get('index')
            ), vod_id, vod.get('name'), traverse_obj(vod, (('content', 'blurb'), {str}, filter, any)))

        episode = next((
            ep for ep in episodes if int_or_none(ep.get('index')) == episode_number), None)
        if not episode:
            raise ExtractorError(f'Episode {episode_number} not found', expected=True)
        return self._episode_info(vod, episode, f'{vod_id}-{episode_number}', len(episodes))
