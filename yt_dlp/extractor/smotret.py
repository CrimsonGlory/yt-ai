import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    extract_attributes,
    get_domain,
    url_or_none,
    urljoin,
)


class SmotretTVIE(InfoExtractor):
    IE_NAME = 'smotret.tv'
    _VALID_URL = r'https?://(?:www\.)?smotret\.tv/(?P<id>[\w-]+)/?(?:$|[?#])'
    _TESTS = [
        {
            'url': 'https://smotret.tv/rbk',
            'info_dict': {
                'id': 'rbk',
                'ext': 'mp4',
                'title': r're:РБК — смотреть онлайн прямой эфир бесплатно в хорошем качестве',
                'description': 'md5:31d224a89fd4f6d33be974e881e65f41',
                'thumbnail': r're:https://smotret\.tv/images/.+',
                'live_status': 'is_live',
            },
        },
        {
            'url': 'https://smotret.tv/rossiya-1',
            'only_matching': True,
        },
        {
            'url': 'https://www.smotret.tv/zvezda',
            'only_matching': True,
        },
        {
            'url': 'https://smotret.tv/1-kanal',
            'only_matching': True,
        },
    ]

    def _iframe_url(self, webpage, page_url):
        for iframe in re.findall(r'<iframe\b[^>]*>', webpage):
            attrs = extract_attributes(iframe)
            src = attrs.get('src')
            if src and attrs.get('id') != 'chat':
                return urljoin(page_url, src)
        return None

    def _is_own_host(self, url):
        return get_domain(url) == 'smotret.tv'

    def _extract_hls(self, webpage, video_id):
        streams = self._search_json(
            r'var\s+streams\s*=', webpage, 'streams', video_id, contains_pattern=r'\[(?s:.+?)\]', default=[],
        )
        formats, subtitles = [], {}
        for i, stream in enumerate(streams if isinstance(streams, list) else []):
            stream_url = url_or_none(stream)
            if not stream_url or determine_ext(stream_url) != 'm3u8':
                continue
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id='hls' if i == 0 else f'hls-{i}', live=True, fatal=False,
            )
            if fmts:
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                break
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_url = self._iframe_url(webpage, url)
        if not player_url:
            self.raise_no_formats('No player found', video_id=video_id, expected=True)

        if not self._is_own_host(player_url):
            return self.url_result(player_url)

        player_page = self._download_webpage(player_url, video_id, 'Downloading player page', headers={'Referer': url})

        formats, subtitles = self._extract_hls(player_page, video_id)
        if formats:
            return {
                'id': video_id,
                'title': self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
                'description': self._og_search_description(webpage, default=None),
                'thumbnail': self._og_search_thumbnail(webpage, default=None),
                'formats': formats,
                'subtitles': subtitles,
                'is_live': True,
            }

        embed_url = self._iframe_url(player_page, player_url)
        if embed_url and not self._is_own_host(embed_url):
            return self.url_result(embed_url)

        self.raise_no_formats('No playable stream found', video_id=video_id, expected=True)
