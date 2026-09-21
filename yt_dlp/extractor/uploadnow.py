import json
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class UploadNowIE(InfoExtractor):
    IE_NAME = 'uploadnow'
    IE_DESC = 'UploadNow'
    _VALID_URL = (
        r'https?://(?:www\.)?uploadnow\.io/(?:[a-z]{2}/)?'
        r'(?:files/(?P<id>[^/?#]+)|f/(?P<folder_share>[^/?#]+)|s/(?P<file_id>[^/?#]+)|share/?(?:$|[?#]))')
    _TESTS = [{
        'url': 'https://uploadnow.io/files/TWKzN8d',
        'skip': 'Guest sample folder; files expire',
        'info_dict': {
            'id': 'TWKzN8d',
            'title': 'jhqzd3tC',
        },
        'playlist_count': 3,
    }, {
        'url': 'https://uploadnow.io/f/g6dMJDT',
        'info_dict': {
            'id': 'g6dMJDT',
            'title': 'SMB0RoUS',
        },
        'playlist_mincount': 1,
        'params': {'skip_download': True},
    }, {
        'url': 'https://uploadnow.io/en/share?utm_source=g6dMJDT',
        'only_matching': True,
    }, {
        'url': 'https://uploadnow.io/en/files/TWKzN8d',
        'only_matching': True,
    }, {
        'url': 'https://www.uploadnow.io/files/TWKzN8d',
        'only_matching': True,
    }, {
        'url': 'https://uploadnow.io/s/dfd16b2a-809d-4194-91d2-9a08763bb79b',
        'only_matching': True,
    }]
    _API_BASE = 'https://uploadnow.io/api'
    _FIREBASE_SIGNUP = 'https://identitytoolkit.googleapis.com/v1/accounts:signUp'
    _FIREBASE_KEY = 'AIzaSyB1SU4XZ9ryZjgtlYLU2yX2OBrAM6ajSWo'
    _PAGE_SIZE = 40
    _TOKEN = None

    def _api_headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://uploadnow.io',
            'Referer': 'https://uploadnow.io/',
            'Authorization': f'Bearer {self._TOKEN}',
        }

    def _real_initialize(self):
        if self._TOKEN:
            return
        data = self._download_json(
            self._FIREBASE_SIGNUP, None, 'Getting a new guest account',
            query={'key': self._FIREBASE_KEY},
            data=json.dumps({'returnSecureToken': True}).encode(),
            headers={'Content-Type': 'application/json'})
        token = traverse_obj(data, ('idToken', {str}))
        if not token:
            raise ExtractorError('Unable to create UploadNow guest account', expected=True)
        self._TOKEN = token

    def _call_api(self, path, video_id, data, note, retry_auth=True):
        res = self._download_json_handle(
            f'{self._API_BASE}{path}', video_id, note,
            data=json.dumps(data).encode(),
            headers=self._api_headers(),
            expected_status=(400, 401, 403, 404))
        payload, urlh = res or ({}, None)
        status = getattr(urlh, 'status', None)
        if status == 401 and retry_auth:
            self._TOKEN = None
            self._real_initialize()
            return self._call_api(path, video_id, data, note, retry_auth=False)
        return payload if isinstance(payload, dict) else {}, status

    def _raise_for_status(self, payload, status, video_id):
        if status in (200, 201):
            return
        error = traverse_obj(payload, ('error', {str})) or 'Unknown error'
        codes = traverse_obj(payload, ('codes', ..., {str})) or []
        if payload.get('cloudflare_error') or payload.get('error_name') == 'browser_signature_banned':
            raise ExtractorError(
                'UploadNow blocked this request (Cloudflare). Try --impersonate chrome',
                expected=True, video_id=video_id)
        if status == 404:
            raise ExtractorError('Requested content was not found', expected=True, video_id=video_id)
        if 'NO_FILES_TO_DOWNLOAD' in codes:
            raise ExtractorError('No files found at provided URL', expected=True, video_id=video_id)
        if status in (401, 403) or 'PASSWORD_REQUIRED' in codes or 'INVALID_PASSWORD' in codes:
            if self.get_param('videopassword') or 'INVALID_PASSWORD' in codes:
                raise ExtractorError('Invalid password', expected=True, video_id=video_id)
            raise ExtractorError(
                'This content is private or password protected, use --video-password',
                expected=True, video_id=video_id)
        raise ExtractorError(f'{self.IE_NAME} said: {error}', expected=True, video_id=video_id)

    def _download_query(self, extra=None):
        query = {}
        password = self.get_param('videopassword')
        if password:
            query['password'] = password
        token = traverse_obj(extra, ('token', {str}))
        if token:
            query['token'] = token
        return query

    def _file_entry(self, file, extra=None, fatal=False):
        file_id = traverse_obj(file, ('id', {str}))
        folder_id = traverse_obj(file, ('folderId', {str}))
        name = traverse_obj(file, ('name', {str})) or file_id
        if not file_id or not folder_id:
            return None
        payload = {
            'folderGroups': [{
                'selectedFiles': [file_id],
                'selectedFolders': [],
                'folderId': folder_id,
            }],
            'stream': False,
            **self._download_query(extra),
        }
        data, status = self._call_api(
            '/file/downloads/links', file_id, payload, 'Getting download URL')
        try:
            self._raise_for_status(data, status, file_id)
        except ExtractorError as e:
            if fatal or status in (401, 403):
                raise
            self.report_warning(e.msg)
            return None
        file_url = url_or_none(data.get('url'))
        if not file_url:
            if fatal:
                raise ExtractorError('Unable to extract download URL', expected=True, video_id=file_id)
            self.report_warning(f'Unable to extract download URL for {name or file_id}')
            return None
        ext = determine_ext(name, default_ext=None)
        title = name.rsplit('.', 1)[0] if name and '.' in name[1:] else name
        return {
            'id': file_id,
            'title': title,
            'url': file_url,
            'ext': ext,
            'filesize': int_or_none(file.get('size')),
            'timestamp': parse_iso8601(file.get('createDate')),
            'http_headers': {'Referer': 'https://uploadnow.io/'},
        }

    def _iter_folder(self, folder_id, extra, visited, first_page=None):
        if folder_id in visited:
            return
        visited.add(folder_id)

        data = first_page
        start_after_folder = None
        start_after_file = None
        while True:
            if data is None:
                payload = {
                    'folderId': folder_id,
                    'limit': self._PAGE_SIZE,
                    'sortField': 'nameLowerCase',
                    'sortDirection': 'asc',
                    **self._download_query(extra),
                }
                if start_after_folder:
                    payload['startAfterFolder'] = start_after_folder
                if start_after_file:
                    payload['startAfterFile'] = start_after_file
                note = (
                    'Getting file list' if not (start_after_folder or start_after_file)
                    else 'Getting file list page')
                data, status = self._call_api(
                    '/file/search/folder-content', folder_id, payload, note)
                self._raise_for_status(data, status, folder_id)

            folders = traverse_obj(data, ('folders', ..., {dict})) or []
            files = traverse_obj(data, ('files', ..., {dict})) or []
            for child in folders:
                child_id = traverse_obj(child, ('id', {str}))
                if child_id:
                    yield from self._iter_folder(child_id, extra, visited)
            for file in files:
                entry = self._file_entry(file, extra)
                if entry:
                    yield entry

            if len(folders) < self._PAGE_SIZE and len(files) < self._PAGE_SIZE:
                break
            if folders:
                start_after_folder = traverse_obj(folders, (-1, 'id', {str})) or start_after_folder
            if files:
                start_after_file = traverse_obj(files, (-1, 'id', {str})) or start_after_file
            if not start_after_folder and not start_after_file:
                break
            data = None

    def _extract_file(self, file_id, extra):
        data, status = self._call_api(
            '/file/search/file', file_id, {'fileId': file_id}, 'Downloading file metadata')
        self._raise_for_status(data, status, file_id)
        entry = self._file_entry(data, extra, fatal=True)
        if not entry:
            raise ExtractorError('Unable to extract download URL', expected=True, video_id=file_id)
        return entry

    def _extract_folder(self, folder_id, extra):
        data, status = self._call_api(
            '/file/search/folder-content', folder_id, {
                'folderId': folder_id,
                'limit': self._PAGE_SIZE,
                'sortField': 'nameLowerCase',
                'sortDirection': 'asc',
                **self._download_query(extra),
            }, 'Getting file list')
        self._raise_for_status(data, status, folder_id)
        parent = traverse_obj(data, ('parentFolder', {dict})) or {}
        return self.playlist_result(
            self._iter_folder(folder_id, extra, set(), first_page=data),
            playlist_id=folder_id,
            playlist_title=traverse_obj(parent, ('name', {str})) or folder_id,
            playlist_description=traverse_obj(parent, ('description', {str}, filter)))

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        extra = {
            'token': (
                traverse_obj(qs, ('token', 0, {str}))
                or traverse_obj(qs, ('utm_content', 0, {str}))),
        }
        folder_id = (
            mobj.group('id')
            or mobj.group('folder_share')
            or traverse_obj(qs, ('utm_source', 0, {str})))
        file_id = mobj.group('file_id') or traverse_obj(qs, ('utm_medium', 0, {str}))
        if file_id and not folder_id:
            return self._extract_file(file_id, extra)
        if folder_id:
            return self._extract_folder(folder_id, extra)
        raise ExtractorError('Unable to determine UploadNow folder or file id', expected=True)
