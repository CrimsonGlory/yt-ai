from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class NhacCuaTuiIE(InfoExtractor):
    IE_NAME = 'nhaccuatui'
    IE_DESC = 'nhaccuatui.com'
    _VALID_URL = (
        r'https?://(?:www\.)?nhaccuatui\.com/'
        r'(?P<kind>bai-hat|song|video)/(?:[^/?#.]+\.)?(?P<id>[^/?#.]+)'
        r'(?:\.html)?/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://www.nhaccuatui.com/bai-hat/this-love-davichi.R07lnYhmtOXV.html',
        'md5': '2ba0bc5ac66272b8b2340d34ff229c61',
        'info_dict': {
            'id': 'R07lnYhmtOXV',
            'ext': 'mp3',
            'title': 'This Love',
            'track': 'This Love',
            'artists': ['DAVICHI'],
            'duration': 226,
            'timestamp': 1554468004,
            'upload_date': '20190405',
            'thumbnail': r're:https://image-cdn\.nct\.vn/.+',
            'uploader': 'thanhexo',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'genres': ['Nhạc Hàn'],
            'description': r're:(?s)Siganeul doedollimyeon.+',
        },
    }, {
        'url': 'https://www.nhaccuatui.com/song/R07lnYhmtOXV',
        'only_matching': True,
    }, {
        'url': 'https://www.nhaccuatui.com/video/IXTbg1bBelQKh',
        'only_matching': True,
    }, {
        'url': 'https://www.nhaccuatui.com/video/co-hen-voi-thanh-xuan-monstar.IXTbg1bBelQKh.html',
        'only_matching': True,
    }]

    def _extract_formats(self, info):
        formats = []
        for stream in traverse_obj(info, ('streamURL', ..., {dict})):
            url = url_or_none(stream.get('stream')) or url_or_none(stream.get('download'))
            if not url:
                continue
            type_id = traverse_obj(stream, ('type', {str}))
            type_ui = (traverse_obj(stream, ('typeUI', {str})) or '').lower()
            ext = determine_ext(url)
            fmt = {
                'url': url,
                'format_id': traverse_obj(stream, (('type', 'typeUI'), {str}, any)),
                'filesize': traverse_obj(info, (
                    'qualityDownload', lambda _, v: v.get('key') == type_id,
                    'fileSize', {int_or_none}, any)),
            }
            if ext in ('mp3', 'm4a', 'flac', 'aac') or 'kbps' in type_ui or (
                    type_id or '').lower() in ('128', '320', 'lossless'):
                fmt.update({
                    'ext': ext or 'mp3',
                    'vcodec': 'none',
                    'abr': int_or_none(type_id),
                    'acodec': 'flac' if (type_id or ext or '').lower() in ('lossless', 'flac') else 'mp3',
                })
            else:
                fmt.update({
                    'ext': ext or 'mp4',
                    'height': int_or_none(type_id),
                })
            formats.append(fmt)
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        nuxt = self._search_nuxt_json(webpage, video_id)
        info = traverse_obj(nuxt, (
            'data', (f'dataDetail:{video_id}', f'videoDetail:{video_id}'), {dict}, any)) or {}

        formats = self._extract_formats(info)
        if not formats:
            if 'not available in your country' in webpage.lower():
                self.raise_geo_restricted(countries=['VN'])
            self.raise_no_formats(
                'No public stream was found', expected=True, video_id=video_id)

        artists = traverse_obj(info, (('artist', 'artists'), ..., 'name', {str}, filter))
        if not artists:
            artists = traverse_obj(info, ('artistName', {str}, filter, all))

        return {
            'id': video_id,
            'formats': formats,
            'artists': list(dict.fromkeys(artists or [])),
            'description': (
                traverse_obj(info, ('LyricDetail', 'content', {str}, filter))
                or traverse_obj(nuxt, ('data', f'lyrics:{video_id}', 'content', {str}, filter))
                or self._og_search_description(webpage, default=None)),
            **traverse_obj(info, {
                'title': ('name', {str}),
                'track': ('name', {str}),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('dateRelease', {int_or_none(scale=1000)}),
                'view_count': ('viewed', {int_or_none}),
                'like_count': ('totalLiked', {int_or_none}),
                'comment_count': ('commentCnt', {int_or_none}),
                'thumbnail': (('image', 'bgImage', 'artistImage'), {url_or_none}, any),
                'uploader': (((('provider', 'name'), 'uploader'), {str}, filter, any)),
                'genres': (('genreName', ('genre', 'name')), {str}, filter, all),
            }),
        }
