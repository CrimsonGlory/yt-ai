import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    unified_strdate,
    url_or_none,
)


class PornLibIE(InfoExtractor):
    IE_DESC = 'pornlib.com'
    _VALID_URL = r'https?://(?:www\.)?pornlib\.com/(?:video|embed)/(?:[\w-]+-)?(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.pornlib.com/video/buxom-teen-sends-her-lovely-lips-bringing-a-cock-to-orgasm-277094',
        'md5': '9cb53a9ed9f71afbc320d4c9e2e26804',
        'info_dict': {
            'id': '277094',
            'ext': 'mp4',
            'title': 'Buxom teen sends her lovely lips bringing a cock to orgasm',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 549,
            'age_limit': 18,
            'uploader': 'Anowelf2000',
            'upload_date': '20210206',
            'like_count': int,
            'dislike_count': int,
            'tags': ['Amateur', 'Blowjob', 'Brunette', 'Cumshot', 'HD', 'POV', 'Teen (18+)'],
        },
    }, {
        'url': 'https://www.pornlib.com/embed/277094',
        'only_matching': True,
    }, {
        'url': 'https://pornlib.com/video/buxom-teen-sends-her-lovely-lips-bringing-a-cock-to-orgasm-277094',
        'only_matching': True,
    }]
    _QUALITIES = {
        'lq': 320,
        'hq': 720,
        '4k': 2160,
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, fatal=False) or ''

        video_data = self._download_json(
            'https://www.pornlib.com/player_config_json/', video_id, query={
                'vid': video_id,
                'aid': 0,
                'domain_id': 0,
                'embed': 0,
                'check_speed': 0,
            }, headers={
                # Without Accept: application/json the endpoint returns [].
                'Accept': 'application/json, text/javascript, */*; q=0.01',
            }) or {}

        formats = []
        files = video_data.get('files')
        if isinstance(files, dict):
            for format_id, video_url in files.items():
                if url_or_none(video_url):
                    formats.append({
                        'format_id': format_id,
                        'url': video_url,
                        'ext': 'mp4',
                        'height': self._QUALITIES.get(format_id),
                    })

        title = video_data.get('title') or self._html_search_regex(
            r'<h1[^>]+class="title"[^>]*>([^<]+)', webpage, 'title', default=None)
        duration = int_or_none(video_data.get('duration')) or parse_duration(
            video_data.get('duration_format'))
        thumbnail = url_or_none(video_data.get('poster')) or self._html_search_regex(
            r'<video[^>]+poster="([^"]+)"', webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': self._rta_search(webpage) or 18,
            'uploader': self._html_search_regex(
                r'Submitted by\s*<a[^>]+>([^<]+)', webpage, 'uploader', default=None),
            'upload_date': unified_strdate(self._search_regex(
                r'Published on\s+(\d{2}\.\d{2}\.\d{4})',
                webpage, 'upload date', default=None)),
            'like_count': int_or_none(self._search_regex(
                r'class="rate_likes"[^>]*>([\d,.]+)', webpage, 'like count', default=None)),
            'dislike_count': int_or_none(self._search_regex(
                r'class="rate_dislikes"[^>]*>([\d,.]+)', webpage, 'dislike count', default=None)),
            'tags': re.findall(r'<a title="([^"]+)"[^>]*class="tag"', webpage) or None,
        }
