import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    extract_attributes,
    get_element_by_class,
    get_elements_by_class,
    int_or_none,
    parse_filesize,
    remove_end,
    traverse_obj,
    unified_strdate,
    unified_timestamp,
    url_or_none,
    urlencode_postdata,
)


class CyberfileBaseIE(InfoExtractor):
    _BASE = 'https://cyberfile.me'

    def _call_ajax(self, path, video_id, data, note, referer):
        return self._download_json(
            f'{self._BASE}{path}',
            video_id,
            note,
            data=urlencode_postdata(data),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self._BASE,
                'Referer': referer,
                'X-Requested-With': 'XMLHttpRequest',
            },
        )

    def _raise_unavailable(self, html, video_id):
        if 'File has been removed' in html:
            raise ExtractorError('File has been removed', expected=True, video_id=video_id)
        if 'File is not publicly available' in html:
            raise ExtractorError('File is not publicly available', expected=True, video_id=video_id)
        if re.search(r'src=["\'][^"\']+/recaptcha/api\.js', html):
            raise ExtractorError('CyberFile is blocking this request with reCAPTCHA', expected=True)


class CyberfileIE(CyberfileBaseIE):
    IE_NAME = 'cyberfile'
    IE_DESC = 'CyberFile'
    _VALID_URL = (
        r'https?://(?:www\.)?cyberfile\.me/'
        r'(?!(?:folder|shared|account|api|register|login|plugins|themes|cache|ajax|js|assets)(?:/|$|[?#]))'
        r'(?P<id>[A-Za-z0-9]+)(?:/[^/?#]*)?'
    )
    _TESTS = [
        {
            'url': 'https://cyberfile.me/bpfD',
            'md5': '712bc59abb39354e95c4e046b283fb2f',
            'info_dict': {
                'id': 'bpfD',
                'ext': 'mp4',
                'title': 'Raindrops',
                'thumbnail': r're:https?://.+',
                'uploader': 'barbarella',
                'timestamp': 1704384086,
                'upload_date': '20240104',
                'tags': ['raindrops', 'mp4'],
            },
        },
        {
            'url': 'https://www.cyberfile.me/bpfD',
            'only_matching': True,
        },
    ]

    def _unlock_file(self, video_id):
        password = self.get_param('videopassword')
        if not password:
            raise ExtractorError('This file is password protected, use --video-password', expected=True)
        webpage = self._download_webpage(
            f'{self._BASE}/{video_id}?pt=',
            video_id,
            'Submitting file password',
            data=urlencode_postdata(
                {
                    'filePassword': password,
                    'submitme': '1',
                },
            ),
        )
        if re.search(r'id=["\']filePassword["\']', webpage):
            raise ExtractorError('Invalid password', expected=True)
        return webpage

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        if re.search(r'id=["\']filePassword["\']', webpage):
            webpage = self._unlock_file(video_id)
        self._raise_unavailable(webpage, video_id)

        numeric_id = self._search_regex(r'showFileInformation\((\d+)\)', webpage, 'numeric file id')
        if numeric_id == '0':
            raise ExtractorError('Unable to find file information', expected=True)

        details = self._call_ajax(
            '/account/ajax/file_details', video_id, {'u': numeric_id}, 'Downloading file details', url,
        )
        html = traverse_obj(details, ('html', {str})) or ''
        self._raise_unavailable(html, video_id)

        download_url = url_or_none(
            self._search_regex(
                r'openUrl\((["\'])(?P<url>https?://[^"\']+?download_token=[^"\']+)\1',
                html,
                'download url',
                group='url',
                default=None,
            )
            or self._search_regex(
                r'<source[^>]+src=(["\'])(?P<url>https?://[^"\']+)\1', html, 'source url', group='url', default=None,
            ),
        )
        if not download_url:
            raise ExtractorError('Unable to extract download URL', expected=True)

        filename = (
            clean_html(get_element_by_class('image-name-title', html))
            or remove_end(self._og_search_title(webpage, default=''), ' - CyberFile')
            or video_id
        )
        filename = re.sub(r'(?:\s*-\s*CyberFile)+$', '', filename).strip() or video_id
        ext = determine_ext(filename, default_ext=None) or determine_ext(download_url, default_ext=None)
        title = filename
        if ext and title.lower().endswith(f'.{ext.lower()}'):
            title = title[: -(len(ext) + 1)]

        upload_date_str = self._html_search_regex(
            r'Uploaded:\s*</td>\s*<td[^>]*>([^<]+)', html, 'upload date', default=None,
        )

        return {
            'id': video_id,
            'title': title,
            'url': download_url,
            'ext': ext,
            'thumbnail': url_or_none(
                self._search_regex(
                    r'data-poster=(["\'])(?P<url>https?://[^"\']+)\1', html, 'thumbnail', group='url', default=None,
                )
                or self._og_search_thumbnail(webpage, default=None),
            ),
            'uploader': self._html_search_regex(
                r'Added By:\s*</td>\s*<td[^>]*>([^<]+)', html, 'uploader', default=None,
            ),
            'filesize': parse_filesize(
                self._html_search_regex(r'Filesize:\s*</td>\s*<td[^>]*>([^<]+)', html, 'filesize', default=None),
            ),
            'timestamp': unified_timestamp(upload_date_str),
            'upload_date': unified_strdate(upload_date_str),
            'tags': [t for t in map(clean_html, get_elements_by_class('tag', html) or []) if t] or None,
            'http_headers': {'Referer': f'{self._BASE}/'},
        }


