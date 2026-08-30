import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
    orderedSet,
    parse_iso8601,
    parse_resolution,
    url_or_none,
    urljoin,
)


class AstalaVRIE(InfoExtractor):
    IE_DESC = 'AstalaVR'
    _VALID_URL = r'https?://(?:www\.)?astalavr\.com/(?:[a-z]{2}/)?videos/(?P<id>[0-9A-Za-z]{5})(?:/|$|\?)'
    _TESTS = [{
        'url': 'https://astalavr.com/videos/7gYMp/Kenzie-Reeves-Fucks-Big-Dick-In-Full-VR-Scene',
        'md5': '465e3b68e90d1c15e2458aafec3be333',
        'info_dict': {
            'id': '7gYMp',
            'ext': 'mp4',
            'title': 'Kenzie Reeves Fucks Big Dick In Full VR Scene',
            'description': 'md5:e56e8a75d726e5470474608c018e3a0f',
            'thumbnail': r're:https?://cdn2\.astalavr\.com/7gYMp/poster\.jpg',
            'duration': 2603,
            'timestamp': 1598554718,
            'upload_date': '20200827',
            'uploader': 'y2k',
            'uploader_id': '82N4Q',
            'uploader_url': 'https://astalavr.com/users/82N4Q/y2k',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'cast': ['Kenzie Reeves'],
            'categories': ['Blonde VR'],
            'tags': ['Blonde'],
            'age_limit': 18,
        },
        'params': {
            # Full-quality cdn3 MP4s are WAF-blocked from some IPs; preview is public.
            'format': 'preview',
        },
    }, {
        'url': 'https://astalavr.com/videos/px4mm/pool-sex-with-your-sister-s-friend',
        'only_matching': True,
    }, {
        'url': 'https://astalavr.com/ja/videos/7gYMp/Kenzie-Reeves-Fucks-Big-Dick-In-Full-VR-Scene',
        'only_matching': True,
    }, {
        'url': 'https://astalavr.com/videos/7gYMp',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)
        headers = {'Referer': 'https://astalavr.com/'}

        formats = []
        player_tag = self._search_regex(
            r'<dl8-video\b[^>]*>', webpage, 'player', default='', group=0)
        fps = int_or_none(extract_attributes(player_tag).get('fps')) if player_tag else None
        for source in re.findall(r'<source[^>]+>', webpage):
            attrs = extract_attributes(source)
            video_url = url_or_none(attrs.get('src'))
            if not video_url:
                continue
            quality = attrs.get('quality') or ''
            height = (
                parse_resolution(video_url).get('height')
                or parse_resolution(quality).get('height'))
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': quality.lower() or (str(height) if height else None),
                'height': height,
                'fps': fps,
                'http_headers': headers,
                'impersonate': True,
            })

        preview_url = f'https://cdn2.astalavr.com/{video_id}/preview.mp4'
        if not any(f.get('url') == preview_url for f in formats):
            formats.append({
                'url': preview_url,
                'ext': 'mp4',
                'format_id': 'preview',
                'quality': -10,
                'fps': fps,
                'http_headers': headers,
                'impersonate': True,
            })

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)

        uploader_id, uploader = self._search_regex(
            r'href="/users/([^/]+)/([^"/]+)"', webpage, 'uploader',
            default=(None, None), group=(1, 2))
        actor = self._html_search_meta('video:actor', webpage, default=None)
        tag = self._html_search_meta('video:tag', webpage, default=None)

        return {
            **json_ld,
            'id': video_id,
            'title': (
                self._og_search_title(webpage, default=None)
                or self._html_extract_title(webpage, default=None)
                or video_id),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': (
                url_or_none(self._og_search_thumbnail(webpage, default=None))
                or url_or_none(json_ld.get('thumbnail'))
                or f'https://cdn2.astalavr.com/{video_id}/poster.jpg'),
            'duration': (
                int_or_none(self._html_search_meta('video:duration', webpage, default=None))
                or json_ld.get('duration')),
            'timestamp': parse_iso8601(
                self._html_search_meta('video:release_date', webpage, default=None),
            ) or json_ld.get('timestamp'),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': (
                urljoin(url, f'/users/{uploader_id}/{uploader}')
                if uploader_id and uploader else None),
            'like_count': int_or_none(self._search_regex(
                r'class="js-likes-count"[^>]*>([^<]+)', webpage, 'like count', default=None),
            ) or json_ld.get('like_count'),
            'dislike_count': int_or_none(self._search_regex(
                r'class="js-dislikes-count"[^>]*>([^<]+)', webpage, 'dislike count', default=None)),
            'cast': [actor] if actor else None,
            'categories': orderedSet(re.findall(
                r'<a[^>]+href="/categories/[^"]+"[^>]*>([^<]+)', webpage)) or None,
            'tags': [tag] if tag else None,
            'age_limit': 18,
            'formats': formats,
            'http_headers': headers,
            'impersonate': True,
        }
