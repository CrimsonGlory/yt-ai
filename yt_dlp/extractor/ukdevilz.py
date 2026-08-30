from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class UKDevilzIE(InfoExtractor):
    IE_NAME = 'ukdevilz'
    IE_DESC = 'ukdevilz.com'
    _VALID_URL = r'https?://(?:www\.)?ukdevilz\.com/watch/(?P<id>-?\d+_\d+)'
    _TESTS = [{
        'url': 'https://ukdevilz.com/watch/-181972558_456239071',
        'md5': '4cb5fe595c900bf7d48bbaa3085f1538',
        'info_dict': {
            'id': '-181972558_456239071',
            'ext': 'mp4',
            'title': 'Остановил время и рассматривает пизды девушек (голые телки в супермаркете, девушки без трусов, пизда в фильме без цензуры)',
            'description': 'Video Остановил время и рассматривает пизды девушек (голые телки в супермаркете, девушки без трусов, пизда в фильме без цензуры) HQ Mp4',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 121,
            'view_count': int,
            'like_count': int,
            'upload_date': '20190526',
            'timestamp': 1558828800,
            'tags': ['голые', 'девушек', 'девушки', 'пизда', 'фильме', 'цензуры', 'телки'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.ukdevilz.com/watch/-181972558_456239071',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        playlist = self._search_json(r'window\.playlist\s*=', webpage, 'playlist', video_id)
        jw_info = self._parse_jwplayer_data(
            playlist, video_id, require_title=False, base_url=url)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)

        tags = traverse_obj(json_ld, ('tags', ..., {str.strip}, filter)) or traverse_obj(
            (self._html_search_meta('video:tag', webpage) or '').split(','),
            (..., {str.strip}, filter))

        return {
            **json_ld,
            **jw_info,
            'id': video_id,
            'title': (
                self._og_search_title(webpage, default=None)
                or json_ld.get('title')
                or self._html_extract_title(webpage)),
            'description': (
                self._og_search_description(webpage, default=None)
                or json_ld.get('description')),
            'thumbnail': (
                url_or_none(jw_info.get('thumbnail'))
                or self._og_search_thumbnail(webpage)),
            'duration': (
                int_or_none(self._html_search_meta('video:duration', webpage))
                or json_ld.get('duration')
                or jw_info.get('duration')),
            'view_count': (
                int_or_none(self._html_search_meta('ya:ovs:views_total', webpage))
                or json_ld.get('view_count')),
            'like_count': (
                int_or_none(self._html_search_meta('ya:ovs:likes', webpage))
                or json_ld.get('like_count')),
            'upload_date': unified_strdate(self._html_search_meta('ya:ovs:upload_date', webpage)),
            'timestamp': json_ld.get('timestamp'),
            'tags': tags or None,
            'age_limit': 18,
            'impersonate': True,
        }
