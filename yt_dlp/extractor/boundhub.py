import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    js_to_json,
    merge_dicts,
    parse_count,
    parse_duration,
    parse_resolution,
    traverse_obj,
    url_or_none,
    urljoin,
)


class BoundHubIE(InfoExtractor):
    IE_DESC = 'boundhub.com'
    _VALID_URL = r'https?://(?:www\.)?boundhub\.com/(?:videos|embed)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.boundhub.com/videos/1030103/frogtied-after-stripping-tease/',
        'md5': 'b6c7e5e26a1b091037f2bfe231233a94',
        'info_dict': {
            'id': '1030103',
            'ext': 'mp4',
            'title': 'Frogtied after stripping tease',
            'description': 'Blonde girl spits out her gag only to be gagged again with socks. She strips down and is frogtied nicely leaving her exposed and beautiful.',
            'thumbnail': r're:https?://cnt\.bondageobserver\.com/contents/videos_screenshots/.+\.jpg',
            'duration': 456,
            'view_count': int,
            'uploader': 'Tieherupandgagher',
            'age_limit': 18,
            'categories': ['Classic Bondage', 'Gags'],
            'tags': ['frogtied', 'exposed', 'socks', 'rope bondage', 'cleave gag'],
        },
    }, {
        'url': 'https://www.boundhub.com/videos/169268/sahara-rain-extreme/',
        'only_matching': True,
    }, {
        'url': 'https://www.boundhub.com/embed/169268',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

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
            video_url = flashvars[key]
            if not video_url or '/get_file/' not in video_url:
                continue
            format_id = flashvars.get(f'{key}_text', key)
            formats.append({
                'url': urljoin(url, GenericIE._kvs_get_real_url(
                    video_url, flashvars.get('license_code'))),
                'format_id': format_id,
                'ext': 'mp4',
                **(parse_resolution(format_id) or parse_resolution(video_url) or {}),
                'http_headers': {'Referer': url},
                'impersonate': True,
            })

        if not formats:
            if re.search(r'This video is a private video', webpage):
                self.raise_login_required('This video is private')
            if re.search(r'videos? no longer available', webpage, re.IGNORECASE):
                raise ExtractorError('Video is no longer available', expected=True)
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

        view_count_str = self._html_search_regex(
            r'Views:\s*<em[^>]*>([^<]+)</em>', webpage, 'view count', default=None)
        if view_count_str:
            view_count_str = view_count_str.replace(' ', '')

        return merge_dicts(info, {
            'id': traverse_obj(flashvars, ('video_id', {str})) or video_id,
            'title': title,
            'description': self._html_search_meta(
                'description', webpage) or self._og_search_description(webpage),
            'thumbnail': urljoin(url, traverse_obj(flashvars, ('preview_url', {url_or_none}))),
            'duration': parse_duration(self._html_search_regex(
                r'Duration:\s*<em[^>]*>([^<]+)</em>', webpage, 'duration', default=None)),
            'view_count': parse_count(view_count_str),
            'uploader': self._html_search_regex(
                r'<div class="username">\s*<a[^>]+>\s*([^<]+?)\s*</a>',
                webpage, 'uploader', default=None),
            'formats': formats,
            'age_limit': 18,
            'categories': split_csv(traverse_obj(flashvars, ('video_categories', {str}))),
            'tags': split_csv(traverse_obj(flashvars, ('video_tags', {str}))),
            'cast': split_csv(traverse_obj(flashvars, ('video_models', {str}))),
        })


class BoundHubPlaylistIE(InfoExtractor):
    IE_NAME = 'boundhub:playlist'
    IE_DESC = 'boundhub.com playlists'
    _VALID_URL = r'https?://(?:www\.)?boundhub\.com/playlists/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.boundhub.com/playlists/15864/wrist-cage/',
        'info_dict': {
            'id': '15864',
            'title': 'Wrist Cage',
            'age_limit': 18,
        },
        'playlist_mincount': 10,
        'params': {
            'skip_download': True,
            'extract_flat': 'in_playlist',
        },
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id, impersonate=True)
        title = (
            self._html_search_regex(
                r'<title>\s*BoundHub\s*-\s*(.+?)\s*</title>',
                webpage, 'title', default=None)
            or self._html_extract_title(webpage))
        return self.playlist_from_matches(
            re.findall(r'data-playlist-item="([^"]+)"', webpage),
            playlist_id, title, ie=BoundHubIE, age_limit=18)
