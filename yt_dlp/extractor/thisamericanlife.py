from .common import InfoExtractor
from ..utils import (
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ThisAmericanLifeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisamericanlife\.org/(?:radio-archives/episode/|play_full\.php\?play=)?(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.thisamericanlife.org/487/harper-high-school-part-one',
        'md5': 'a1e2fce87af5597a86a32d47a57e9821',
        'info_dict': {
            'id': '487',
            'ext': 'mp3',
            'title': '487: Harper High School - Part One',
            'description': 'md5:2412f16614df435b101d5905948fd8c7',
            'thumbnail': r're:https?://.+',
            'timestamp': 1360904400,
            'upload_date': '20130215',
        },
    }, {
        'url': 'http://www.thisamericanlife.org/radio-archives/episode/487/#content',
        'only_matching': True,
    }, {
        'url': 'http://www.thisamericanlife.org/play_full.php?play=487',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        playlist = self._search_json(
            r'<script[^>]+id="playlist-data"[^>]*>', webpage, 'playlist data', video_id)

        audio_url = traverse_obj(playlist, (('archive', 'audio'), {url_or_none}), get_all=False)
        stream_url = traverse_obj(playlist, ('stream', {url_or_none}))

        formats = []
        if audio_url:
            formats.append({
                'format_id': 'http',
                'url': audio_url,
                'ext': 'mp3',
                'vcodec': 'none',
            })
        elif stream_url:
            formats.extend(self._extract_m3u8_formats(
                stream_url, video_id, 'm4a', m3u8_id='hls'))

        return {
            'id': video_id,
            'formats': formats,
            'vcodec': 'none',
            'title': traverse_obj(playlist, ('title', {str})) or self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': (
                traverse_obj(playlist, ('thumbnail', {url_or_none}))
                or self._og_search_thumbnail(webpage)),
            'timestamp': unified_timestamp(self._html_search_meta(
                'article:published_time', webpage, default=None)),
        }
