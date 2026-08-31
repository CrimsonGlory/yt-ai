import hashlib
import json
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class YoukuTVIE(InfoExtractor):
    IE_NAME = 'youku:tv'
    IE_DESC = 'YOUKU International'
    _VALID_URL = r'https?://(?:www\.)?youku\.tv/(?:v/)?v_show/id_(?P<id>[A-Za-z0-9=]+)'
    _API = 'mtop.youku.play.ups.appinfo.get'
    _API_VERSION = '1.1'
    _APP_KEY = '34300712'
    _CKEY = 'DIl58SLFxFNndSV1GFNnMQVYkx1PP5tKe1siZu/86PR1u/Wh1Ptd+WOZsHHWxysSfAOhNJpdVWsdVJNsfJ8Sxd8WKVvNfAS8aS8fAOzYARzPyPc3JvtnPHjTdKfESTdnuTW6ZPvk2pNDh4uFzotgdMEFkzQ5wZVXl2Pf1/Y6hLK0OnCNxBj3+nb0v72gZ6b0td+WOZsHHWxysSo/0y9D2K42SaB8Y/+aD2K42SaB8Y/+ahU+WOZsHcrxysooUeND'
    _HEADERS = {
        'Origin': 'https://www.youku.tv',
        'Referer': 'https://www.youku.tv/',
    }
    _TESTS = [{
        'url': 'https://www.youku.tv/v/v_show/id_XNjU1NjE3MDc2MA==.html',
        'md5': '9f1b5f14af35f2285956e9b7e5e89f79',
        'info_dict': {
            'id': 'XNjU1NjE3MDc2MA==',
            'ext': 'mp4',
            'title': 'Trailer phần Núi Dung Lô đảo Lưỡng Giới',
            'uploader': 'YoukuChinaVi',
            'uploader_id': '2066785701',
            'uploader_url': 'https://www.youku.tv/profile/index/?uid=UODI2NzE0MjgwNA==',
            'duration': 75.2,
            'thumbnail': 'https://m.ykimg.com/054101016A757DFF3F84C7207B4D3113',
            'series': 'Thương Nguyên Đồ',
        },
        'params': {
            'format': 'bv',
            'hls_prefer_native': False,
        },
    }, {
        'url': 'https://www.youku.tv/v/v_show/id_XNTk3Mzg0NjYyNA==.html',
        'only_matching': True,
    }, {
        'url': 'https://www.youku.tv/v/v_show/id_XNjM1NDY4NjM0NA==.html?s=ddba12a33dc44673a604',
        'only_matching': True,
    }]

    def _get_cna(self, video_id):
        _, urlh = self._download_webpage_handle(
            'https://log.mmstat.com/eg.js', video_id, 'Retrieving cna info',
            impersonate=True)
        etag = urlh.headers.get('etag') or urlh.headers.get('ETag') or ''
        return etag.strip('"')

    def _call_ups(self, video_id):
        cna = self._get_cna(video_id)
        if cna:
            self._set_cookie('youku.tv', 'cna', cna)

        data_str = json.dumps({
            'steal_params': json.dumps({
                'ccode': '0597',
                'client_ip': '192.168.1.1',
                'utid': cna,
                'client_ts': int(time.time()),
                'version': '4.8.8',
                'ckey': self._CKEY,
            }, separators=(',', ':')),
            'biz_params': json.dumps({
                'vid': video_id,
                'preferClarity': 99,
                'extag': 'EXT-X-PRIVINF',
                'master_m3u8': 1,
                'media_type': 'standard,subtitle',
                'app_ver': '4.8.8',
            }, separators=(',', ':')),
            'ad_params': '{}',
        }, separators=(',', ':'))

        def query():
            timestamp = str(int(time.time() * 1000))
            token = ''
            for cookie in self.cookiejar:
                if cookie.name == '_m_h5_tk':
                    token = cookie.value.partition('_')[0]
                    break
            sign = hashlib.md5(
                f'{token}&{timestamp}&{self._APP_KEY}&{data_str}'.encode()).hexdigest()
            return {
                'jsv': '2.7.2',
                'appKey': self._APP_KEY,
                't': timestamp,
                'sign': sign,
                'api': self._API,
                'v': self._API_VERSION,
                'type': 'originaljson',
                'dataType': 'json',
                'timeout': '20000',
                'YKPid': '20160317PLF000211',
                'YKLoginRequest': 'true',
                'AntiFlood': 'true',
                'AntiCreep': 'true',
                'data': data_str,
            }

        url = f'https://acs.youku.tv/h5/{self._API}/{self._API_VERSION}/'
        result = self._download_json(
            url, video_id, 'Fetching mtop token', query=query(),
            headers=self._HEADERS, impersonate=True,
            require_impersonation=True, fatal=False)
        inner = traverse_obj(result, ('data', 'data', {dict})) or {}
        if inner.get('stream') or inner.get('video') or inner.get('error'):
            return inner
        result = self._download_json(
            url, video_id, query=query(), headers=self._HEADERS,
            impersonate=True, require_impersonation=True)
        return traverse_obj(result, ('data', 'data', {dict})) or {}

    def _handle_ups_error(self, error, video_id, has_drm=False):
        code = int_or_none(error.get('code'))
        note = clean_html(error.get('note')) or ''
        if code in (-6005, -3007) or '登录' in note:
            self.raise_login_required(note or 'This video requires you to log in')
        if code in (-4001, -6004) or '版权' in note:
            self.raise_geo_restricted(
                note or 'This video is not available in your region')
        if has_drm:
            self.report_drm(video_id)
        if note:
            raise ExtractorError(f'Youku said: {note}', expected=True)
        self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._call_ups(video_id)
        video = data.get('video') or {}
        error = data.get('error') or {}

        formats, subtitles, has_drm = [], {}, False
        for stream in traverse_obj(data, ('stream', ..., {dict})) or []:
            if stream.get('channel_type') == 'tail':
                continue
            license_uri = traverse_obj(stream, ('stream_ext', 'uri', {str}))
            if license_uri and 'drm-license' in license_uri:
                has_drm = True
                continue
            m3u8_url = url_or_none(stream.get('m3u8_url'))
            if not m3u8_url:
                continue
            stream_type = stream.get('stream_type') or 'hls'
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id=stream_type, fatal=False,
                headers=self._HEADERS)
            for f in fmts:
                f.setdefault('width', int_or_none(stream.get('width')))
                f.setdefault('height', int_or_none(stream.get('height')))
                f.setdefault('filesize', int_or_none(stream.get('size')))
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        for sub in traverse_obj(data, ('subtitle', ..., {dict})) or []:
            sub_url = url_or_none(sub.get('url'))
            if not sub_url:
                continue
            lang = traverse_obj(sub, ('subtitle_info_code', 0, {str})) or sub.get('subtitle_lang') or 'und'
            subtitles.setdefault(lang, []).append({
                'url': sub_url,
                'ext': determine_ext(sub_url, 'ass'),
            })

        if not formats:
            self._handle_ups_error(error, video_id, has_drm=has_drm)

        return {
            'id': video.get('encodeid') or video_id,
            'title': video.get('title'),
            'formats': formats,
            'subtitles': subtitles,
            'duration': float_or_none(video.get('seconds')),
            'thumbnail': url_or_none(video.get('logo')),
            'uploader': traverse_obj(data, ('uploader', 'username', {str})) or video.get('username'),
            'uploader_id': str_or_none(video.get('userid')),
            'uploader_url': url_or_none(traverse_obj(data, ('uploader', 'homepage', {str}))),
            'tags': video.get('tags') or None,
            'series': traverse_obj(data, ('show', 'title', {str})),
            'http_headers': self._HEADERS,
        }
