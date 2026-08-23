from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class RockstarGamesIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?rockstargames\.com/(?:[a-z]{2}/)?videos(?:/video/|#?/?\?.*\bvideo=|/)(?P<id>[\w-]+)/?'
    _TESTS = [{
        'url': 'https://www.rockstargames.com/videos/video/11544/',
        'md5': '03b5caa6e357a4bd50e3143fc03e5733',
        'info_dict': {
            'id': '11544',
            'ext': 'mp4',
            'title': 'Further Adventures in Finance and Felony Trailer',
            'description': 'md5:6d31f55f30cb101b5476c4a379e324a3',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1464876000,
            'upload_date': '20160602',
        },
    }, {
        'url': 'http://www.rockstargames.com/videos#/?video=48',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'https://www.rockstargames.com/videoplayer/videos/get-video.json',
            video_id, fatal=False, query={
                'id': video_id,
                'locale': 'en_us',
            }) or {}
        video = video.get('video') or {}

        formats = []
        for v in (video.get('files_processed') or {}).get('video/mp4') or []:
            if not v.get('src'):
                continue
            resolution = v.get('resolution')
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]$', resolution or '', 'height', default=None))
            formats.append({
                'url': self._proto_relative_url(v['src']),
                'format_id': resolution,
                'height': height,
            })

        youtube_id = video.get('youtube_id')
        if not formats and youtube_id:
            return self.url_result(youtube_id, 'Youtube')

        webpage = None
        if not formats:
            webpage = self._download_webpage(url, video_id)
            json_ld = self._search_json_ld(webpage, video_id, default={})
            content_url = json_ld.get('url') or json_ld.get('contentUrl') or self._og_search_video_url(webpage, default=None)
            if content_url:
                formats.append({'url': content_url})
            m3u8_url = self._search_regex(
                rf'(https?://videos\.rockstargames\.com/v4/{video_id}[^"\']*\.m3u8[^"\']*)',
                webpage, 'm3u8', default=None)
            if not m3u8_url:
                # HLS master used by the current player
                m3u8_url = f'https://videos.rockstargames.com/v4/{video_id}/index.m3u8'
            m3u8_fmts = self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(m3u8_fmts or [])
            youtube_url = self._search_regex(
                r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)',
                webpage, 'youtube', default=None)
            if not formats and youtube_url:
                return self.url_result(youtube_url, 'Youtube')

        title = video.get('title')
        if not title:
            webpage = webpage or self._download_webpage(url, video_id)
            title = self._og_search_title(webpage, default=video_id)

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': self._proto_relative_url(video.get('screencap')) or (
                self._og_search_thumbnail(webpage) if webpage else None),
            'timestamp': parse_iso8601(video.get('created')),
            'formats': formats,
        }
