import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
    unified_strdate,
    url_or_none,
    urljoin,
)


class GranicusIE(InfoExtractor):
    IE_NAME = 'Granicus'
    IE_DESC = 'Granicus public meetings'
    _VALID_URL = r'''(?x)
        https?://[\w.-]+\.granicus\.com/
        (?:
            (?:player/clip|videos)/
            |MediaPlayer\.php\?(?:[^#]*&)?clip_id=
        )(?P<id>\d+)
    '''
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://[\w.-]+\.granicus\.com/(?:player/clip|videos)/\d+[^"\']*)\1']
    _TESTS = [{
        'url': 'https://harrisonburg-va.granicus.com/player/clip/1234?view_id=4',
        'md5': '21279d1e54e78b6044d99ac6fdb4b357',
        'info_dict': {
            'id': '1234',
            'ext': 'mp4',
            'title': 'City Council on 2025-12-09 7:00 PM',
            'description': 'Live and Recorded Public meetings of City Council on 2025-12-09 7:00 PM for The City of Harrisonburg, VA',
            'upload_date': '20251209',
            'chapters': 'count:20',
        },
    }, {
        'url': 'https://harrisonburg-va.granicus.com/player/clip/1234',
        'only_matching': True,
    }, {
        'url': 'https://harrisonburg-va.granicus.com/MediaPlayer.php?view_id=4&clip_id=1234',
        'only_matching': True,
    }, {
        'url': 'https://harrisonburg-va.granicus.com/videos/1234/player',
        'only_matching': True,
    }]

    def _extract_stream_url(self, webpage):
        stream_url = self._search_regex(
            (r'\bvideo_url\s*=\s*(["\'])(?P<url>(?:https?:)?//[^"\']+)\1',
             r'\bstandardVideoUrl\s*=\s*(["\'])(?P<url>(?:https?:)?//[^"\']+)\1',
             r'<source[^>]+src=(["\'])(?P<url>(?:https?:)?//[^"\']+\.m3u8[^"\']*)\1'),
            webpage, 'stream URL', default=None, group='url')
        if not stream_url:
            return None
        return url_or_none(stream_url.replace('\\/', '/'))

    def _extract_chapters(self, webpage):
        chapters = []
        for start, title in re.findall(
                r'<div[^>]+class="index-point[^"]*"[^>]*\btime="(\d+)"[^>]*>([^<]+)',
                webpage):
            start_time = int(start)
            if chapters:
                chapters[-1]['end_time'] = start_time
            chapters.append({
                'start_time': start_time,
                'title': unescapeHTML(title).strip(),
            })
        return chapters or None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        stream_url = self._extract_stream_url(webpage)
        if not stream_url:
            player = self._download_webpage(
                urljoin(url, f'/videos/{video_id}/player'), video_id,
                'Downloading embed player', fatal=False)
            if player:
                stream_url = self._extract_stream_url(player)
        if not stream_url:
            raise ExtractorError('Unable to extract stream URL', expected=True)

        is_live = self._search_regex(
            r'var\s+isLive\s*=\s*(true|false)', webpage, 'is live',
            default='false') == 'true'
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            stream_url, video_id, 'mp4', m3u8_id='hls', live=is_live,
            headers={'Referer': url})

        caption_path = self._search_regex(
            r'(["\'])(?P<url>/videos/\d+/captions\.vtt)\1',
            webpage, 'captions', default=None, group='url')
        if caption_path:
            self._merge_subtitles(
                {'en': [{'url': urljoin(url, caption_path)}]},
                target=subtitles)

        title = (
            self._html_search_regex(
                r'<div[^>]+id="video-name"[^>]*>([^<]+)',
                webpage, 'title', default=None)
            or self._html_extract_title(webpage, default=None))

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta(
                'description', webpage, default=None),
            'upload_date': unified_strdate(self._search_regex(
                r'\bon\s+(\d{4}-\d{2}-\d{2})\b', title or '',
                'upload date', default=None)),
            'formats': formats,
            'subtitles': subtitles,
            'chapters': self._extract_chapters(webpage),
            'is_live': is_live,
        }
