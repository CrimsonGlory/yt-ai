import re

from .common import InfoExtractor
from ..utils import (
    format_field,
    int_or_none,
    orderedSet,
    remove_start,
    str_to_int,
    unified_strdate,
    url_or_none,
    urljoin,
)


class KamTapeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kamtape\.com/(?:(?:watch(?:\.php)?|watch_video)\?(?:[^#]*&)?v=|v/)(?P<id>[0-9A-Za-z_-]{11})'
    _TESTS = [{
        'url': 'https://www.kamtape.com/watch?v=0FWizEG-65g',
        'md5': '3ad8222644e2544e174f2e4e44065550',
        'info_dict': {
            'id': '0FWizEG-65g',
            'ext': 'mp4',
            'title': 'skyward fire (bartender2000 dnb bootleg remix)',
            'description': 'md5:dfee8396a7512923ea339e9f629ddf68',
            'thumbnail': r're:https?://.+\.jpg',
            'uploader': 'Bartender2000',
            'uploader_id': 'Bartender2000',
            'uploader_url': 'https://www.kamtape.com/user/Bartender2000',
            'upload_date': '20260724',
            'duration': 385,
            'view_count': int,
            'comment_count': int,
            'categories': ['Music'],
            'tags': ['ut99', 'unreal', 'tournament', 'dnb'],
        },
    }, {
        'url': 'https://www.kamtape.com/v/0FWizEG-65g',
        'only_matching': True,
    }, {
        'url': 'https://www.kamtape.com/watch.php?v=0FWizEG-65g',
        'only_matching': True,
    }, {
        'url': 'https://www.kamtape.com/watch_video?v=0FWizEG-65g',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            f'https://www.kamtape.com/watch?v={video_id}', video_id)

        formats = []
        for format_id, pattern, height in (
            ('sd', r'(?<![a-zA-Z])src\s*:\s*(["\'])(?P<url>(?:https?:)?/get_video[^"\']*)\1', 360),
            ('hd', r'hdsrc\s*:\s*(["\'])(?P<url>(?:https?:)?/[^"\']+)\1', 720),
        ):
            video_url = urljoin(
                'https://www.kamtape.com/',
                self._search_regex(pattern, webpage, f'{format_id} url', default=None, group='url'))
            if url_or_none(video_url):
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'height': height,
                    'ext': 'mp4',
                })
        if not formats:
            formats.append({
                'url': self._og_search_video_url(webpage, default=None) or (
                    f'https://www.kamtape.com/get_video?video_id={video_id}&webm=1'),
                'format_id': 'sd',
                'height': 360,
                'ext': 'mp4',
            })

        title = (
            self._html_search_regex(
                r'<h1[^>]*id=["\']title1["\'][^>]*>([^<]+)', webpage, 'title', default=None)
            or remove_start(self._html_extract_title(webpage, default=''), 'KamTape - ')
            or None)

        uploader_id, uploader = self._html_search_regex(
            r'<a[^>]+href=["\']/profile\?user=(?P<id>[^"\'&]+)["\'][^>]*>(?P<name>[^<]+)',
            webpage, 'uploader', default=(None, None), group=('id', 'name'))

        category = self._html_search_regex(
            r'Category(?:&nbsp;|\s)*</span>\s*<a[^>]*>([^<]+)',
            webpage, 'category', default=None)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, default=None),
            'thumbnail': url_or_none(self._search_regex(
                r'\bimg\s*:\s*(["\'])(?P<url>(?:https?:)?/[^"\']+)\1',
                webpage, 'thumbnail', default=None, group='url')) or self._og_search_thumbnail(webpage),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': format_field(uploader_id, None, 'https://www.kamtape.com/user/%s'),
            'upload_date': unified_strdate(
                self._html_search_meta('og:video:release_date', webpage, default=None)
                or self._html_search_regex(
                    r'Added:</span>(?:\s|&nbsp;)*<b[^>]*>([^<]+)', webpage, 'upload date', default=None)),
            'duration': int_or_none(self._search_regex(
                r'(?<![a-zA-Z])duration\s*:\s*(\d+)', webpage, 'duration', default=None),
            ) or int_or_none(self._og_search_property('video:duration', webpage, default=None)),
            'view_count': str_to_int(self._search_regex(
                r'Views:\s*<span[^>]*>([\d,]+)', webpage, 'view count', default=None)),
            'comment_count': str_to_int(self._search_regex(
                r'Comments:\s*<span[^>]*>([\d,]+)', webpage, 'comment count', default=None)),
            'categories': [category] if category else None,
            'tags': orderedSet(re.findall(
                r'<meta[^>]+property=["\']og:video:tag["\'][^>]+content=["\']([^"\']+)',
                webpage)) or None,
            'formats': formats,
        }
