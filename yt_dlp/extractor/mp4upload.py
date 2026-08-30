import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_filesize,
    unified_strdate,
    url_or_none,
)


class Mp4UploadIE(InfoExtractor):
    IE_NAME = 'mp4upload'
    IE_DESC = 'mp4upload.com'
    _VALID_URL = r'https?://(?:www\.)?mp4upload\.com/(?:embed-)?(?P<id>[0-9a-zA-Z]{10,16})(?:\.html)?'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?mp4upload\.com/embed-[0-9a-zA-Z]+(?:\.html)?)']
    _FILE_NOT_FOUND_REGEXES = (
        r'>(?:404 - )?\s*File Not Found\s*<',
        r'File was deleted',
        r'The file you were looking for could not be found',
    )
    _TESTS = [{
        'url': 'https://www.mp4upload.com/1u1ug369cm0a',
        'md5': '2f350373b6ae81c16059ba9d0ea83f97',
        'info_dict': {
            'id': '1u1ug369cm0a',
            'ext': 'mp4',
            'title': 'One Piece - 1139.1K.mp4',
            'thumbnail': r're:https?://.*\.jpg',
            'filesize_approx': 313800000,
            'upload_date': '20250810',
        },
    }, {
        'url': 'https://www.mp4upload.com/embed-1u1ug369cm0a.html',
        'only_matching': True,
    }, {
        'url': 'https://mp4upload.com/1u1ug369cm0a',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            f'https://www.mp4upload.com/{video_id}', video_id,
            'Downloading file page', fatal=False) or ''
        if webpage and any(re.search(p, webpage) for p in self._FILE_NOT_FOUND_REGEXES):
            raise ExtractorError(f'Video {video_id} does not exist', expected=True)

        fields = self._hidden_inputs(webpage)
        title = (
            fields.get('fname')
            or self._html_search_regex(
                r'<h1[^>]*class="filename"[^>]*>([^<]+)', webpage, 'title', default=None)
            or video_id)

        embed_url = f'https://www.mp4upload.com/embed-{video_id}.html'
        embed = self._download_webpage(embed_url, video_id, 'Downloading embed page')
        if any(re.search(p, embed) for p in self._FILE_NOT_FOUND_REGEXES):
            raise ExtractorError(f'Video {video_id} does not exist', expected=True)

        video_url = url_or_none(self._search_regex(
            r'player\.src\(\s*\{[^}]*?\bsrc\s*:\s*(["\'])(?P<url>https?://.+?)\1',
            embed, 'video URL', group='url', flags=re.DOTALL))
        if not video_url:
            raise ExtractorError('Unable to extract video URL')

        thumbnail = url_or_none(self._search_regex(
            r'player\.poster\((["\'])(?P<url>https?://.+?)\1',
            embed, 'thumbnail', default=None, group='url'))

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'filesize_approx': parse_filesize(self._html_search_regex(
                r'<span class="meta-label">Size</span>([^<]+)',
                webpage, 'filesize', default=None)),
            'upload_date': unified_strdate(self._html_search_regex(
                r'<span class="meta-label">Uploaded</span>([^<]+)',
                webpage, 'upload date', default=None)),
            'http_headers': {'Referer': embed_url},
        }
