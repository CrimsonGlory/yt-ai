import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    get_element_by_class,
    parse_duration,
    remove_end,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CuriosityUIE(InfoExtractor):
    IE_DESC = 'Curiosity University'
    _VALID_URL = r'https?://(?:www\.)?curiosityu\.com/videos/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.curiosityu.com/videos/how-music-shapes-the-brain/',
        'md5': '47bd18ed00f2ec3292884b3796ddb1be',
        'info_dict': {
            'id': 'how-music-shapes-the-brain',
            'ext': 'mp4',
            'title': 'How Music Shapes the Brain',
            'description': 'md5:c5fa1aa2a64eb79d41cbfc085d3cb52d',
            'duration': 3933,
            'thumbnail': r're:https?://img\.curiositystream\.com/.+',
            'uploader': 'Indre Viskontas',
        },
        # DASH --test only fetches the fMP4 init fragment (~1KB), below the default 10KB check
        'file_minsize': None,
    }, {
        'url': 'https://www.curiosityu.com/videos/the-psychology-of-money-2',
        'only_matching': True,
    }, {
        'url': 'https://curiosityu.com/videos/how-music-shapes-the-brain/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        source = self._search_json(
            r'var\s+sourceConfig\s*=', webpage, 'bitmovin source', video_id, fatal=False)
        mpd_url = traverse_obj(source, ('dash', {url_or_none}))
        if not mpd_url:
            self.raise_login_required(
                'This Curiosity University video requires a membership', method=None)

        formats, subtitles = self._extract_mpd_formats_and_subtitles(
            mpd_url, video_id, mpd_id='dash')

        uploader = ' '.join((
            clean_html(get_element_by_class('odu-hero__author', webpage)) or '').split()) or None

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (
                self._html_search_regex(
                    r'<h1[^>]+class="[^"]*odu-hero__title[^"]*"[^>]*>(.+?)</h1>',
                    webpage, 'title', default=None)
                or remove_end(
                    self._html_extract_title(webpage, default=''),
                    ' – Curiosity University')
                or None),
            'description': self._html_search_regex(
                r'<h2[^>]*class="[^"]*overview-title[^"]*"[^>]*>\s*Overview\s*</h2>\s*<div class="content">(.*?)</div>',
                webpage, 'description', default=None, flags=re.DOTALL),
            'duration': parse_duration(self._search_regex(
                r'class=[\'"]video-duration[\'"][^>]*>Duration\s+([^<]+)',
                webpage, 'duration', default=None)),
            'thumbnail': traverse_obj(source, ('poster', {url_or_none})),
            'uploader': uploader,
        }
