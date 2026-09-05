import itertools

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_or_none,
    traverse_obj,
    unified_strdate,
)


class NateIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.nate\.com/clip/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'https://tv.nate.com/clip/1848976',
        'skip': 'extractor broken: Failed to parse JSON (caused by JSONDecodeError("Expecting value in \'\': line 1 c',
        'info_dict': {
            'id': '1848976',
            'ext': 'mp4',
            'title': '[결승 오프닝 타이틀] 2018 LCK 서머 스플릿 결승전 kt Rolster VS Griffin',
            'description': 'md5:e1b79a7dcf0d8d586443f11366f50e6f',
            'thumbnail': r're:^https?://.*\.jpg',
            'upload_date': '20180908',
            'age_limit': 15,
            'duration': 73,
            'uploader': '2018 LCK 서머 스플릿(롤챔스)',
            'channel': '2018 LCK 서머 스플릿(롤챔스)',
            'channel_id': '3606',
            'uploader_id': '3606',
            'tags': 'count:59',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://tv.nate.com/clip/4300566',
        'info_dict': {
            'id': '4300566',
            'ext': 'mp4',
            'title': '[심쿵엔딩] 이준호x이세영, 서로를 기억하며 끌어안는 두 사람!💕, MBC 211204 방송',
            'description': 'md5:be1653502d9c13ce344ddf7828e089fa',
            'thumbnail': r're:^https?://.*\.jpg',
            'upload_date': '20211204',
            'age_limit': 15,
            'duration': 201,
            'uploader': '옷소매 붉은 끝동',
            'channel': '옷소매 붉은 끝동',
            'channel_id': '27987',
            'uploader_id': '27987',
            'tags': 'count:20',
        },
        'params': {'skip_download': True},
    }]

    _QUALITY = {
        '36': 2160,
        '35': 1080,
        '34': 720,
        '33': 480,
        '32': 360,
        '31': 270,
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(f'https://tv.nate.com/api/v1/clip/{video_id}', video_id)
        formats = [{
            'format_id': f_url[-2:],
            'url': f_url,
            'height': self._QUALITY.get(f_url[-2:]),
            'quality': int_or_none(f_url[-2:]),
        } for f_url in video_data.get('smcUriList') or []]
        return {
            'id': video_id,
            'title': video_data.get('clipTitle'),
            'description': video_data.get('synopsis'),
            'thumbnail': video_data.get('contentImg'),
            'upload_date': unified_strdate(traverse_obj(video_data, 'broadDate', 'regDate')),
            'age_limit': video_data.get('targetAge'),
            'duration': video_data.get('playTime'),
            'formats': formats,
            'uploader': video_data.get('programTitle'),
            'channel': video_data.get('programTitle'),
            'channel_id': str_or_none(video_data.get('programSeq')),
            'uploader_id': str_or_none(video_data.get('programSeq')),
            'tags': video_data['hashTag'].split(',') if video_data.get('hashTag') else None,
        }


class NateProgramIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.nate\.com/program/clips/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'https://tv.nate.com/program/clips/27987',
        'playlist_mincount': 191,
        'info_dict': {
            'id': '27987',
        },
    }, {
        'url': 'https://tv.nate.com/program/clips/3606',
        'skip': 'extractor broken: Failed to parse JSON (caused by JSONDecodeError("Expecting value in \'\': line 1 c',
        'playlist_mincount': 15,
        'info_dict': {
            'id': '3606',
        },
    }]

    def _entries(self, playlist_id):
        for page_num in itertools.count(1):
            program_data = self._download_json(
                f'https://tv.nate.com/api/v1/program/{playlist_id}/clip/ranking?size=20&page={page_num}',
                playlist_id, note=f'Downloading page {page_num}')
            for clip in program_data.get('content') or []:
                clip_id = clip.get('clipSeq')
                if clip_id:
                    yield self.url_result(
                        f'https://tv.nate.com/clip/{clip_id}', NateIE, playlist_id)
            if program_data.get('last'):
                break

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        return self.playlist_result(self._entries(playlist_id), playlist_id=playlist_id)
