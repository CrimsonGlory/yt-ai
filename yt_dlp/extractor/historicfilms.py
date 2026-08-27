from .common import InfoExtractor
from ..utils import parse_duration


class HistoricFilmsIE(InfoExtractor):
    _VALID_URL = [
        r'https?://(?:www\.)?historicfilms\.com/(?:tapes/|play)(?P<id>\d+)',
        r'https?://(?:www\.)?historicfilms\.com/(?:search/)?\?(?:[^#]*?&)?reel=(?P<id>\d+)',
    ]
    _TESTS = [{
        'url': 'https://www.historicfilms.com/tapes/13604',
        'md5': '4385a4372bcc04c8a5242f2e269d8c91',
        'info_dict': {
            'id': '13604',
            'ext': 'mp4',
            'title': 'Historic Films: F-8016',
            'description': 'OHIO NEWSSTORIES: 4/14/72',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 722,
        },
    }, {
        'url': 'https://www.historicfilms.com/?reel=13604',
        'only_matching': True,
    }, {
        'url': 'http://www.historicfilms.com/tapes/4728',
        'skip': 'video gone',
        'md5': 'd4a437aec45d8d796a38a215db064e9a',
        'info_dict': {
            'id': '4728',
            'ext': 'mov',
            'title': 'Historic Films: GP-7',
            'description': 'md5:1a86a0f3ac54024e419aba97210d959a',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2096,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            f'https://www.historicfilms.com/tapes/{video_id}', video_id)

        tape_id = self._search_regex(
            [r'class="tapeId"[^>]*>([^<]+)<', r'tapeId\s*:\s*"([^"]+)"'],
            webpage, 'tape id')
        video_url = self._og_search_video_url(webpage, default=None)
        if not video_url:
            video_url = f'https://www.historicfilms.com/video/{tape_id}_{video_id}_web.mp4'

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._html_search_meta(
                'thumbnailUrl', webpage, 'thumbnails') or self._og_search_thumbnail(webpage),
            'duration': parse_duration(self._html_search_meta(
                'duration', webpage, 'duration')),
        }
