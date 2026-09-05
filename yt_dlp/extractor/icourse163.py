import hashlib
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_qs,
    qualities,
    str_or_none,
    strip_or_none,
    try_call,
    url_or_none,
    urlencode_postdata,
)
from ..utils.traversal import traverse_obj


class ICourse163IE(InfoExtractor):
    IE_NAME = 'icourse163'
    IE_DESC = '中国大学MOOC'
    _VALID_URL = r'https?://(?:www\.)?icourse163\.org/(?:spoc/)?(?:course|learn)/(?:(?P<school>[\w+]+)-)?(?P<id>\d+)'
    _HOME = 'https://www.icourse163.org'
    _TESTS = [
        {
            'url': 'https://www.icourse163.org/course/USTC-1462062166?tid=1465253471',
            'md5': '4594646de9b423af050d080fa2d039f0',
            'info_dict': {
            'id': '1217694729',
            'ext': 'mp4',
            'display_id': 'USTC-1462062166',
            'title': '天文学导论_中国科学技术大学',
            'alt_title': '课程片花',
            'description': '天文学导论,中国科学技术大学',
            'uploader': '薛永泉',
            'duration': 96,
            'thumbnail': 'https://nos.netease.com/edu-image/531233e396194667a3327378424a044c.png',
        },
        },
        {
            'url': 'https://www.icourse163.org/learn/USTC-1462062166?tid=1465253471',
            'only_matching': True,
        },
        {
            'url': 'https://www.icourse163.org/learn/USTC-1462062166?tid=1465253471#/learn/content?type=detail&id=1244068605',
            'only_matching': True,
        },
        {
            'url': 'https://www.icourse163.org/course/USTC-1462062166',
            'only_matching': True,
        },
    ]

    def _csrf_key(self):
        return try_call(lambda: self._get_cookies(self._HOME)['NTESSTUDYSI'].value)

    def _token_sign(self, biz_id, biz_type, content_type, timestamp, user_id=''):
        payload = f"{biz_id}{biz_type}{timestamp}88{content_type}mooc{user_id or ''}"
        return hashlib.md5(payload.encode()).hexdigest()

    def _call_rpc(self, bean_method, video_id, data, note):
        csrf = self._csrf_key()
        return self._download_json(
            f'{self._HOME}/web/j/{bean_method}.rpc',
            video_id,
            note,
            query={'csrfKey': csrf} if csrf else {},
            data=urlencode_postdata(data),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self._HOME,
                'Referer': f'{self._HOME}/',
            },
        )

    def _get_video_sign(self, biz_id, biz_type, video_id, user_id=''):
        timestamp = int(time.time() * 1000)
        token = self._call_rpc(
            'resourceRpcBean.getResourceTokenV2',
            video_id,
            {
                'bizId': biz_id,
                'bizType': biz_type,
                'contentType': '1',
                'sign': self._token_sign(biz_id, biz_type, 1, timestamp, user_id),
                'timestamp': timestamp,
            },
            'Downloading resource token',
        )
        if traverse_obj(token, 'code') not in (0, '0', None):
            raise ExtractorError(traverse_obj(token, ('message', {str})) or 'Unable to get video token', expected=True)
        sign_dto = traverse_obj(token, ('result', 'videoSignDto', {dict})) or {}
        if int_or_none(sign_dto.get('status'), default=0) not in (0, None):
            raise ExtractorError(traverse_obj(token, ('message', {str})) or 'Video is not available', expected=True)
        video_id = str_or_none(sign_dto.get('videoId'))
        signature = traverse_obj(sign_dto, ('signature', {str}))
        if not video_id or not signature:
            raise ExtractorError('Unable to extract video signature', expected=True)
        return sign_dto, video_id, signature

    def _extract_vod(self, video_id, signature):
        vod = self._download_json(
            'https://vod.study.163.com/eds/api/v1/vod/video',
            video_id,
            'Downloading VOD metadata',
            data=urlencode_postdata(
                {
                    'videoId': video_id,
                    'signature': signature,
                    'clientType': '1',
                },
            ),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self._HOME,
                'Referer': f'{self._HOME}/',
            },
        )
        if traverse_obj(vod, 'code') not in (0, '0', None):
            raise ExtractorError(traverse_obj(vod, ('message', {str})) or 'Unable to get video URL', expected=True)
        return traverse_obj(vod, ('result', {dict})) or {}

    def _extract_formats_and_subtitles(self, vod, video_id):
        formats, subtitles = [], {}
        quality = qualities((1, 2, 3))
        quality_note = {1: 'sd', 2: 'hd', 3: 'shd'}
        for video in traverse_obj(vod, ('videos', lambda _, v: url_or_none(v['videoUrl']))):
            if video.get('secondaryEncrypt') or video.get('k'):
                self.report_warning('Skipping AES-wrapped video URL', video_id=video_id)
                continue
            media_url = video['videoUrl'].replace('http://', 'https://', 1)
            q = int_or_none(video.get('quality'))
            fmt = (video.get('format') or '').lower()
            if fmt == 'hls' or '.m3u8' in media_url:
                m3u8_id = f'hls-{q}' if q is not None else 'hls'
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id=m3u8_id, fatal=False,
                )
                for f in fmts:
                    f.setdefault('quality', quality(q))
                    if q in quality_note:
                        f.setdefault('format_note', quality_note[q])
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append(
                    {
                        'url': media_url,
                        'ext': fmt or 'mp4',
                        'quality': quality(q),
                        'format_id': f"{fmt or 'http'}-{q}" if q is not None else (fmt or 'http'),
                        'format_note': quality_note.get(q),
                        'filesize': int_or_none(video.get('size')),
                    },
                )
        for caption in traverse_obj(
            vod, ('srtCaptions', lambda _, v: url_or_none(v.get('url')) or url_or_none(v.get('nosUrl'))),
        ):
            lang = traverse_obj(caption, ('lang', {str})) or traverse_obj(caption, ('name', {str})) or 'zh'
            subtitles.setdefault(lang, []).append(
                {
                    'url': caption.get('url') or caption.get('nosUrl'),
                    'ext': 'srt',
                },
            )
        return formats, subtitles

    def _real_extract(self, url):
        course_id = self._match_id(url)
        school = self._match_valid_url(url).group('school')
        display_id = f'{school}-{course_id}' if school else course_id

        term_id = traverse_obj(parse_qs(url), ('tid', 0, {str}))
        unit_id = traverse_obj(
            urllib.parse.parse_qs(urllib.parse.urlparse(url).fragment.partition('?')[2]), ('id', 0, {str}),
        )

        webpage = self._download_webpage(url, display_id)
        term_id = term_id or self._search_regex(r'termId\s*:\s*"(\d+)"', webpage, 'term id', default=None)
        user_id = self._search_regex(
            r'window\.webUser\s*=\s*\{[^}]*?\bid\s*:\s*"?(\d+)', webpage, 'user id', default='',
        )

        sign_dto, errors = None, []
        attempts = []
        if unit_id:
            attempts.append((unit_id, 1, 'lesson unit'))
        if term_id:
            attempts.append((term_id, 2, 'course preview'))
        for biz_id, biz_type, label in attempts:
            try:
                sign_dto, video_id, signature = self._get_video_sign(biz_id, biz_type, display_id, user_id)
                break
            except ExtractorError as e:
                errors.append(f'{label}: {e.msg}')
                self.report_warning(f'Unable to extract {label}: {e.msg}', display_id)
        else:
            raise ExtractorError(
                errors[-1] if errors else 'Unable to find a playable video (lesson units require login)', expected=True,
            )

        vod = self._extract_vod(video_id, signature)
        formats, subtitles = self._extract_formats_and_subtitles(vod, video_id)
        if not formats:
            self.raise_no_formats('No playable video formats', expected=True, video_id=video_id)

        video_name = traverse_obj(sign_dto, ('name', {str})) or traverse_obj(vod, ('name', {str}))
        if video_name and video_name.lower().endswith('.mp4'):
            video_name = video_name[:-4]
        title = self._og_search_title(webpage, default=None) or video_name

        return {
            'id': str(video_id),
            'display_id': display_id,
            'title': title,
            'alt_title': video_name,
            'description': self._og_search_description(webpage, default=None),
            'duration': int_or_none(sign_dto.get('duration')) or int_or_none(vod.get('duration')),
            'thumbnail': (
                url_or_none(sign_dto.get('videoImgUrl'))
                or url_or_none(vod.get('videoImgUrl'))
                or url_or_none(
                    self._search_regex(r'bigPhoto\s*:\s*"(https?://[^"]+)"', webpage, 'thumbnail', default=None),
                )
            ),
            'uploader': strip_or_none(
                self._search_regex(r'lectorName\s*:\s*"([^"]+)"', webpage, 'uploader', default=None),
            ),
            'formats': formats,
            'subtitles': subtitles,
        }
