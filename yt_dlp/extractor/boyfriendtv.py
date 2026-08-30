import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    merge_dicts,
    orderedSet,
    str_to_int,
    unescapeHTML,
    url_or_none,
)


class BoyfriendTVIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?boyfriendtv\.com/(?:[a-z]{2}/)?'
        r'(?:videos|embed)/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?')
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//(?:www\.)?boyfriendtv\.com/embed/\d+[^"\']*)\1']
    _TESTS = [{
        'url': 'https://www.boyfriendtv.com/videos/1464014/cum-inside-twice/',
        'md5': '9bf92863d98652fe5ef054eb8da01408',
        'info_dict': {
            'id': '1464014',
            'ext': 'mp4',
            'display_id': 'cum-inside-twice',
            'title': 'Cum Inside Twice',
            'description': 'Cum Inside Twice featuring Anal, Amateur, Big Cock, Homemade, Bareback, Gay Sex, Creampie, Hardcore, Boyfriend, Smells, Sniffing Feet',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg|png|webp)',
            'duration': 608,
            'timestamp': 1753811162,
            'upload_date': '20250729',
            'uploader': 'Richwhite2011',
            'uploader_id': '4187027',
            'view_count': int,
            'tags': ['anal', 'amateur', 'big cock', 'homemade', 'bareback', 'gay sex', 'creampie', 'hardcore', 'boyfriend', 'Smells', 'Sniffing feet'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.boyfriendtv.com/embed/1464014/2887/',
        'only_matching': True,
    }, {
        'url': 'https://www.boyfriendtv.com/de/videos/1464014/cum-inside-twice/',
        'only_matching': True,
    }, {
        'url': 'https://www.boyfriendtv.com/videos/1554105/fucking-the-piss-out-of-that-bottom/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id, impersonate=True)

        if not display_id or display_id.isdigit():
            display_id = self._search_regex(
                rf'/videos/{video_id}/([^/?#]+)',
                self._og_search_url(webpage, default='') or url,
                'display_id', default=video_id)

        sources = self._search_json(
            r'(?:var\s+)?playerConfig\s*=\s*\{\s*sources\s*:',
            webpage, 'player sources', video_id, default={})
        if not isinstance(sources, dict):
            sources = {}

        hls_url = url_or_none(sources.get('hlsAuto'))
        formats, subtitles = [], {}
        if hls_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls',
                headers={'Referer': 'https://www.boyfriendtv.com/'})
        else:
            formats = [{
                'url': src,
                'format_id': format_id,
            } for format_id, src in sources.items() if url_or_none(src)]
        if not formats:
            raise ExtractorError('No video sources found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)

        tags = orderedSet(
            unescapeHTML(t.strip())
            for t in re.findall(
                r'<a[^>]+class="[^"]*btn-tag[^"]*"[^>]+href="/tags/[^"]+"[^>]+title="([^"]+)"',
                webpage)
            if t.strip())

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title': (self._html_search_regex(r'<h1>([^<]+)</h1>', webpage, 'title', default=None)
                      or self._og_search_title(webpage, default=None)),
            'description': self._html_search_meta('description', webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': int_or_none(self._search_regex(
                r'videoDuration:\s*(\d+)', webpage, 'duration', default=None)),
            'view_count': str_to_int(self._html_search_regex(
                r'([\d,]+)\s*Views', webpage, 'view count', default=None)),
            'uploader': self._html_search_regex(
                r'<a[^>]+class="[^"]*user-uploader[^"]*"[^>]+title="([^"]+)"',
                webpage, 'uploader', default=None),
            'uploader_id': self._html_search_regex(
                r'<a[^>]+class="[^"]*user-uploader[^"]*"[^>]+href="/profiles/(\d+)/"',
                webpage, 'uploader id', default=None),
            'tags': tags or None,
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
        }, json_ld)
