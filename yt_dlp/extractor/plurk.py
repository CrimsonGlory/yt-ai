import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    format_field,
    int_or_none,
    strip_or_none,
    unified_timestamp,
    update_url_query,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PlurkIE(InfoExtractor):
    IE_DESC = 'Plurk'
    _VALID_URL = r'https?://(?:www\.)?plurk\.com/p/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'https://www.plurk.com/p/3i84keeuho',
        'md5': '13ef731e12a2ebe0068dd1440e9525be',
        'info_dict': {
            'id': '3i84keeuho',
            'ext': 'mp4',
            'display_id': '3i84keeuho',
            'title': '功能更新 \n現在噗浪網頁和 App 最新版（iOS 7.20.0、Android 6.83.0），噗幣使用者可以上傳影片了！\n此功能目前為試營運中，相關使用說明下收留言區',
            'description': '功能更新 \n現在噗浪網頁和 App 最新版（iOS 7.20.0、Android 6.83.0），噗幣使用者可以上傳影片了！\n此功能目前為試營運中，相關使用說明下收留言區',
            'thumbnail': r're:https://video\.plurk\.com/.+\.jpg',
            'uploader': '噗浪技術部🛠',
            'uploader_id': 'plurkwork',
            'uploader_url': 'https://www.plurk.com/plurkwork',
            'duration': 27,
            'timestamp': 1768901431,
            'upload_date': '20260120',
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
            'age_limit': 0,
        },
    }, {
        'url': 'https://www.plurk.com/p/3i64kdqlzy',
        'only_matching': True,
    }, {
        'url': 'https://plurk.com/p/3i84keeuho',
        'only_matching': True,
    }]

    @staticmethod
    def _js_dates_to_json(code):
        return re.sub(r'new Date\("([^"]+)"\)', r'"\1"', code)

    def _extract_formats(self, video, video_id):
        token = traverse_obj(video, 'token', {str})
        query = {'verify': token} if token else {}
        formats = []

        mp4_url = traverse_obj(video, 'mp4_url', {url_or_none})
        if mp4_url:
            formats.append({
                'format_id': 'http',
                'url': update_url_query(mp4_url, query),
                'ext': 'mp4',
                'quality': 1,
                **traverse_obj(video, {
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                }),
            })

        hls_url = traverse_obj(video, 'hls_url', {url_or_none})
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                update_url_query(hls_url, query), video_id, 'mp4',
                m3u8_id='hls', fatal=False))
        return formats

    def _real_extract(self, url):
        plurk_id = self._match_id(url)
        webpage = self._download_webpage(url, plurk_id)

        plurk = self._search_json(
            r'\bplurk\s*=', webpage, 'plurk', plurk_id,
            transform_source=self._js_dates_to_json)
        page_user = traverse_obj(self._search_json(
            r'\bGLOBAL\s*=', webpage, 'global', plurk_id,
            transform_source=self._js_dates_to_json, fatal=False, default={}),
            'page_user', {dict}) or {}

        videos = traverse_obj(plurk, (
            'videos', lambda _, v: url_or_none(v.get('mp4_url')) or url_or_none(v.get('hls_url'))))
        if not videos:
            raise ExtractorError('This Plurk does not contain a video', expected=True)

        nick_name = traverse_obj(page_user, 'nick_name', {str})
        text = (
            strip_or_none(clean_html(traverse_obj(plurk, 'content', {str})))
            or strip_or_none(traverse_obj(plurk, 'content_raw', {str})))
        common = {
            'title': text or self._og_search_title(webpage, default=None) or f'Plurk {plurk_id}',
            'description': text,
            'uploader': traverse_obj(page_user, 'display_name', {str}) or nick_name,
            'uploader_id': nick_name or traverse_obj(page_user, ('id', {str})),
            'uploader_url': format_field(nick_name, None, 'https://www.plurk.com/%s'),
            'age_limit': 18 if traverse_obj(plurk, 'porn') else 0,
            **traverse_obj(plurk, {
                'timestamp': ('posted', {unified_timestamp}),
                'like_count': ('favorite_count', {int_or_none}),
                'comment_count': ('response_count', {int_or_none}),
                'repost_count': ('replurkers_count', {int_or_none}),
            }),
        }

        entries = []
        for idx, video in enumerate(videos):
            video_id = plurk_id if len(videos) == 1 else (
                traverse_obj(video, 'id', {str}) or f'{plurk_id}-{idx}')
            formats = self._extract_formats(video, video_id)
            if not formats:
                continue
            entries.append({
                **common,
                'id': video_id,
                'display_id': plurk_id,
                'formats': formats,
                **traverse_obj(video, {
                    'thumbnail': ('thumbnail', {url_or_none}),
                    'duration': ('duration', {int_or_none}),
                }),
            })

        if not entries:
            raise ExtractorError('Unable to extract Plurk video formats', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, plurk_id, common.get('title'))
