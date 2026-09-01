import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    js_to_json,
    merge_dicts,
    parse_duration,
    parse_iso8601,
    parse_resolution,
    traverse_obj,
    url_or_none,
    urljoin,
)


class XcadrIE(InfoExtractor):
    IE_DESC = 'xcadr.tv'
    _VALID_URL = r'https?://(?:www\.)?xcadr\.(?:tv|online)/videos/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://xcadr.online/videos/67585/seksi-angelina-strechina-uchastvuet-v-marafone/',
        'md5': 'ed05b30ef564b3c6502b939c5f7d1e5d',
        'info_dict': {
            'id': '67585',
            'ext': 'mp4',
            'title': 'Секси Ангелина Стречина участвует в марафоне',
            'description': 'Секси Ангелина Стречина участвует в марафоне – Осторожно люди (2025)',
            'thumbnail': r're:https?://xcadr\.online/contents/videos_screenshots/.+\.jpg',
            'duration': 35,
            'timestamp': 1767852000,
            'upload_date': '20260108',
            'age_limit': 18,
            'categories': ['Осторожно люди'],
            'tags': ['секси', 'бег', 'лосины'],
            'cast': ['Ангелина Стречина'],
        },
    }, {
        'url': 'https://xcadr.tv/videos/67585/seksi-angelina-strechina-uchastvuet-v-marafone/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        from .generic import GenericIE

        flashvars = self._search_json(
            r'var\s+\w+\s*=', webpage, 'player config', video_id,
            contains_pattern=r'\{[^{}]*video_url[^{}]*\}',
            transform_source=js_to_json, default={})
        if not flashvars.get('video_url'):
            flashvars = dict(re.findall(
                r'(video(?:_alt)?_url(?:\d*)?(?:_text)?|license_code|video_title|video_id|preview_url|video_categories|video_tags|video_models)\s*:\s*\'([^\']+)\'',
                webpage))

        formats = []
        for key in filter(re.compile(r'^video_(?:url|alt_url\d*)$').match, flashvars):
            video_url = url_or_none(urljoin(url, flashvars[key]))
            if not video_url or '/get_file/' not in video_url:
                continue
            format_id = flashvars.get(f'{key}_text', key)
            formats.append({
                'url': GenericIE._kvs_get_real_url(
                    video_url, flashvars.get('license_code')),
                'format_id': format_id,
                'ext': 'mp4',
                **(parse_resolution(format_id) or parse_resolution(video_url) or {}),
                'http_headers': {'Referer': url},
            })
        if not formats:
            raise ExtractorError('Unable to extract video URL')

        info = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        info.pop('url', None)
        info.pop('ext', None)

        def split_csv(value):
            if not value:
                return None
            return [item.strip() for item in value.split(',') if item.strip()] or None

        title = (
            traverse_obj(flashvars, ('video_title', {str}))
            or info.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage))

        return merge_dicts(info, {
            'id': traverse_obj(flashvars, ('video_id', {str})) or video_id,
            'title': title,
            'description': self._html_search_meta(
                'description', webpage) or self._og_search_description(webpage),
            'thumbnail': urljoin(url, traverse_obj(flashvars, ('preview_url', {url_or_none}))),
            'duration': parse_duration(self._html_search_meta('duration', webpage)),
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage)),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })


class XcadrPlaylistIE(InfoExtractor):
    IE_NAME = 'xcadr:playlist'
    IE_DESC = 'xcadr.tv celeb/movie pages'
    _VALID_URL = r'https?://(?:www\.)?xcadr\.(?:tv|online)/(?:celebs|movies)/(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'https://xcadr.tv/celebs/golaya-angelina-strechina/',
        'info_dict': {
            'id': 'golaya-angelina-strechina',
            'title': 'Голая Ангелина Стречина',
            'age_limit': 18,
        },
        'playlist_mincount': 10,
        'params': {
            'skip_download': True,
            'extract_flat': 'in_playlist',
        },
    }, {
        'url': 'https://xcadr.online/movies/ostorojno-lyudi-eroticheskie-sceny/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        title = (
            self._html_search_regex(r'<h1>([^<]+)</h1>', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage))
        return self.playlist_from_matches(
            re.findall(r'href="((?:https?:)?(?://[^/]+)?/videos/\d+/[^"]+)"', webpage),
            playlist_id, title, getter=lambda path: urljoin(url, path), ie=XcadrIE,
            age_limit=18)