class CyberfileFolderIE(CyberfileBaseIE):
    IE_NAME = 'cyberfile:folder'
    _VALID_URL = r'https?://(?:www\.)?cyberfile\.me/folder/(?P<id>[0-9a-f]+)(?:/[^/?#]*)?'
    _TESTS = [
        {
            'url': 'https://cyberfile.me/folder/82d0aab0853fdd13294171577081f4d8/Playlist',
            'info_dict': {
                'id': '82d0aab0853fdd13294171577081f4d8',
                'title': 'Playlist',
            },
            'playlist_mincount': 2,
            'params': {'skip_download': True},
        },
        {
            'url': 'https://cyberfile.me/folder/1524a09fa9d773dcc88c841ed2e098c9/Playlist_Protected',
            'info_dict': {
                'id': '1524a09fa9d773dcc88c841ed2e098c9',
                'title': 'Playlist Protected',
            },
            'playlist_mincount': 2,
            'params': {
                'skip_download': True,
                'videopassword': 'sample_pwd',
            },
        },
        {
            'url': 'https://cyberfile.me/folder/82d0aab0853fdd13294171577081f4d8',
            'only_matching': True,
        },
    ]

    def _unlock_folder(self, folder_id, node_id, html, referer):
        password = self.get_param('videopassword')
        if not password:
            raise ExtractorError('This folder is password protected, use --video-password', expected=True)
        node_id = (
            node_id
            or self._search_regex(
                r'<input[^>]+(?:id|name)=["\']folderId["\'][^>]+value=["\'](\d+)', html, 'folder node id', default=None,
            )
            or self._search_regex(
                r'<input[^>]+value=["\'](\d+)["\'][^>]+(?:id|name)=["\']folderId["\']', html, 'folder node id',
            )
        )
        resp = self._call_ajax(
            '/ajax/folder_password_process',
            folder_id,
            {
                'folderPassword': password,
                'folderId': node_id,
                'submitme': '1',
            },
            'Submitting folder password',
            referer,
        )
        if not traverse_obj(resp, ('success', {bool})):
            raise ExtractorError('Invalid password', expected=True)
        return node_id

    def _load_files(self, folder_id, node_id, page, referer):
        return self._call_ajax(
            '/account/ajax/load_files',
            folder_id,
            {
                'pageType': 'folder',
                'perPage': '100',
                'filterOrderBy': '',
                'nodeId': node_id,
                'pageStart': str(page),
            },
            'Downloading folder listing' if page == 1 else f'Downloading folder listing page {page}',
            referer,
        )

    def _real_extract(self, url):
        folder_id = self._match_id(url)
        webpage = self._download_webpage(url, folder_id)
        if re.search(r'id=["\']form_login["\']', webpage):
            raise ExtractorError('Folder has been deleted', expected=True)

        node_id = self._search_regex(r"loadImages\(\s*'folder'\s*,\s*'(\d+)'", webpage, 'node id')
        title = re.sub(r'(?:\s*-\s*CyberFile)+$', '', self._html_extract_title(webpage, default='') or '')
        title = remove_end(title, ' Folder').strip() or folder_id

        entries, page, total_pages = [], 1, 1
        while page <= total_pages:
            listing = self._load_files(folder_id, node_id, page, url)
            html = traverse_obj(listing, ('html', {str})) or ''
            if re.search(r'id=["\']folderPasswordForm["\']', html):
                node_id = self._unlock_folder(folder_id, node_id, html, url) or node_id
                listing = self._load_files(folder_id, node_id, page, url)
                html = traverse_obj(listing, ('html', {str})) or ''
                if re.search(r'id=["\']folderPasswordForm["\']', html):
                    raise ExtractorError('Invalid password', expected=True)
            self._raise_unavailable(html, folder_id)

            if page == 1:
                total_pages = (
                    int_or_none(
                        self._search_regex(
                            r'id=["\']rspTotalPages["\'][^>]*value=["\'](\d+)', html, 'total pages', default='1',
                        ),
                    )
                    or 1
                )

            for item_html in re.findall(r'<div[^>]+dtfullurl=["\'][^"\']+["\'][^>]*>', html):
                attrs = extract_attributes(item_html)
                file_url = url_or_none(attrs.get('dtfullurl'))
                if not file_url:
                    continue
                file_id = self._search_regex(
                    r'https?://(?:www\.)?cyberfile\.me/([A-Za-z0-9]+)', file_url, 'file id', default=None,
                )
                entries.append(self.url_result(file_url, CyberfileIE, file_id))
            page += 1

        return self.playlist_result(entries, folder_id, title or None)
