from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class AudiMediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:audi-mediacenter\.com|audi\.com)/(?P<lang>en|de)/(?:audimediatv(?:/video)?|videos/video)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.audi-mediacenter.com/en/videos/video/audi-q7-suv-trailer-on-location-8422',
        'md5': 'd39348d1948a2bbbb4132651033498da',
        'info_dict': {
            'id': '8422',
            'ext': 'mp4',
            'title': 'Audi Q7 SUV – Trailer (on location)',
            'description': 'On location trailer of the Audi Q7 SUV from France including driving scenes as well as interior and exterior shots.',
            'upload_date': '20260812',
            'duration': 42,
            'thumbnail': r're:https://uploads\.audi\.com/.+',
            'tags': ['Audi Q7 SUV', 'design', 'exterior', 'interior', 'driving scenes'],
        },
        'params': {'format': 'http-720'},
    }, {
        'url': 'https://www.audi.com/en/videos/video/audi-q7-suv-trailer-on-location-8422',
        'only_matching': True,
    }, {
        'url': 'https://www.audi-mediacenter.com/en/audimediatv/60-seconds-of-audi-sport-104-2015-wec-bahrain-rookie-test-1467',
        'skip': 'video gone',
        'md5': '79a8b71c46d49042609795ab59779b66',
        'info_dict': {
            'id': '1565',
            'ext': 'mp4',
            'title': '60 Seconds of Audi Sport 104/2015 - WEC Bahrain, Rookie Test',
            'description': 'md5:60e5d30a78ced725f7b8d34370762941',
            'upload_date': '20151124',
            'timestamp': 1448354940,
            'duration': 74022,
            'view_count': int,
        },
    }, {
        'url': 'https://www.audi-mediacenter.com/en/audimediatv/video/60-seconds-of-audi-sport-104-2015-wec-bahrain-rookie-test-2991',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, lang = self._match_valid_url(url).group('id', 'lang')
        video_id = self._search_regex(r'(\d+)$', display_id, 'video id')

        video_data = traverse_obj(
            self._download_json(
                f'https://www.audimedia.tv/api/videos/{video_id}', video_id,
                query={'locale': lang, 'id_type': 'amc'},
                headers={'Accept': 'application/json'}),
            ('data', {dict}, {require('video data')}))

        formats = []
        hls_url = traverse_obj(video_data, ('stream_url_hls', {url_or_none}))
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
        formats.extend(traverse_obj(video_data, ('downloads', lambda _, v: url_or_none(v['url']), {
            'url': 'url',
            'height': ('height', {int_or_none}),
            'format_id': ('height', {int_or_none}, {lambda h: f'http-{h}'}),
        })))

        return {
            'id': video_id,
            'formats': formats,
            **traverse_obj(video_data, {
                'id': ('id', {int}, {str_or_none}),
                'title': ('title', {str}),
                'description': ('description_text', {str}),
                'thumbnail': ('splash_image_url', {url_or_none}),
                'upload_date': ('public_date', {unified_strdate}),
                'duration': ('duration_millis', {int_or_none(scale=1000)}),
                'tags': ('tags', ..., {str}),
            }),
        }
