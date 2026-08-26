from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_or_none,
    traverse_obj,
    try_get,
    unified_timestamp,
    urljoin,
)


class BeegIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beeg\.(?:com(?:/video)?)/-?(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://beeg.com/-0983946056129650',
        'md5': 'ee26908515c64175da770f104de94a9b',
        'info_dict': {
            'id': '983946056129650',
            'ext': 'mp4',
            'title': 'Sucked Cock and Fucked in a Private Plane',
            'duration': 927,
            'tags': list,
            'age_limit': 18,
            'upload_date': '20240301',
            'timestamp': 1709308546,
            'display_id': '5511897',
        },
    }, {
        'url': 'https://beeg.com/-0599050563103750?t=4-861',
        'md5': '56f5edf40c6237b7cc41b28a7d447686',
        'info_dict': {
            'id': '599050563103750',
            'ext': 'mp4',
            'title': 'Bad Relatives',
            'duration': 2060,
            'tags': list,
            'age_limit': 18,
            'description': 'md5:b4fc879a58ae6c604f8f259155b7e3b9',
            'timestamp': 1643623200,
            'display_id': '2569965',
            'upload_date': '20220131',
        },
    }, {
        # api/v6 v2
        'url': 'https://beeg.com/1941093077?t=911-1391',
        'only_matching': True,
    }, {
        # api/v6 v2 w/o t
        'url': 'https://beeg.com/1277207756',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        # Site prefixes file IDs with "-0" in URLs; the API rejects leading zeros.
        video_id = str(int(self._match_id(url)))

        webpage = self._download_webpage(url, video_id)

        video = self._download_json(
            f'https://store.externulls.com/facts/file/{video_id}',
            video_id, f'Downloading JSON for {video_id}')

        fc_facts = video.get('fc_facts') or []
        first_fact = {}
        for fact in fc_facts:
            if not first_fact or try_get(fact, lambda x: x['id'] < first_fact['id']):
                first_fact = fact

        resources = traverse_obj(video, ('file', 'hls_resources')) or first_fact.get('hls_resources') or {}

        formats = []
        for format_id, video_uri in resources.items():
            if not video_uri:
                continue
            height = int_or_none(self._search_regex(
                r'fl_cdn_(\d+)', format_id, 'height', default=None))
            current_formats = self._extract_m3u8_formats(
                urljoin('https://video.beeg.com/', video_uri), video_id, 'mp4',
                m3u8_id=str(height) if height else 'hls')
            if height:
                for f in current_formats:
                    f['height'] = height
            formats.extend(current_formats)

        return {
            'id': video_id,
            'display_id': str_or_none(first_fact.get('id')),
            'title': traverse_obj(
                video, ('file', 'stuff', 'sf_name'),
                ('file', 'data', lambda _, v: v['cd_column'] == 'sf_name', 'cd_value'),
                get_all=False),
            'description': traverse_obj(
                video, ('file', 'stuff', 'sf_story'),
                ('file', 'data', lambda _, v: v['cd_column'] == 'sf_story', 'cd_value'),
                get_all=False),
            'timestamp': unified_timestamp(first_fact.get('fc_created')),
            'duration': int_or_none(traverse_obj(video, ('file', 'fl_duration'))),
            'tags': traverse_obj(video, ('tags', ..., 'tg_name')),
            'formats': formats,
            'age_limit': self._rta_search(webpage),
        }
