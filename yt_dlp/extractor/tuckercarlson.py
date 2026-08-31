import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TuckerCarlsonIE(InfoExtractor):
    IE_NAME = 'tuckercarlson'
    IE_DESC = 'Tucker Carlson Network'
    _VALID_URL = r'https?://(?:www\.)?tuckercarlson\.com/(?P<id>[a-z0-9]+(?:-[a-z0-9]+)*)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://tuckercarlson.com/the-okc-bomb-files-trailer',
        'md5': '33a4cb2573dc2eb3eeb2fa8d1ea7b38b',
        'info_dict': {
            'id': 'the-okc-bomb-files-trailer',
            'ext': 'mp4',
            'title': 'OFFICIAL TRAILER: The OKCBOMB Files: An Unofficial History',
            'description': 'md5:1f6beae6ab4dbb52427ac754ea1fe213',
            'thumbnail': r're:https://assets\.tuckercarlson\.com/.+',
            'duration': 97,
            'timestamp': 1787868000,
            'upload_date': '20260827',
        },
        # HLS --test only fetches the first fragment (~1KB), below the default 10KB check
        'params': {'format': 'bestvideo[protocol=m3u8_native]'},
        'file_minsize': None,
    }, {
        'url': 'https://tuckercarlson.com/the-vladimir-putin-interview/',
        'only_matching': True,
    }, {
        'url': 'https://www.tuckercarlson.com/the-vladimir-putin-interview',
        'only_matching': True,
    }, {
        'url': 'https://tuckercarlson.com/the-vladimir-putin-interview?watchedTime=120',
        'only_matching': True,
    }]

    def _extract_media_formats(self, media_url, video_id):
        formats, subtitles = [], {}
        ext = determine_ext(media_url)
        if ext == 'm3u8' or '/manifest/video.m3u8' in media_url:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
            dash_url = media_url.replace('/manifest/video.m3u8', '/manifest/video.mpd')
            if dash_url != media_url:
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    dash_url, video_id, mpd_id='dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
        elif ext == 'mpd':
            formats, subtitles = self._extract_mpd_formats_and_subtitles(
                media_url, video_id, mpd_id='dash', fatal=False)
        else:
            formats.append({
                'url': media_url,
                'ext': ext or 'mp4',
            })
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        media_url = json_ld.pop('url', None)
        json_ld.pop('ext', None)

        if not media_url:
            media_url = url_or_none(self._search_regex(
                r'(https?://customer-[\w-]+\.cloudflarestream\.com/[\da-f]{32}/manifest/video\.m3u8)',
                webpage, 'cloudflare stream', default=None))
        if not media_url:
            media_url = url_or_none(self._search_regex(
                r'\\?"hlsUrl\\?"\s*:\s*\\?"(https?://[^"\\]+\.m3u8)\\?"',
                webpage, 'livepeer hls', default=None))

        if not media_url:
            if re.search(r'Video(?:Paywall|Locked)Overlay', webpage):
                self.raise_login_required(
                    'This video is only available for Tucker Carlson Network members',
                    metadata_available=True)
            self.raise_no_formats('No video source found', expected=True, video_id=video_id)

        formats, subtitles = self._extract_media_formats(media_url, video_id)
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        title = strip_or_none(json_ld.get('title')) or strip_or_none(
            self._og_search_title(webpage, default=None))
        thumbnail = traverse_obj(
            json_ld, ('thumbnails', 0, 'url', {url_or_none})) or self._og_search_thumbnail(
            webpage, default=None)

        return {
            'id': video_id,
            **json_ld,
            'title': title,
            'thumbnail': thumbnail or json_ld.get('thumbnail'),
            'formats': formats,
            'subtitles': subtitles,
        }
