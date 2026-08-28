from .common import InfoExtractor
from ..utils import (
    float_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ReutersIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?reuters\.com/(?:video/watch/id|(?:[^?#]+[?&]videoId=))(?P<id>[A-Za-z0-9]+)'
    _TESTS = [{
        'url': 'https://www.reuters.com/video/watch/idRW810726082026RP1/',
        'md5': '70283d2fec4584963460260e5110dc4f',
        'info_dict': {
            'id': 'RW810726082026RP1',
            'ext': 'mp4',
            'title': "Meta's $18 billion settlement could lead to changes at TikTok, YouTube",
            'description': 'md5:f01e4f452299e7fc06649a4a9bcffc9f',
            'thumbnail': r're:https?://ajo\.prod\.reuters\.tv/api/v2/img/',
            'duration': 146.26,
            'timestamp': 1787785294,
            'upload_date': '20260826',
        },
    }, {
        'url': 'http://www.reuters.com/video/2016/05/20/san-francisco-police-chief-resigns?videoId=368575562',
        'skip': 'video gone',
        'md5': '8015113643a0b12838f160b0b81cc2ee',
        'info_dict': {
            'id': '368575562',
            'ext': 'mp4',
            'title': 'San Francisco police chief resigns',
        },
    }, {
        'url': 'https://www.reuters.com/video/watch/idRW810726082026RP1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)
        content = self._search_json(
            r'Fusion\.globalContent\s*=', webpage, 'content', video_id, default={})
        video = traverse_obj(content, (
            'result', 'videos',
            lambda _, v: v.get('id') == video_id or v.get('external_id') == video_id,
            any)) or traverse_obj(content, ('result', 'videos', 0, {dict})) or {}

        hls_url = traverse_obj(video, ('source', 'hls', {url_or_none}))
        if not hls_url:
            hls_url = url_or_none(self._og_search_property('video:url', webpage, default=None))
        if not hls_url:
            self.raise_no_formats('No HLS source found', expected=True, video_id=video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls')

        return {
            'id': video.get('id') or video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': video.get('title') or self._og_search_title(webpage),
            'description': video.get('description') or self._og_search_description(webpage, default=None),
            'thumbnail': (traverse_obj(video, ('thumbnail', 'url', {url_or_none}))
                          or self._og_search_thumbnail(webpage)),
            'duration': float_or_none(video.get('duration')),
            'timestamp': parse_iso8601(video.get('published_time')),
        }
