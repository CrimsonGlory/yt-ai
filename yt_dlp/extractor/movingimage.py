import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    traverse_obj,
    unescapeHTML,
    url_or_none,
)


class MovingImageIE(InfoExtractor):
    _VALID_URL = r'https?://movingimage\.nls\.uk/film/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://movingimage.nls.uk/film/3561',
        'md5': '87b63ba3b7568d27522395f305a4aca5',
        'info_dict': {
            'id': '3561',
            'ext': 'mp4',
            'title': 'SHETLAND WOOL',
            'description': 'md5:c5afca6871ad59b4271e7704fe50ab04',
            'duration': 900,
            'thumbnail': r're:https?://.*\.jpg$',
        },
    }]

    def _is_film_page(self, webpage):
        return bool(webpage and 'jwplayer' in webpage and 'field_title' in webpage)

    def _download_film_page(self, url, video_id):
        webpage = self._download_webpage(
            url, video_id, expected_status=(403, 405))
        if self._is_film_page(webpage):
            return webpage

        snapshot = self._download_json(
            'https://archive.org/wayback/available', video_id,
            'Resolving Wayback Machine snapshot',
            query={'url': f'https://movingimage.nls.uk/film/{video_id}'})
        snapshot_url = traverse_obj(
            snapshot, ('archived_snapshots', 'closest', 'url', {url_or_none}))
        if snapshot_url:
            snapshot_url = re.sub(
                r'(?i)^https?://web\.archive\.org/web/(\d+)/',
                r'https://web.archive.org/web/\1id_/', snapshot_url)
            webpage = self._download_webpage(
                snapshot_url, video_id, 'Downloading webpage from Wayback Machine')
            if self._is_film_page(webpage):
                return webpage

        raise ExtractorError(
            'NLS Moving Image Archive blocks automated access with an AWS WAF captcha',
            expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_film_page(url, video_id)

        formats = self._extract_m3u8_formats(
            self._html_search_regex(
                r'file\s*:\s*"([^"]+\.m3u8[^"]*)"', webpage, 'm3u8 manifest URL'),
            video_id, ext='mp4', entry_protocol='m3u8_native')

        def search_field(field_name, fatal=False):
            return self._search_regex(
                rf'<span\s+class="field_title">{field_name}:</span>\s*<span\s+class="field_content">([^<]+)</span>',
                webpage, field_name.lower(), fatal=fatal)

        title = unescapeHTML(search_field('Title', fatal=True)).strip('()[]')
        description = unescapeHTML(search_field('Description'))
        running_time = search_field('Running time')
        duration = parse_duration(running_time)
        if duration is None and running_time:
            mins = self._search_regex(
                r'([\d.]+)\s*min', running_time, 'duration minutes', default=None)
            if mins:
                duration = int(float(mins) * 60)
        thumbnail = self._search_regex(
            r"image\s*:\s*'([^']+)'", webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
        }
