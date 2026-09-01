import hashlib
import hmac
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    update_url_query,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TeraBoxIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?terabox\.(?P<domain>app|com)/
        (?:
            (?:[\w-]+/)*(?:sharing/link|share/filelist)\?(?:[^#]*&)?surl=(?P<id>[^&#]+)
            |s/1(?P<sid>[^/?#]+)
        )
    '''
    _TESTS = [{
        'url': 'https://www.terabox.app/sharing/link?surl=DdE5omp0kAF1UGFQ_TGFHg',
        'md5': '12ff2f8a57beb4da70b4e8064cb6039c',
        'info_dict': {
            'id': 'DdE5omp0kAF1UGFQ_TGFHg',
            'ext': 'mp4',
            'title': 'bVWi4TNV1.mp4',
            'duration': 66,
            'width': 720,
            'height': 1280,
            'timestamp': 1785185834,
            'upload_date': '20260727',
            'age_limit': 18,
            'thumbnail': r're:https?://.*',
        },
    }, {
        'url': 'https://www.terabox.com/sharing/link?surl=DdE5omp0kAF1UGFQ_TGFHg',
        'md5': '12ff2f8a57beb4da70b4e8064cb6039c',
        'info_dict': {
            'id': 'DdE5omp0kAF1UGFQ_TGFHg',
            'ext': 'mp4',
            'title': 'bVWi4TNV1.mp4',
            'duration': 66,
            'width': 720,
            'height': 1280,
            'timestamp': 1785185834,
            'upload_date': '20260727',
            'age_limit': 18,
            'thumbnail': r're:https?://.*',
        },
    }, {
        'url': 'https://www.terabox.app/wap/share/filelist?surl=DdE5omp0kAF1UGFQ_TGFHg',
        'only_matching': True,
    }, {
        'url': 'https://www.terabox.app/s/1DdE5omp0kAF1UGFQ_TGFHg',
        'only_matching': True,
    }, {
        'url': 'https://www.terabox.app/indonesian/sharing/link?surl=DdE5omp0kAF1UGFQ_TGFHg',
        'only_matching': True,
    }, {
        'url': 'https://terabox.com/s/1DdE5omp0kAF1UGFQ_TGFHg',
        'only_matching': True,
    }, {
        'url': 'https://www.terabox.com/s/1fgJnEjTkrixpGx0hpwoJUg',
        'only_matching': True,
    }]
    _BASE_URL = 'https://www.terabox.app'
    _APP_ID = '250528'
    _CLIENT_TYPE = 0
    _CHANNEL = 'dubox'
    _STREAM_SIGN_KEY = b'iuuPc64E4Fhn0rTXEzrnbLph0o5qyEEa'
    _VERIFY_ERRNOS = {400141, 400210, 400310, 4000020}
    _MEDIA_EXTS = {
        '3g2', '3gp', 'aac', 'ac3', 'aif', 'aiff', 'asf', 'avi', 'flac', 'flv',
        'm2ts', 'm4a', 'm4v', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'ogg',
        'ogv', 'opus', 'rm', 'rmvb', 'ts', 'wav', 'webm', 'wma', 'wmv',
    }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id') or mobj.group('sid')
        self._BASE_URL = f'https://www.terabox.{mobj.group("domain")}'
        headers = {'Referer': url}

        webpage = self._download_webpage(
            url, video_id, impersonate=True, headers=headers)
        if webpage.lstrip().startswith('{'):
            self._raise_api_error(self._parse_json(webpage, video_id), video_id)

        js_token = self._search_regex(
            r'fn%28%22([0-9A-F]+)%22%29', webpage, 'jsToken', default='')
        cookie = self._get_cookies(self._BASE_URL).get('browserid')
        browserid = cookie.value if cookie else ''

        share = self._download_json(
            f'{self._BASE_URL}/share/list', video_id,
            'Downloading share file list', impersonate=True, headers={
                **headers,
                'Accept': 'application/json, text/plain, */*',
            }, query={
                'shorturl': video_id,
                'root': '1',
                'app_id': self._APP_ID,
            })
        self._raise_api_error(share, video_id)

        media = list(self._iter_media(share, video_id, headers))
        if not media:
            raise ExtractorError('No media files found in this share', expected=True)

        entries = [
            self._extract_file(item, share, video_id, js_token, browserid, headers)
            for item in media
        ]
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, video_id, traverse_obj(share, ('title', {str})))

    def _iter_media(self, share, video_id, headers, depth=0):
        for item in traverse_obj(share, ('list', ..., {dict})):
            if str(item.get('isdir') or '0') == '1':
                if depth >= 3 or not item.get('path'):
                    continue
                nested = self._download_json(
                    f'{self._BASE_URL}/share/list', video_id,
                    f'Downloading folder {item["path"]}', impersonate=True,
                    headers={**headers, 'Accept': 'application/json, text/plain, */*'},
                    query={
                        'shorturl': video_id,
                        'root': '0',
                        'dir': item['path'],
                        'app_id': self._APP_ID,
                    }, fatal=False)
                if not nested:
                    continue
                self._raise_api_error(nested, video_id)
                yield from self._iter_media(nested, video_id, headers, depth + 1)
                continue
            if self._is_media(item):
                yield item

    def _is_media(self, item):
        category = str(item.get('category') or '')
        if category in ('1', '2'):
            return True
        ext = determine_ext(item.get('server_filename'), default_ext=None)
        return ext in self._MEDIA_EXTS if ext else False

    def _extract_file(self, item, share, share_id, js_token, browserid, headers):
        fs_id = str(item['fs_id'])
        filename = item.get('server_filename') or fs_id
        timestamp = int(time.time())
        sign = hmac.new(
            self._STREAM_SIGN_KEY,
            f'{self._CLIENT_TYPE}{self._CHANNEL}{browserid}{timestamp}'.encode(),
            hashlib.sha1).hexdigest()
        m3u8_url = update_url_query(f'{self._BASE_URL}/share/streaming.m3u8', {
            'uk': share['uk'],
            'shareid': share['share_id'],
            'type': 'M3U8_FLV_264_480',
            'fid': fs_id,
            'sign': sign,
            'timestamp': timestamp,
            'esl': '1',
            'isplayer': '1',
            'ehps': '1',
            'clienttype': self._CLIENT_TYPE,
            'app_id': self._APP_ID,
            'web': '1',
            'channel': self._CHANNEL,
            'jsToken': js_token,
        })
        m3u8_doc = self._download_m3u8(m3u8_url, share_id, headers)
        # Embed the playlist so the downloader does not re-fetch /share/streaming.m3u8
        formats, _ = self._parse_m3u8_formats_and_subtitles(
            m3u8_doc, None, 'mp4', m3u8_id='hls', video_id=share_id)
        for fmt in formats:
            fmt['impersonate'] = True
            fmt['http_headers'] = headers

        return {
            'id': share_id,
            'title': filename,
            'formats': formats,
            'age_limit': 18 if int_or_none(item.get('is_adult')) else 0,
            **traverse_obj(item, {
                'duration': ('duration', {int_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'timestamp': ('server_ctime', {int_or_none}),
                'thumbnail': ('thumbs', ('url3', 'url2', 'url1'), {url_or_none}, any),
            }),
        }

    def _download_m3u8(self, m3u8_url, video_id, headers):
        last_error = None
        for attempt in range(3):
            m3u8_doc = self._download_webpage(
                m3u8_url, video_id, 'Downloading m3u8 playlist',
                impersonate=True, headers={**headers, 'Accept': '*/*'})
            if m3u8_doc.lstrip().startswith('#EXTM3U'):
                return m3u8_doc
            if not m3u8_doc.lstrip().startswith('{'):
                raise ExtractorError('Unexpected m3u8 response', expected=True, video_id=video_id)
            data = self._parse_json(m3u8_doc, video_id, fatal=False) or {}
            errno = int_or_none(traverse_obj(data, 'errno', 'code'))
            errmsg = traverse_obj(data, 'errmsg', 'show_msg', {str}) or ''
            if attempt < 2 and (errno in self._VERIFY_ERRNOS or 'need verify' in errmsg.lower()):
                last_error = data
                self._sleep(2 * (attempt + 1), video_id)
                continue
            self._raise_api_error(data, video_id)
        self._raise_api_error(last_error, video_id)

    def _raise_api_error(self, data, video_id):
        errno = int_or_none(traverse_obj(data, 'errno', 'code'))
        errmsg = traverse_obj(data, 'errmsg', 'show_msg', {str}) or ''
        if errno in (None, 0) and not errmsg:
            return
        if errno in self._VERIFY_ERRNOS or 'need verify' in errmsg.lower():
            raise ExtractorError(
                'TeraBox requires captcha verification for this share; try again later',
                expected=True, video_id=video_id)
        if errno == -6:
            self.raise_login_required(method=None)
        if errno in (-9, -12):
            raise ExtractorError(
                'This share is password protected; use --video-password',
                expected=True, video_id=video_id)
        raise ExtractorError(
            join_nonempty(f'TeraBox API error {errno}', errmsg, delim=': '),
            expected=True, video_id=video_id)
