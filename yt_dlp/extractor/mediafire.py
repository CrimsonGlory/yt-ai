from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    mimetype2ext,
    parse_iso8601,
    traverse_obj,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class MediaFireIE(InfoExtractor):
    IE_NAME = 'mediafire'
    IE_DESC = 'MediaFire'
    _VALID_URL = (
        r'https?://(?:www\.)?mediafire\.com/'
        r'(?:(?:file|download|view|watch|listen)/|\?)(?P<id>[a-z0-9]+)')
    _TESTS = [{
        'url': 'https://www.mediafire.com/file/bgv7rnx2bqngtiz/andai_aku_tidak_berburu.mp4/file',
        'md5': '8a712d5721df78d2720fcb97dfd82763',
        'info_dict': {
            'id': 'bgv7rnx2bqngtiz',
            'ext': 'mp4',
            'title': 'andai aku tidak berburu',
            'uploader': 'D M K Tiktok',
            'filesize': 23119518,
            'timestamp': 1635575701,
            'upload_date': '20211030',
        },
    }, {
        'url': 'http://www.mediafire.com/file/bgv7rnx2bqngtiz/mp4/file',
        'only_matching': True,
    }, {
        'url': 'https://www.mediafire.com/download/bgv7rnx2bqngtiz',
        'only_matching': True,
    }, {
        'url': 'https://www.mediafire.com/view/bgv7rnx2bqngtiz/andai_aku_tidak_berburu.mp4',
        'only_matching': True,
    }, {
        'url': 'https://www.mediafire.com/watch/bgv7rnx2bqngtiz/andai_aku_tidak_berburu.mp4',
        'only_matching': True,
    }, {
        'url': 'https://www.mediafire.com/?bgv7rnx2bqngtiz',
        'only_matching': True,
    }]
    _API_URL = 'https://www.mediafire.com/api/1.5/file/get_info.php'
    _UNAVAILABLE_HINTS = (
        'invalid or deleted file',
        'this file has been removed',
        'file has currently been flagged',
        'this file is currently unavailable',
        'the file you attempted to download is no longer available',
    )

    def _call_file_info(self, video_id):
        data = self._download_json(
            self._API_URL, video_id, 'Downloading file info',
            query={
                'quick_key': video_id,
                'response_format': 'json',
            }, fatal=False)
        response = traverse_obj(data, ('response', {dict})) or {}
        if not data:
            return {}
        if response.get('result') != 'Success':
            raise ExtractorError(
                traverse_obj(response, ('message', {str})) or 'Unable to get file info',
                expected=True)
        return traverse_obj(response, ('file_info', {dict})) or {}

    def _raise_if_unavailable(self, webpage, video_id, file_info):
        if traverse_obj(file_info, ('password_protected', {str})) == 'yes':
            raise ExtractorError('This file is password protected', expected=True, video_id=video_id)
        lower = webpage.lower()
        if any(hint in lower for hint in self._UNAVAILABLE_HINTS):
            raise ExtractorError('This file is no longer available', expected=True, video_id=video_id)
        if 'cf-turnstile' in lower:
            raise ExtractorError(
                'MediaFire is blocking this request with Cloudflare Turnstile',
                expected=True, video_id=video_id)

    def _extract_download_url(self, webpage, url, video_id):
        download_url = url_or_none(unescapeHTML(self._search_regex(
            (r'<a[^>]+id=["\']downloadButton["\'][^>]+href=["\']([^"\']+)',
             r'<a[^>]+href=["\']([^"\']+)["\'][^>]+id=["\']downloadButton["\']',
             r'(https?://download\d+\.mediafire\.com/[^"\'\s<>]+)'),
            webpage, 'download URL', default=None)))
        if not download_url:
            raise ExtractorError('Unable to extract download URL', video_id=video_id)
        return urljoin(url, download_url)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        file_info = self._call_file_info(video_id)
        webpage = self._download_webpage(url, video_id)
        self._raise_if_unavailable(webpage, video_id, file_info)

        download_url = self._extract_download_url(webpage, url, video_id)
        filename = traverse_obj(file_info, ('filename', {str}))
        title = (
            self._og_search_title(webpage, default=None)
            or (filename.rsplit('.', 1)[0] if filename else None)
            or video_id)

        return {
            'id': video_id,
            'url': download_url,
            'title': title,
            'ext': (
                mimetype2ext(traverse_obj(file_info, ('mimetype', {str})))
                or determine_ext(filename, default_ext=None)
                or determine_ext(download_url, default_ext='mp4')),
            'description': traverse_obj(file_info, ('description', {str}, filter)),
            'uploader': traverse_obj(file_info, ('owner_name', {str})),
            'filesize': traverse_obj(file_info, ('size', {int_or_none})),
            'timestamp': traverse_obj(file_info, ('created_utc', {parse_iso8601})),
            'http_headers': {'Referer': 'https://www.mediafire.com/'},
        }
