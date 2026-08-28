from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    traverse_obj,
    update_url_query,
    url_or_none,
)


class StarTVIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?startv\.com\.tr/
        (?:
            (?:dizi|program)/(?:[^/?#&]+)/(?:bolumler|fragmanlar|ekstralar)|
            video/arsiv/(?:dizi|program)/(?:[^/?#&]+)
        )/
        (?P<id>[^/?#&]+)
    '''
    IE_NAME = 'startv'
    _API_BASE = 'https://dygvideo.dygdigital.com/api/video_info'
    _PUBLISHER_ID = '1'
    _SECRET_KEY = 'NtvApiSecret2014*'
    _TESTS = [
        {
            'url': 'https://www.startv.com.tr/dizi/cocuk/bolumler/3-bolum',
            'md5': 'f7aa453bd5659ae8daf838306b87084f',
            'info_dict': {
                'id': '904972',
                'display_id': '3-bolum',
                'ext': 'mp4',
                'title': '3. Bölüm',
                'description': 'md5:c2632f29394758569cad4f697d6e48a3',
                'thumbnail': r're:^https?://.*\.jpg(?:\?.*?)?$',
                'timestamp': 1569281400,
                'upload_date': '20190923',
                'duration': 7757,
            },
        },
        {
            'url': 'https://www.startv.com.tr/video/arsiv/dizi/avlu/44-bolum',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/dizi/cocuk/fragmanlar/5-bolum-fragmani',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/dizi/cocuk/ekstralar/5-bolumun-nefes-kesen-final-sahnesi',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/program/burcu-ile-haftasonu/bolumler/1-bolum',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/program/burcu-ile-haftasonu/fragmanlar/2-fragman',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/video/arsiv/program/buyukrisk/14-bolumde-hangi-unlu-ne-sordu-',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/video/arsiv/program/buyukrisk/buyuk-risk-334-bolum',
            'only_matching': True,
        },
        {
            'url': 'https://www.startv.com.tr/video/arsiv/program/dada/dada-58-bolum',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        info_url = self._search_regex(
            r'(["\'])videoUrl\1\s*:\s*\1(?P<url>(?:(?!\1).)+)\1\s*',
            webpage, 'video info url', group='url', default=None)
        if not info_url:
            reference_id = self._search_regex(
                r'\\?"referenceId\\?"\s*:\s*\\?"([^"\\]+)\\?"',
                webpage, 'reference id', default=None)
            if not reference_id:
                tags = self._html_search_meta('dyg:tags', webpage, 'reference id', fatal=True)
                reference_id = tags.rsplit(',', 1)[-1].strip()
            info_url = update_url_query(self._API_BASE, {
                'akamai': 'true',
                'PublisherId': self._PUBLISHER_ID,
                'ReferenceId': f'StarTv_{reference_id}',
                'SecretKey': self._SECRET_KEY,
            })

        info = traverse_obj(self._download_json(info_url, display_id), 'data', expected_type=dict)
        if not info:
            raise ExtractorError('Failed to extract API data')

        video_id = str(info.get('id'))
        title = info.get('title') or self._og_search_title(webpage)
        description = clean_html(info.get('description')) or self._og_search_description(webpage, default=None)
        thumbnail = self._proto_relative_url(
            self._og_search_thumbnail(webpage), scheme='http:')

        formats = self._extract_m3u8_formats(
            traverse_obj(info, ('flavors', 'hls', {url_or_none})),
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': int_or_none(info.get('release_date')),
            'duration': int_or_none(info.get('duration')),
            'formats': formats,
        }
