from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class XXXTikIE(InfoExtractor):
    IE_NAME = 'xxxtik'
    IE_DESC = 'XXXTik'
    _VALID_URL = (
        r'https?://(?:www\.)?xxxtik\.com/(?:feed|post)/'
        r'(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')
    _API_HOSTS = (
        'https://xxxtik-api-iw98m.ondigitalocean.app',
        'https://xxxtik-apix-s2l6l.ondigitalocean.app',
    )
    _CDN_SPACES = (
        'https://p5rn.com/',
        'https://xcdn.tv/',
    )
    _SPACE_SUFFIX = 'cdn/production/'
    _DEFAULT_SALT = '0312'
    _API_HEADERS = {
        'Accept': 'application/json',
        'Origin': 'https://xxxtik.com',
        'Referer': 'https://xxxtik.com/',
    }
    _MEDIA_HEADERS = {
        'Origin': 'https://xxxtik.com',
        'Referer': 'https://xxxtik.com/',
    }
    _TESTS = [{
        'url': 'https://xxxtik.com/feed/e185211e-730a-42ac-8c99-b7c821f017eb',
        'md5': '1ff75bf87af468088aa8a892b800edd3',
        'info_dict': {
            'id': 'e185211e-730a-42ac-8c99-b7c821f017eb',
            'ext': 'mp4',
            'title': 'That slide out is wild 🫣',
            'description': 'That slide out is wild 🫣',
            'thumbnail': r're:https://p5rn\.com/cdn/production/media/.+/thumbnail\.webp',
            'timestamp': 1784064401,
            'upload_date': '20260714',
            'uploader': 'blackworldorder',
            'uploader_id': 'c230a502-3c5a-49cc-a5c8-8d89e1680e3a',
            'view_count': int,
            'like_count': int,
            'width': 1922,
            'height': 1080,
            'tags': ['ass', 'bbc', 'interracial', 'doggystyle', 'monster-cock',
                     'big-ass', 'thick-cock', 'big-dick', 'white-girl', 'blackworldorder'],
            'age_limit': 18,
        },
    }, {
        # Original site-request URL
        'url': 'https://xxxtik.com/feed/11c127fc-e7f1-4fa2-a8c1-ed92255f81f1',
        'only_matching': True,
    }, {
        'url': 'https://www.xxxtik.com/feed/e2e57761-b5ba-46b2-a83a-49480f45c052',
        'only_matching': True,
    }, {
        'url': 'https://xxxtik.com/post/e185211e-730a-42ac-8c99-b7c821f017eb',
        'only_matching': True,
    }]

    def _download_post(self, video_id):
        last_error = None
        for host in self._API_HOSTS:
            try:
                post = self._download_json(
                    f'{host}/post/{video_id}', video_id,
                    headers=self._API_HEADERS)
            except ExtractorError as e:
                last_error = e
                continue
            if not isinstance(post, dict):
                continue
            if post.get('status') == 404:
                raise ExtractorError('Video not found', expected=True)
            if post.get('uuid') or post.get('uid'):
                return post
        if last_error:
            raise last_error
        raise ExtractorError('Unable to download post metadata', expected=True)

    def _extract_hls_formats(self, video_id, salt, uid):
        formats, subtitles = [], {}
        if not uid:
            return formats, subtitles
        for space in self._CDN_SPACES:
            m3u8_url = f'{space}{self._SPACE_SUFFIX}media/{salt}/{uid}/master.m3u8'
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                headers=self._MEDIA_HEADERS)
            if fmts:
                return fmts, subs
        return formats, subtitles

    def _extract_http_formats(self, post, salt, uid):
        formats = []
        path = traverse_obj(post, ('path', {str}))
        if path:
            for quality, preference in (('hd', 1), ('sd', -1)):
                formats.append({
                    'url': f'{self._API_HOSTS[0]}/util/media/{path}/{quality}.mp4',
                    'format_id': quality,
                    'ext': 'mp4',
                    'quality': preference,
                    'http_headers': self._MEDIA_HEADERS,
                })
            return formats

        video_url = traverse_obj(post, (
            ('redGifsVideoUrl', 'source'), {url_or_none}, any))
        if video_url:
            formats.append({
                'url': video_url,
                'format_id': 'http',
                'ext': 'mp4',
                'http_headers': self._MEDIA_HEADERS,
            })
            return formats

        video_name = traverse_obj(post, ('videoName', {str}))
        if video_name:
            base = (
                f'{self._CDN_SPACES[0]}{self._SPACE_SUFFIX}'
                f'media/{salt}/videos/{video_name}/{video_name}')
            formats.extend(({
                'url': f'{base}-0-480.mp4',
                'format_id': '480',
                'height': 480,
                'ext': 'mp4',
                'http_headers': self._MEDIA_HEADERS,
            }, {
                'url': f'{base}-0.mp4',
                'format_id': 'http',
                'ext': 'mp4',
                'quality': 1,
                'http_headers': self._MEDIA_HEADERS,
            }))
            return formats

        if uid:
            formats.append({
                'url': (
                    f'{self._CDN_SPACES[0]}{self._SPACE_SUFFIX}'
                    f'media/{salt}/{uid}/preview.mp4'),
                'format_id': 'preview',
                'ext': 'mp4',
                'quality': -10,
                'http_headers': self._MEDIA_HEADERS,
            })
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        post = self._download_post(video_id)

        salt = traverse_obj(post, ('salt', {str})) or self._DEFAULT_SALT
        uid = traverse_obj(post, ('uid', {str}))
        formats, subtitles = self._extract_hls_formats(video_id, salt, uid)
        if not formats:
            formats = self._extract_http_formats(post, salt, uid)

        if not formats:
            source = traverse_obj(post, ('source', {url_or_none}))
            if source and 'redgifs.com' in source:
                return self.url_result(source, ie='RedGifs')
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        for f in formats:
            f.setdefault('http_headers', {}).update(self._MEDIA_HEADERS)

        if uid:
            thumbnail = (
                f'{self._CDN_SPACES[0]}{self._SPACE_SUFFIX}'
                f'media/{salt}/{uid}/thumbnail.webp')
        else:
            thumbnail = traverse_obj(post, ('redGifsThumbnailUrl', {url_or_none}))

        return {
            'id': traverse_obj(post, ('uuid', {str})) or video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
            'age_limit': 18,
            'http_headers': self._MEDIA_HEADERS,
            'title': traverse_obj(post, (('description', 'path'), {str}, any)) or '',
            **traverse_obj(post, {
                'description': ('description', {str}),
                'timestamp': ('createdAt', {parse_iso8601}),
                'view_count': ('views', {int_or_none}),
                'like_count': ('likes', {int_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'uploader': ('author', 'name', {str}),
                'uploader_id': ('author', 'uuid', {str_or_none}),
                'tags': ('tags', ..., 'name', {str}),
            }),
        }
