from .common import InfoExtractor
from ..utils import (
    clean_html,
    format_field,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class AparatIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?aparat\.com/(?:v/|video/video/embed/videohash/)(?P<id>[a-zA-Z0-9]+)'
    _EMBED_REGEX = [r'<iframe .*?src="(?P<url>http://www\.aparat\.com/video/[^"]+)"']

    _TESTS = [{
        'url': 'http://www.aparat.com/v/wP8On',
        'md5': '131aca2e14fe7c4dcb3c4877ba300c89',
        'info_dict': {
            'id': 'wP8On',
            'ext': 'mp4',
            'title': 'تیم گلکسی 11 - زومیت',
            'description': 'www.zoomit.ir',
            'duration': 231,
            'timestamp': 1387394859,
            'upload_date': '20131218',
            'view_count': int,
            'uploader': 'وبسایت زومیت',
            'uploader_id': 'thezoomit',
            'channel': 'وبسایت زومیت',
            'channel_id': 'thezoomit',
            'channel_url': 'https://www.aparat.com/thezoomit',
            'comment_count': int,
            'like_count': int,
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'categories': ['فناوری و رایانه'],
            'tags': ['تیم', 'گلکسی', 'زومیت'],
        },
    }, {
        # multiple formats
        'url': 'https://www.aparat.com/v/8dflw/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._download_json(
            f'https://www.aparat.com/api/fa/v1/video/video/show/videohash/{video_id}',
            video_id, query={'pr': 1, 'mf': 1})
        attrs = traverse_obj(video, ('data', 'attributes', {dict}))
        if not attrs:
            self.raise_no_formats('No video data found', expected=True, video_id=video_id)

        formats = []
        for item in traverse_obj(attrs, ('file_link_all', lambda _, v: isinstance(v, dict) and v.get('urls'))):
            profile = item.get('profile') or ''
            height = int_or_none(self._search_regex(
                r'(\d+)[pP]', profile, 'height', default=None))
            for idx, file_url in enumerate(traverse_obj(item, ('urls', ..., {url_or_none}))):
                formats.append({
                    'url': file_url,
                    'format_id': join_nonempty('http', profile, idx or None),
                    'height': height,
                })
        if not formats:
            file_url = url_or_none(attrs.get('file_link'))
            if file_url:
                formats.append({'url': file_url})

        hls_url = traverse_obj(attrs, (('hls_link', ('hls', 'link')), {url_or_none}, any))
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False, quality=-10))

        channel = traverse_obj(video, (
            'included', lambda _, v: v.get('type') == 'channel', 'attributes', {dict}, any)) or {}
        username = traverse_obj(channel, ('username', {str})) or traverse_obj(
            attrs, ('owner_username', {str}))

        return {
            'id': video_id,
            'formats': formats,
            **traverse_obj(attrs, {
                'title': ('title', {str}),
                'description': ('description', {clean_html}),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('mdate', {parse_iso8601}),
                'thumbnail': ('big_poster', {url_or_none}),
                'view_count': ('visit_cnt_non_formatted', {int_or_none}),
                'like_count': ('like_cnt_non_formatted', {int_or_none}),
                'comment_count': ('comment_cnt_non_formatted', {int_or_none}),
                'tags': ('tags', ..., {str}, {str.strip}, filter),
                'categories': ('category', 'name', {str}, filter, all),
            }),
            **traverse_obj(channel, {
                'uploader': (('displayName', 'name'), {str}, any),
                'channel': (('displayName', 'name'), {str}, any),
            }),
            'uploader_id': username,
            'channel_id': username,
            'channel_url': format_field(username, None, 'https://www.aparat.com/%s'),
        }
