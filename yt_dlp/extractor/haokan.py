from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    qualities,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class HaokanIE(InfoExtractor):
    IE_NAME = 'haokan'
    IE_DESC = '百度好看视频'
    _VALID_URL = r'https?://haokan\.(?:baidu|hao123)\.com/(?:v)?/?(?:\?(?:[^#]*&)?)?vid=(?P<id>\d+)'
    _LANDING_URL = 'https://mbd.baidu.com/newspage/data/videolanding'
    _TESTS = [{
        'url': 'https://haokan.baidu.com/v?vid=3321366250719491589',
        'md5': '688716ba7f7202d3de70cb1b6b1afbce',
        'info_dict': {
            'id': '3321366250719491589',
            'ext': 'mp4',
            'title': '科普｜二十四节气起源知多少',
            'thumbnail': r're:https?://.+',
            'duration': 316,
            'timestamp': 1679570270,
            'upload_date': '20230323',
            'uploader': '问理斋',
            'uploader_id': '1761031591146039',
            'view_count': int,
            'like_count': int,
        },
    }, {
        'url': 'https://haokan.baidu.com/v?vid=11369462149913467613&collection_id=10316640470276722301',
        'only_matching': True,
    }, {
        'url': 'https://haokan.hao123.com/v?vid=3321366250719491589',
        'only_matching': True,
    }, {
        'url': 'https://haokan.baidu.com/v?pd=pcshare&vid=3321366250719491589',
        'only_matching': True,
    }]

    def _extract_formats(self, meta, video_id):
        formats, urls = [], set()
        quality = qualities(('sd', 'hd', 'sc', '1080p'))

        def add_url(media_url, format_id=None, item=None):
            media_url = url_or_none(media_url)
            if not media_url or media_url in urls:
                return
            urls.add(media_url)
            ext = determine_ext(media_url, 'mp4')
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', m3u8_id=format_id or 'hls', fatal=False))
                return
            height, width = None, None
            hw = traverse_obj(item, ('vodVideoHW', {str}))
            if hw and '$$' in hw:
                h, w = hw.split('$$', 1)
                height, width = int_or_none(h), int_or_none(w)
            formats.append({
                'url': media_url,
                'format_id': format_id,
                'ext': ext,
                'quality': quality(format_id),
                'width': width,
                'height': height,
                'filesize': int_or_none(float_or_none(
                    traverse_obj(item, 'videoSize'), invscale=1024 * 1024)),
            })

        for item in traverse_obj(meta, ('clarityUrl', ..., {dict})) or []:
            add_url(item.get('url'), str_or_none(item.get('key')), item)
        add_url(meta.get('playurl'), 'playurl')
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            self._LANDING_URL, video_id, 'Downloading video landing page',
            query={'nid': f'sv_{video_id}'},
            headers={'Referer': 'https://haokan.baidu.com/'})
        data = self._search_json(
            r'window\.jsonData\s*=', webpage, 'video data', video_id)
        meta = traverse_obj(data, ('curVideoMeta', {dict})) or {}
        formats = self._extract_formats(meta, video_id)
        if not formats:
            self.raise_no_formats('No video formats', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
            'title': traverse_obj(meta, ('title', {str})),
            'thumbnail': traverse_obj(meta, ('poster', {url_or_none})),
            'duration': int_or_none(meta.get('duration')),
            'timestamp': int_or_none(meta.get('publish_time')),
            'uploader': traverse_obj(data, ('author', 'name', {str})),
            'uploader_id': traverse_obj(data, ('author', 'third_id', {str_or_none})),
            'view_count': int_or_none(traverse_obj(data, 'playCount')),
            'like_count': int_or_none(traverse_obj(data, ('like', 'count'))),
        }
