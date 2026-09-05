from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_count,
    parse_duration,
    unified_strdate,
    urljoin,
)
from ..utils.traversal import traverse_obj


class NoodleMagazineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|adult\.)?noodlemagazine\.com/watch/(?P<id>[0-9-_]+)'
    _TESTS = [{
        'url': 'https://adult.noodlemagazine.com/watch/-67421364_456239604',
        'md5': '163113823da85d3099e77696764bf824',
        'info_dict': {
            'id': '-67421364_456239604',
            'ext': 'mp4',
            'title': 'Aria alexander manojob',
            'description': 'Aria alexander manojob',
            'duration': 903,
            'thumbnail': 'md5:59e3e77647f1a6dd31de3e1c094616c7',
            'upload_date': '20190218',
            'age_limit': 18,
            'view_count': int,
            'like_count': int,
            'tags': ['aria', 'alexander', 'manojob'],
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)
        title = self._og_search_title(webpage)
        duration = parse_duration(self._html_search_meta('video:duration', webpage, 'duration', default=None))
        description = self._og_search_property('description', webpage, default='').replace(' watch online hight quality video', '')
        tags = self._html_search_meta('video:tag', webpage, default='').split(', ')
        view_count = parse_count(self._html_search_meta('ya:ovs:views_total', webpage, default=None))
        like_count = parse_count(self._html_search_meta('ya:ovs:likes', webpage, default=None))
        upload_date = unified_strdate(self._html_search_meta('ya:ovs:upload_date', webpage, default=''))

        def build_url(url_or_path):
            return urljoin('https://adult.noodlemagazine.com', url_or_path)

        playlist_info = self._search_json(
            r'window\.playlist\s*=', webpage, video_id, 'playlist info')

        formats = []
        for source in traverse_obj(playlist_info, ('sources', lambda _, v: v['file'])):
            if source.get('type') == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    build_url(source['file']), video_id, 'mp4', fatal=False, m3u8_id='hls'))
            else:
                formats.append(traverse_obj(source, {
                    'url': ('file', {build_url}),
                    'format_id': 'label',
                    'height': ('label', {int_or_none}),
                    'ext': 'type',
                }))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': self._og_search_property('image', webpage, default=None) or playlist_info.get('image'),
            'duration': duration,
            'description': description,
            'tags': tags,
            'view_count': view_count,
            'like_count': like_count,
            'upload_date': upload_date,
            'age_limit': 18,
            'impersonate': True,
        }
