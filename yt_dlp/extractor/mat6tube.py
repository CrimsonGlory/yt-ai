from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_count,
    unified_strdate,
    urljoin,
)
from ..utils.traversal import traverse_obj


class Mat6TubeIE(InfoExtractor):
    IE_DESC = 'mat6tube.com'
    _VALID_URL = r'https?://(?:www\.)?mat6tube\.com/watch/(?P<id>[0-9-_]+)'
    _TESTS = [{
        'url': 'https://mat6tube.com/watch/-200614178_456239061',
        'md5': '5ee44a7fc8383d4dcc22f1849a9a0877',
        'info_dict': {
            'id': '-200614178_456239061',
            'ext': 'mp4',
            'title': 'Korean hot movie bosomy mom 2020 порно фильм с русским переводом anal sex porno janan asia retro vintage rus',
            'description': 'Watch hot porn movie Korean hot movie bosomy mom 2020 порно фильм с русским переводом anal sex porno janan asia retro vintage rus',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 4150,
            'view_count': int,
            'like_count': int,
            'upload_date': '20201209',
            'tags': 'count:26',
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.mat6tube.com/watch/-68355713_456239357',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        playlist = self._search_json(
            r'window\.playlist\s*=', webpage, 'playlist', video_id)

        formats = []
        for source in traverse_obj(playlist, ('sources', lambda _, v: v['file'])):
            media_url = urljoin('https://mat6tube.com', source['file'])
            if source.get('type') == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', fatal=False, m3u8_id='hls'))
            else:
                formats.append({
                    'url': media_url,
                    'format_id': source.get('label'),
                    'height': int_or_none(source.get('label')),
                    'ext': source.get('type') or 'mp4',
                })

        return {
            'id': video_id,
            'formats': formats,
            'title': self._og_search_title(webpage, default=None),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage) or playlist.get('image'),
            'duration': int_or_none(self._html_search_meta(
                'video:duration', webpage, default=None)),
            'view_count': parse_count(self._html_search_meta(
                'ya:ovs:views_total', webpage, default=None)),
            'like_count': parse_count(self._html_search_meta(
                'ya:ovs:likes', webpage, default=None)),
            'upload_date': unified_strdate(self._html_search_meta(
                'ya:ovs:upload_date', webpage, default=None)),
            'tags': [t.strip() for t in (self._html_search_meta(
                'video:tag', webpage, default='') or '').split(',') if t.strip()] or None,
            'age_limit': 18,
        }
