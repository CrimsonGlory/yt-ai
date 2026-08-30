from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
    orderedSet,
    parse_resolution,
    traverse_obj,
    url_or_none,
)


class XPicVidIE(InfoExtractor):
    IE_NAME = 'xpicvid'
    IE_DESC = 'xpicvid.com'
    _VALID_URL = r'https?://(?:www\.)?(?:xpicvid|niacg|suacg)\.com/showinfo-\d+-(?P<id>\d+)-\d+'
    _TESTS = [{
        'url': 'https://www.xpicvid.com/showinfo-21-8061-0.html',
        'md5': 'd40fa1f24c91112a9ede7267a3f7a4bb',
        'info_dict': {
            'id': '8061',
            'ext': 'mp4',
            'title': '[Maplestar] Fern x Stark【Full Animation!!】',
            'description': 'md5:54e64f7306bd6f9da7300439de507abb',
            'thumbnail': 'https://gamezy.xunge.cyou/titlep/2025/0106/qqb4vhbqpqu57.jpg',
            'view_count': int,
            'age_limit': 18,
            'tags': ['1080p', '內射', '巨乳', '無碼', '純愛', '素股', '費倫', '陰毛', '顏射', '葬送的芙莉蓮'],
        },
    }, {
        'url': 'https://www.niacg.com/showinfo-21-8061-0.html',
        'only_matching': True,
    }, {
        'url': 'https://www.suacg.com/showinfo-19-16660-0.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(
            url, video_id, impersonate=True)
        headers = {'Referer': urlh.url}

        video = self._search_json(
            r'\bvideo\s*:\s*', webpage, 'DPlayer video', video_id,
            transform_source=js_to_json)
        qualities = traverse_obj(video, ('quality', ..., {
            'url': ('url', {url_or_none}),
            'format_id': ('name', {str}),
        })) or []
        if not any(q.get('url') for q in qualities):
            media_url = url_or_none(video.get('url'))
            if media_url:
                qualities = [{'url': media_url, 'format_id': None}]

        formats = []
        for quality in qualities:
            media_url = quality.get('url')
            if not media_url:
                continue
            format_id = quality.get('format_id')
            if determine_ext(media_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', m3u8_id=format_id or 'hls',
                    fatal=False, headers=headers))
                continue
            formats.append({
                'url': media_url,
                'format_id': format_id,
                'ext': determine_ext(media_url, 'mp4'),
                **parse_resolution(format_id),
                'http_headers': headers,
            })

        tags = orderedSet(
            tag.strip() for tag in (
                self._html_search_meta('keywords', webpage) or '').split(',')
            if tag.strip())

        return {
            'id': video_id,
            'title': self._html_search_regex(
                r'<h3[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._html_extract_title(webpage),
            'description': self._html_search_meta('description', webpage, default=None),
            'thumbnail': url_or_none(video.get('pic')),
            'view_count': int_or_none(self._search_regex(
                r'查看:\s*(\d+)', webpage, 'view count', default=None)),
            'age_limit': 18,
            'tags': tags or None,
            'formats': formats,
            'http_headers': headers,
        }
