import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    traverse_obj,
    update_url_query,
    url_or_none,
    urljoin,
)


class BunkrIE(InfoExtractor):
    IE_DESC = 'bunkr.cr'
    _VALID_URL = (
        r'https?://(?:www\.)?bunkr\.(?:cr|pk|si|sk|ws|ph|fi|ac|ci|ps|black|red|media|site)'
        r'/(?:f|v|i|d)/(?P<id>[\w-]+)')
    _TESTS = [{
        'url': 'https://bunkr.cr/f/4ykLcXfv142Bl',
        'md5': '51e9dddce458599e94a57aa2f917a5cc',
        'info_dict': {
            'id': '4ykLcXfv142Bl',
            'ext': 'mp4',
            'title': 'video_2024-01-03_11-05-47.mp4',
            'thumbnail': r're:https?://static\.scdn\.st/.+',
            'filesize': 73923028,
            'age_limit': 18,
        },
    }, {
        'url': 'https://bunkr.cr/f/jSIaskLIIIaB4',
        'only_matching': True,
    }, {
        'url': 'https://bunkr.cr/v/4ykLcXfv142Bl',
        'only_matching': True,
    }, {
        'url': 'https://bunkr.pk/f/ljzMkCwUuZKPu',
        'only_matching': True,
    }]
    _API_URL = 'https://dl.bunkr.cr/api/_001_v2'
    _SIGN_URL = 'https://glb-apisign.cdn.cr/sign'
    _DL_ORIGIN = 'https://dl.bunkr.cr'

    def _dl_headers(self, file_id):
        return {
            'Origin': self._DL_ORIGIN,
            'Referer': f'{self._DL_ORIGIN}/file/{file_id}',
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if 'requested page has been removed' in webpage or 'Resource not found' in webpage:
            raise ExtractorError('This file has been removed', expected=True)

        file_id = self._html_search_regex(r'data-file-id="(\d+)"', webpage, 'file id')
        meta = self._download_json(
            self._API_URL, video_id, 'Downloading file metadata',
            data=json.dumps({'id': file_id}).encode(),
            headers={
                'Content-Type': 'application/json',
                **self._dl_headers(file_id),
            })

        cdn = traverse_obj(meta, 'mediafiles', {url_or_none})
        path = traverse_obj(meta, 'path', {str})
        if not cdn or not path:
            raise ExtractorError('Unable to extract CDN URL', expected=True)

        sign = self._download_json(
            self._SIGN_URL, video_id, 'Signing download URL',
            query={'path': path}, headers=self._dl_headers(file_id))
        token = traverse_obj(sign, 'token', {str})
        if not token:
            raise ExtractorError('Unable to sign download URL', expected=True)

        filename = traverse_obj(meta, 'original', {str})
        query = {
            'token': token,
            'ex': traverse_obj(sign, 'ex', {int_or_none}),
        }
        if filename:
            query['n'] = filename

        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
            or filename or video_id)

        return {
            'id': video_id,
            'title': title,
            'url': update_url_query(urljoin(cdn, path), query),
            'ext': determine_ext(filename or path, default_ext='mp4'),
            'filesize': int_or_none(self._search_regex(
                r'Size=(\d+)', webpage, 'filesize', default=None)),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'age_limit': 18,
            'http_headers': {'Referer': 'https://bunkr.cr/'},
        }
