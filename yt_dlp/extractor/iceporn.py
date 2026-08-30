import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    url_or_none,
)


class IcePornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?iceporn\.com/(?:video|embed)/(?P<id>\d+)(?:/(?P<display_id>[\w-]+))?'
    _EMBED_REGEX = [r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//(?:www\.)?iceporn\.com/embed/\d+)']
    _TESTS = [{
        'url': 'https://www.iceporn.com/video/2296835/eva-karera-gets-her-trimmed-cunt-plowed',
        'md5': '88be0402a06e61cd1dfaea69dc8623a7',
        'info_dict': {
            'id': '2296835',
            'display_id': 'eva-karera-gets-her-trimmed-cunt-plowed',
            'ext': 'mp4',
            'title': 'Eva Karera gets her trimmed cunt plowed',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 2178,
            'age_limit': 18,
            'uploader': 'ginstumpy',
            'categories': ['Big Boobs', 'Blowjob', 'Brunette', 'Doggystyle', 'Hardcore', 'Hd', 'Lingerie', 'Masturbation', 'Milf', 'Pornstar', 'Titjob'],
        },
    }, {
        'url': 'https://www.iceporn.com/embed/2296835',
        'only_matching': True,
    }, {
        'url': 'https://m.iceporn.com/video/2296835/eva-karera-gets-her-trimmed-cunt-plowed',
        'only_matching': True,
    }]
    _QUALITIES = {
        'lq': 320,
        'hq': 720,
        '4k': 2160,
    }

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id, fatal=False) or ''

        video_data = self._download_json(
            'https://www.iceporn.com/player_config_json/', video_id, query={
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
            r'<title>([^<]+?)\s*(?:-|@)\s+', webpage, 'title', default=None)
        duration = int_or_none(video_data.get('duration')) or parse_duration(
            video_data.get('duration_format'))
        thumbnail = url_or_none(video_data.get('poster')) or self._html_search_regex(
            r'<video[^>]+poster="([^"]+)"', webpage, 'thumbnail', default=None)

        cats_str = self._search_regex(
            r'<div[^>]+class="data_categories"[^>]*>(.+?)</div>',
            webpage, 'categories', default='')
        categories = re.findall(r'<a[^>]+title="([^"]+)"', cats_str) or None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': self._rta_search(webpage) or 18,
            'uploader': self._html_search_regex(
                r'Submitted:\s*<a[^>]+>([^<]+)', webpage, 'uploader', default=None),
            'categories': categories,
        }
