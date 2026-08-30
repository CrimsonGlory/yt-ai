import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    get_element_html_by_id,
    int_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class WedoTVIE(InfoExtractor):
    IE_DESC = 'wedotv.com'
    _VALID_URL = (
        r'https?://(?:(?:www\.)?wedotv\.com/[a-z]{2}-[a-z]{2}|[a-z]{2}-[a-z]{2}\.wedotv\.com)/'
        r'(?P<id>(?!(?:movies|series|channels|sport|contact|favorites|imprint|'
        r'privacy|recently-watched|terms)(?:[/?#]|$))[\w-]+)')
    _TESTS = [{
        'url': 'https://www.wedotv.com/de-de/family-business#family-business',
        'md5': '2d6be5396aafb75f4ba8fe6878ed4072',
        'info_dict': {
            'id': '34181',
            'ext': 'mp4',
            'display_id': 'family-business',
            'title': 'Family Business',
            'description': 'md5:b7b0a220ba696757058d8e11be6994c6',
            'duration': 6543,
            'categories': ['Movie'],
            'thumbnail': r're:https://cdn-images\.watch4\.com/.+',
            'timestamp': 599616000,
            'upload_date': '19890101',
        },
    }, {
        'url': 'https://www.wedotv.com/de-de/family-business',
        'only_matching': True,
    }, {
        'url': 'https://www.wedotv.com/es-es/my-name-is-nobody',
        'only_matching': True,
    }, {
        'url': 'https://www.wedotv.com/de-de/21-jump-street',
        'only_matching': True,
    }, {
        'url': 'https://es-es.wedotv.com/my-name-is-nobody',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = extract_attributes(
            get_element_html_by_id('start-player-button', webpage) or '').get('data-video-id')
        if not video_id:
            raise ExtractorError('No playable video found', expected=True)

        video_json = self._download_json(
            urljoin(url, '/api/player.get_video.php'), video_id,
            query={
                'video_id': video_id,
                '_cb': int(time.time() * 1000),
            },
            headers={
                'Accept': 'application/json',
                'Referer': url,
            })
        if traverse_obj(video_json, 'error'):
            raise ExtractorError(
                traverse_obj(video_json, ('error', {str})) or 'wedotv player API error',
                expected=True)

        video_url = traverse_obj(video_json, ('video_source', {url_or_none}))
        if not video_url:
            self.raise_no_formats('No video source', expected=True, video_id=video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            video_url, video_id, 'mp4', m3u8_id='hls')

        for sub in traverse_obj(video_json, ('subtitles', lambda _, v: url_or_none(v['src']))):
            subtitles.setdefault(sub.get('srclang') or 'und', []).append({
                'url': sub['src'],
                'name': sub.get('label'),
            })

        info = self._search_json_ld(webpage, video_id, default={})
        info.pop('url', None)
        info.pop('ext', None)

        return {
            **info,
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': (
                info.get('thumbnail')
                or traverse_obj(info, ('thumbnails', 0, 'url', {url_or_none}))
                or self._og_search_thumbnail(webpage)),
            **traverse_obj(video_json, {
                'title': ('title', {str}),
                'duration': ('duration', {int_or_none}),
                'categories': ('labels', ..., 'text', {str}, filter),
            }),
        }
