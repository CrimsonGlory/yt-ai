import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    orderedSet,
    remove_end,
    str_to_int,
    unified_strdate,
    urljoin,
)


class HobuneIE(InfoExtractor):
    IE_NAME = 'hobune'
    IE_DESC = 'hobune.stream'
    _VALID_URL = r'https?://(?:www\.)?hobune\.stream/(?P<pre>(?:tpa-h/)?)videos/(?P<id>[^/?#.]+)(?:\.html)?'
    _TESTS = [{
        'url': 'https://hobune.stream/videos/z6kWijmyAhk',
        'md5': 'c6cff928fc3aa3767ee7f0b08a1f2c28',
        'info_dict': {
            'id': 'z6kWijmyAhk',
            'ext': 'mp4',
            'title': 'In the Grotto',
            'description': 'md5:fc2aa9e886756973d84588131e4d7d09',
            'thumbnail': r're:https?://cdn\.hobune\.stream/.+',
            'upload_date': '20131017',
            'view_count': 3773,
            'uploader': 'Tr4nquilhooves',
            'uploader_id': 'UCKg6OZ57LY1x7AHB-6ahzXA',
            'uploader_url': 'https://hobune.stream/channels/UCKg6OZ57LY1x7AHB-6ahzXA',
            'channel': 'Tr4nquilhooves',
            'channel_id': 'UCKg6OZ57LY1x7AHB-6ahzXA',
            'channel_url': 'https://hobune.stream/channels/UCKg6OZ57LY1x7AHB-6ahzXA',
        },
    }, {
        'url': 'https://hobune.stream/videos/z6kWijmyAhk.html',
        'only_matching': True,
    }, {
        'url': 'https://hobune.stream/tpa-h/videos/rSciSQV94O4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, prefix = self._match_valid_url(url).group('id', 'pre')
        webpage = self._download_webpage(url, video_id)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        if not entries or not entries[0].get('formats'):
            raise ExtractorError('No video source found', expected=True)
        info = entries[0]

        title = (
            self._html_search_regex(
                r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
            or remove_end(self._html_extract_title(webpage, default=''), ' - hobune')
            or None)

        description = self._html_search_regex(
            r'<h2[^>]*>\s*Description\b.*?</h2>\s*<p>(.*?)</p>',
            webpage, 'description', default=None, flags=re.DOTALL) or None

        channel_id = self._search_regex(
            r'class="uploader">Video by <a[^>]+href="[^"]*?/channels/([^"/?#]+)',
            webpage, 'channel id', default=None)
        uploader = self._html_search_regex(
            r'class="uploader">Video by <a[^>]*>([^<]+)</a>',
            webpage, 'uploader', default=None) or self._html_search_meta(
            'author', webpage, default=None)
        channel_url = urljoin(url, f'/{prefix}channels/{channel_id}') if channel_id else None

        info.update({
            'id': video_id,
            'title': title,
            'description': description,
            'view_count': str_to_int(self._search_regex(
                r'class="views">([\d,]+)\s*views', webpage, 'view count', default=None)),
            'upload_date': unified_strdate(self._html_search_regex(
                r'class="date">([^<]+)', webpage, 'upload date', default=None)),
            'uploader': uploader,
            'uploader_id': channel_id,
            'uploader_url': channel_url,
            'channel': uploader,
            'channel_id': channel_id,
            'channel_url': channel_url,
        })
        return info


class HobuneChannelIE(InfoExtractor):
    IE_NAME = 'hobune:channel'
    _VALID_URL = r'https?://(?:www\.)?hobune\.stream/(?P<pre>(?:tpa-h/)?)channels/(?P<id>[^/?#.]+)(?:\.html)?'
    _TESTS = [{
        'url': 'https://hobune.stream/channels/UC1yAk-KCgL-tBBzH2zBC08A',
        'info_dict': {
            'id': 'UC1yAk-KCgL-tBBzH2zBC08A',
            'title': 'MrBeast Extra',
            'description': "MrBeast Extra's channel archive",
        },
        'playlist_count': 1,
    }, {
        'url': 'https://hobune.stream/channels/UCkVo7eqym1ZX2A9-GabEXrw',
        'info_dict': {
            'id': 'UCkVo7eqym1ZX2A9-GabEXrw',
            'title': 'taia777',
            'description': "taia777's channel archive",
        },
        'playlist_mincount': 31,
    }, {
        'url': 'https://hobune.stream/channels/UCKg6OZ57LY1x7AHB-6ahzXA',
        'only_matching': True,
    }, {
        'url': 'https://hobune.stream/tpa-h/channels/UCepDizXP-O_-7VwSwfB-Nfg',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel_id, prefix = self._match_valid_url(url).group('id', 'pre')
        webpage = self._download_webpage(url, channel_id)
        title = self._html_search_regex(
            r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
        video_ids = orderedSet(re.findall(
            r'href="(?:/[^"]+)?/videos/([^"?#]+)"', webpage))
        return self.playlist_result(
            (self.url_result(urljoin(url, f'/{prefix}videos/{vid}'), HobuneIE, vid)
             for vid in video_ids),
            channel_id, title, self._html_search_meta(
                'description', webpage, default=None))
