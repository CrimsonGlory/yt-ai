import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    js_to_json,
    merge_dicts,
    parse_duration,
    remove_end,
    str_to_int,
    urljoin,
)


class AzNudeIE(InfoExtractor):
    IE_DESC = 'AZNude'
    _VALID_URL = (
        r'https?://(?:www\.)?aznude\.com/'
        r'(?:azncdn/(?:[^/?#]+/)*|embed/)(?P<id>[^/?#]+)\.html'
    )
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?aznude\.com/embed/[^"\']+)']
    _TESTS = [
        {
            'url': 'https://www.aznude.com/azncdn/389b628f2c6244d2b06964af6f9ec7e5/389b628f2c6244d2b06964af6f9ec7e5-hd.html',
            'md5': 'd538b2fcac66ae5057e243994aebd106',
            'info_dict': {
                'id': '389b628f2c6244d2b06964af6f9ec7e5-hd',
                'ext': 'mp4',
                'title': 'Katie Stuart Breasts, Bikini Scene in Wild Things 2',
                'description': "Watch Katie Stuart's Breasts, Bikini scene for free on AZNude (1 minute and 36 seconds).",
                'thumbnail': r're:https?://cdn2\.aznude\.com/.+\.(?:jpg|jpeg|png|webp)',
                'duration': 96,
                'view_count': int,
                'age_limit': 18,
            },
            'params': {'format': 'HD'},
        },
        {
            'url': 'https://www.aznude.com/embed/389b628f2c6244d2b06964af6f9ec7e5-hd.html',
            'only_matching': True,
        },
        {
            'url': 'https://www.aznude.com/azncdn/meganward/ticktock/ticktock2000-ward-hd-01_hd.html',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        jwplayer_data = self._search_json(
            r'playerInstance\.setup\s*\(', webpage, 'JWPlayer data', video_id, transform_source=js_to_json, default=None,
        )
        info = self._parse_jwplayer_data(jwplayer_data, video_id, require_title=False) if jwplayer_data else {}
        if not isinstance(info, dict) or not info.get('formats'):
            raise ExtractorError('No video source found', expected=True)

        description = self._og_search_description(webpage, default=None) or self._html_search_meta(
            'description', webpage, default=None,
        )
        duration = parse_duration(
            re.sub(r'\s+and\s+', ' ', self._search_regex(r'\(([^()]+)\)', description or '', 'duration', default='')),
        )

        return merge_dicts(
            {
                'id': video_id,
                'title': (
                    self._og_search_title(webpage, default=None)
                    or remove_end(self._html_extract_title(webpage), ' - AZNude')
                ),
                'description': description,
                'thumbnail': self._og_search_thumbnail(webpage, default=None),
                'duration': duration,
                'view_count': str_to_int(self._search_regex(r'([\d,]+)\s*Views', webpage, 'view count', default=None)),
                'age_limit': 18,
            },
            info,
        )


class AzNudePlaylistIE(InfoExtractor):
    IE_NAME = 'aznude:playlist'
    IE_DESC = 'AZNude celeb/movie pages'
    _VALID_URL = (
        r'https?://(?:www\.)?aznude\.com/view/(?:celeb|movie)/'
        r'[^/?#]+/(?P<id>[^/?#]+)\.html'
    )
    _TESTS = [
        {
            'url': 'https://www.aznude.com/view/celeb/k/katiestuart-7010.html',
            'info_dict': {
                'id': 'katiestuart-7010',
                'title': 'KATIE STUART Nude',
            },
            'playlist_mincount': 1,
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.aznude.com/view/movie/t/titans.html',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        title = remove_end(
            self._og_search_title(webpage, default=None) or self._html_extract_title(webpage), ' - AZNude',
        )
        return self.playlist_from_matches(
            re.findall(r'href=["\'](/azncdn/[^"\']+\.html)', webpage),
            playlist_id,
            title,
            getter=lambda path: urljoin(url, path),
            ie=AzNudeIE,
        )
