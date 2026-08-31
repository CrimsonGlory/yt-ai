import codecs
import hashlib
import re
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    mimetype2ext,
    traverse_obj,
    url_or_none,
)


class GofileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gofile\.io/d/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://gofile.io/d/AMZyDw',
        'skip': 'Login required',
        'info_dict': {
            'id': 'AMZyDw',
        },
        'playlist_mincount': 2,
        'playlist': [{
            'info_dict': {
                'id': 'de571ac1-5edc-42e2-8ec2-bdac83ad4a31',
                'filesize': 928116,
                'ext': 'mp4',
                'title': 'nuuh',
                'release_timestamp': 1638338704,
                'release_date': '20211201',
            },
        }],
    }, {
        'url': 'https://gofile.io/d/is8lKr',
        'info_dict': {
            'id': 'TMjXd9',
            'ext': 'mp4',
        },
        'playlist_count': 0,
        'skip': 'No files found at provided URL.',
    }, {
        'url': 'https://gofile.io/d/TMjXd9',
        'skip': 'Rate limited',
        'info_dict': {
            'id': 'TMjXd9',
        },
        'playlist_count': 1,
    }, {
        'url': 'https://gofile.io/d/gqOtRf',
        'skip': 'Rate limited',
        'info_dict': {
            'id': 'gqOtRf',
        },
        'playlist_mincount': 1,
        'params': {
            'videopassword': 'password',
        },
    }, {
        'url': 'https://gofile.io/d/h92ILTbq',
        'skip': 'Guest sample folder; files expire',
        'info_dict': {
            'id': 'h92ILTbq',
            'title': 'test',
        },
        'playlist_mincount': 2,
    }]
    _API_BASE = 'https://api.gofile.io'
    _CLIENT_UA = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    _CLIENT_LANG = 'en-US'
    _WT_SALT = '12af056dacea0b'
    _WT_WINDOW = 14400
    _WT_SCRIPT_URLS = (
        'https://gofile.io/js/wt.obf.js',
        'https://gofile.io/dist/js/wt.obf.js',
    )
    _PAGE_SIZE = 100
    _TOKEN = None

    def _api_headers(self, website_token=None, auth=True):
        headers = {
            'Accept': 'application/json',
            'Origin': 'https://gofile.io',
            'Referer': 'https://gofile.io/',
            'User-Agent': self._CLIENT_UA,
            'X-BL': self._CLIENT_LANG,
        }
        if auth and self._TOKEN:
            headers['Authorization'] = f'Bearer {self._TOKEN}'
        if website_token:
            headers['X-Website-Token'] = website_token
        return headers

    def _website_token(self, account_token, window_offset=0):
        window = int(time.time() // self._WT_WINDOW) + window_offset
        raw = '{}::{}::{}::{}::{}'.format(
            self._CLIENT_UA, self._CLIENT_LANG, account_token or '', window, self._WT_SALT)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _extract_wt_salt(self, script):
        candidates = []
        for encoded in re.findall(r"'((?:\\x[0-9a-fA-F]{2})+)'", script):
            try:
                decoded = codecs.decode(encoded, 'unicode_escape')
            except (UnicodeDecodeError, ValueError):
                continue
            if re.fullmatch(r'[a-f0-9]{10,16}', decoded):
                candidates.append(decoded)
        candidates.extend(re.findall(r'["\']([a-f0-9]{10,16})["\']', script))
        return candidates[0] if candidates else None

    def _refresh_wt_salt(self):
        for url in self._WT_SCRIPT_URLS:
            script = self._download_webpage(
                url, None, 'Downloading Gofile website token script',
                fatal=False, headers={
                    'Referer': 'https://gofile.io/',
                    'User-Agent': self._CLIENT_UA,
                })
            salt = self._extract_wt_salt(script or '')
            if salt:
                type(self)._WT_SALT = salt
                return True
        return False

    def _real_initialize(self):
        token = self._get_cookies('https://gofile.io/').get('accountToken')
        if token:
            self._TOKEN = token.value
            return

        last_status = None
        for attempt in range(3):
            account_data = self._download_json(
                f'{self._API_BASE}/accounts', None, 'Getting a new guest account',
                data=b'{}', headers={
                    **self._api_headers(self._website_token(''), auth=False),
                    'Content-Type': 'application/json',
                }, expected_status=(401, 429))
            self._TOKEN = traverse_obj(account_data, ('data', 'token', {str}))
            if self._TOKEN:
                self._set_cookie('.gofile.io', 'accountToken', self._TOKEN)
                return
            last_status = traverse_obj(account_data, ('status', {str})) or 'unknown'
            if last_status == 'error-rateLimit' and attempt < 2:
                self._sleep(
                    3 * (attempt + 1), None,
                    msg_template='Gofile rate limit, retrying in %(timeout)s seconds')
                continue
            break
        raise ExtractorError(
            f'Unable to create Gofile guest account: {last_status}', expected=True)

    def _raise_for_status(self, response, content_id):
        status = traverse_obj(response, ('status', {str}))
        if status == 'error-passwordRequired':
            raise ExtractorError(
                'This video is protected by a password, use the --video-password option', expected=True)
        if status == 'error-passwordWrong':
            raise ExtractorError('Invalid password', expected=True)
        if status == 'error-notFound':
            raise ExtractorError('Requested content was not found', expected=True, video_id=content_id)
        if status == 'error-rateLimit':
            raise ExtractorError('Gofile rate limit reached, try again later', expected=True)
        if status != 'ok':
            raise ExtractorError(f'{self.IE_NAME} said: status {status}', expected=True)
        if traverse_obj(response, ('data', 'canAccess')) is False:
            raise ExtractorError('This content is not accessible', expected=True, video_id=content_id)

    def _fetch_contents(self, content_id, page):
        query = {
            'page': page,
            'pageSize': self._PAGE_SIZE,
            'sortField': 'name',
            'sortDirection': 1,
        }
        if password := self.get_param('videopassword'):
            query['password'] = hashlib.sha256(password.encode()).hexdigest()

        def call(window_offset=0):
            return self._download_json(
                f'{self._API_BASE}/contents/{content_id}', content_id,
                'Getting filelist' if page == 1 and window_offset == 0 else f'Getting filelist page {page}',
                query=query, headers=self._api_headers(
                    self._website_token(self._TOKEN, window_offset)),
                expected_status=(401, 403, 429))

        response = None
        for attempt in range(3):
            response = call()
            status = traverse_obj(response, ('status', {str}))
            if status == 'error-rateLimit' and attempt < 2:
                self._sleep(
                    3 * (attempt + 1), content_id,
                    msg_template='%(video_id)s: Gofile rate limit, retrying in %(timeout)s seconds')
                continue
            if status != 'error-notPremium':
                return response
            break

        self._refresh_wt_salt()
        for offset in (0, -1):
            response = call(offset)
            if traverse_obj(response, ('status', {str})) != 'error-notPremium':
                break
        return response

    def _file_entry(self, file):
        file_url = url_or_none(file.get('link'))
        file_id = traverse_obj(file, ('id', {str}))
        name = traverse_obj(file, ('name', {str})) or file_id
        if not file_url or not file_id:
            return None
        ext = determine_ext(name, default_ext=None) or mimetype2ext(file.get('mimetype'))
        title = name.rsplit('.', 1)[0] if name and '.' in name[1:] else name
        return {
            'id': file_id,
            'title': title,
            'url': file_url,
            'ext': ext,
            'filesize': int_or_none(file.get('size')),
            'release_timestamp': int_or_none(file.get('createTime')),
            'thumbnail': url_or_none(file.get('thumbnail')),
            'http_headers': {
                'Referer': 'https://gofile.io/',
                'Cookie': f'accountToken={self._TOKEN}',
            },
        }

    def _iter_folder(self, folder_id, page_data, visited):
        if folder_id in visited:
            return
        visited.add(folder_id)

        page = 1
        while page_data:
            self._raise_for_status(page_data, folder_id)
            data = traverse_obj(page_data, ('data', {dict})) or {}
            if data.get('type') == 'file':
                entry = self._file_entry(data)
                if entry:
                    yield entry
                return

            children = traverse_obj(data, ('children', {dict})) or traverse_obj(data, ('contents', {dict})) or {}
            for child in children.values():
                child_id = traverse_obj(child, ('id', {str}))
                if child.get('type') == 'folder' and child_id:
                    if child.get('canAccess') is False:
                        self.report_warning(
                            f'Skipping inaccessible folder {child.get("name") or child_id}')
                        continue
                    yield from self._iter_folder(
                        child_id, self._fetch_contents(child_id, 1), visited)
                    continue
                entry = self._file_entry(child)
                if entry:
                    yield entry

            if not traverse_obj(page_data, ('metadata', 'hasNextPage')):
                break
            page += 1
            page_data = self._fetch_contents(folder_id, page)

    def _real_extract(self, url):
        folder_id = self._match_id(url)
        first = self._fetch_contents(folder_id, 1)
        self._raise_for_status(first, folder_id)
        data = traverse_obj(first, ('data', {dict})) or {}
        return self.playlist_result(
            self._iter_folder(folder_id, first, set()),
            playlist_id=folder_id, playlist_title=traverse_obj(data, ('name', {str})))
