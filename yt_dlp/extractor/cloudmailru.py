import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    traverse_obj,
    url_or_none,
)


class CloudMailRuIE(InfoExtractor):
    IE_NAME = 'cloudmailru'
    IE_DESC = 'Облако Mail.ru'
    _VALID_URL = r'https?://(?:www\.)?cloud\.mail\.ru/public/(?P<id>[^?#]+)'
    _TESTS = [
        {
            'url': 'https://cloud.mail.ru/public/G5WJ/pe2PchPC9',
            'md5': 'eeb5335b886f8fa043b238f9f5766e49',
            'info_dict': {
                'id': 'G5WJ-pe2PchPC9',
                'ext': 'mp4',
                'title': 'На дому_сети.mp4',
                'filesize': 68878166,
                'timestamp': 1755234407,
                'upload_date': '20250815',
                'thumbnail': r're:https?://thumb\.cloud\.mail\.ru/weblink/thumb/',
            },
        },
        {
            'url': 'https://cloud.mail.ru/public/q7w7/Uk7N33hg1',
            'only_matching': True,
        },
        {
            'url': 'https://cloud.mail.ru/public/C76Y/rumhiAWE3',
            'only_matching': True,
        },
        {
            'url': 'https://cloud.mail.ru/public/kFtx/E2t21RwxD',
            'only_matching': True,
        },
    ]
    _API_BASE = 'https://cloud.mail.ru/api/v2'

    def _weblink_to_id(self, weblink):
        return weblink.replace('/', '-')

    def _call_api(self, endpoint, video_id, weblink, note=None, **query):
        return self._download_json(
            f'{self._API_BASE}/{endpoint}',
            video_id,
            note or f'Downloading {endpoint} JSON',
            query={'weblink': weblink, 'api': '2', **query},
            expected_status=(400, 403, 404),
        )

    def _raise_api_error(self, data, weblink):
        status = int_or_none(data.get('status'), default=0)
        if status == 200:
            return
        error = traverse_obj(data, ('body', 'weblink', 'error', {str})) or data.get('body')
        if status == 404 or error == 'not_exists':
            raise ExtractorError(f'Weblink {weblink} does not exist', expected=True)
        if status in (400, 403):
            raise ExtractorError(f'Weblink {weblink} is private or password-protected', expected=True)
        raise ExtractorError(f'Unable to download weblink {weblink}: {error}')

    def _download_url(self, weblink, video_id):
        weblink_get = getattr(self, '_weblink_get_url', None)
        if not weblink_get:
            dispatcher = self._download_json(
                f'{self._API_BASE}/dispatcher', video_id, 'Downloading dispatcher JSON', query={'api': '2'},
            )
            weblink_get = traverse_obj(dispatcher, ('body', 'weblink_get', 0, 'url', {url_or_none}))
            self._weblink_get_url = weblink_get
        if not weblink_get:
            raise ExtractorError('Unable to extract download server')
        return '{}/{}'.format(weblink_get.rstrip('/'), urllib.parse.quote(weblink, safe='/'))

    def _extract_file(self, weblink, video_id, meta):
        name = traverse_obj(meta, ('name', {str})) or video_id
        ext = determine_ext(name, 'mp4')
        return {
            'id': video_id,
            'title': name,
            'ext': ext,
            'filesize': int_or_none(meta.get('size')),
            'timestamp': int_or_none(meta.get('mtime')),
            'thumbnail': f"https://thumb.cloud.mail.ru/weblink/thumb/vxw0/{urllib.parse.quote(weblink, safe='/')}",
            'formats': [
                {
                    'url': self._download_url(weblink, video_id),
                    'format_id': 'original',
                    'format_note': 'Original',
                    'ext': ext,
                    'filesize': int_or_none(meta.get('size')),
                    'quality': 1,
                    'http_headers': {
                        'Referer': f"https://cloud.mail.ru/public/{urllib.parse.quote(weblink, safe='/')}",
                    },
                },
            ],
        }

    def _extract_folder(self, weblink, playlist_id, name=None):
        entries = []
        offset = 0
        limit = 500
        while True:
            data = self._call_api('folder', playlist_id, weblink, limit=limit, offset=offset)
            self._raise_api_error(data, weblink)
            body = traverse_obj(data, ('body', {dict})) or {}
            name = name or traverse_obj(body, ('name', {str}))
            items = traverse_obj(body, ('list', ..., {dict})) or []
            if not items:
                break
            for item in items:
                item_weblink = traverse_obj(item, ('weblink', {str}))
                if not item_weblink:
                    continue
                entries.append(
                    self.url_result(
                        f"https://cloud.mail.ru/public/{urllib.parse.quote(item_weblink, safe='/')}",
                        ie=self.ie_key(),
                        video_id=self._weblink_to_id(item_weblink),
                        video_title=traverse_obj(item, ('name', {str})),
                    ),
                )
            offset += len(items)
            total = (int_or_none(traverse_obj(body, ('count', 'files'))) or 0) + (
                int_or_none(traverse_obj(body, ('count', 'folders'))) or 0
            )
            if len(items) < limit or (total and offset >= total):
                break
        return self.playlist_result(entries, playlist_id, name)

    def _real_extract(self, url):
        weblink = urllib.parse.unquote(self._match_id(url)).strip('/')
        video_id = self._weblink_to_id(weblink)

        data = self._call_api('file', video_id, weblink)
        self._raise_api_error(data, weblink)
        meta = traverse_obj(data, ('body', {dict})) or {}
        kind = traverse_obj(meta, ('kind', {str})) or traverse_obj(meta, ('type', {str}))
        if kind == 'folder':
            return self._extract_folder(weblink, video_id, traverse_obj(meta, ('name', {str})))
        return self._extract_file(weblink, video_id, meta)
