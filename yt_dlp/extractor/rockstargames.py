from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    parse_resolution,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class RockstarGamesIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?rockstargames\.com/(?:[a-z]{2}/)?videos(?:/video/|#?/?\?.*\bvideo=|/)(?P<id>[\w-]+)/?'
    _TESTS = [{
        'url': 'https://www.rockstargames.com/videos/rk721912',
        'md5': 'd1af5ab1f2c8aafef38e4f76bea66741',
        'info_dict': {
            'id': 'rk721912',
            'ext': 'mp4',
            'title': 'An Extended Look',
            'description': 'md5:ca83aaedaf5f75b68ce1273b8415ce60',
            'thumbnail': r're:https?://.+\.jpg',
            'timestamp': 1787788800,
            'upload_date': '20260827',
        },
    }, {
        'url': 'https://www.rockstargames.com/videos/sok93cc8',
        'skip': 'video gone',
        'md5': '03b5caa6e357a4bd50e3143fc03e5733',
        'info_dict': {
            'id': 'sok93cc8',
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

    def _parse_video_files(self, files):
        formats = []
        for v in files or []:
            src = url_or_none(self._proto_relative_url(v.get('src')))
            if not src:
                continue
            resolution = v.get('resolution')
            formats.append({
                'url': src,
                'format_id': resolution,
                **parse_resolution(resolution),
            })
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = traverse_obj(self._download_json(
            f'https://videos.rockstargames.com/v4/{video_id}/data/en_us.json',
            video_id, fatal=False), ('data', 'video', {dict})) or {}

        if not video:
            video = traverse_obj(self._download_json(
                'https://www.rockstargames.com/videoplayer/videos/get-video.json',
                video_id, fatal=False, query={
                    'id': video_id,
                    'locale': 'en_us',
                }), ('video', {dict})) or {}

        formats = self._parse_video_files(video.get('files'))
        formats.extend(self._parse_video_files(
            traverse_obj(video, ('files_processed', 'video/mp4'))))

        youtube_id = video.get('youtubeId') or video.get('youtube_id')
        if not formats and youtube_id:
            return self.url_result(youtube_id, 'Youtube')

        webpage = None
        if not formats:
            webpage = self._download_webpage(url, video_id)
            json_ld = self._search_json_ld(webpage, video_id, default={})
            content_url = (
                json_ld.get('url')
                or json_ld.get('contentUrl')
                or self._og_search_video_url(webpage, default=None))
            if content_url:
                formats.append({'url': content_url})
            m3u8_url = self._search_regex(
                rf'(https?://videos\.rockstargames\.com/v4/{video_id}[^"\']*\.m3u8[^"\']*)',
                webpage, 'm3u8', default=None)
            if m3u8_url:
                formats.extend(self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False) or [])
            youtube_url = self._search_regex(
                r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)',
                webpage, 'youtube', default=None)
            if not formats and youtube_url:
                return self.url_result(youtube_url, 'Youtube')

        title = video.get('title')
        if not title:
            webpage = webpage or self._download_webpage(url, video_id)
            title = self._og_search_title(webpage, default=video_id)

        subtitles = {}
        for track in traverse_obj(video, ('tracks', ..., {dict})) or []:
            captions = url_or_none(track.get('captions'))
            lang = track.get('lang')
            if not captions or not lang:
                continue
            subtitles.setdefault(lang, []).append({
                'url': captions,
                'ext': 'vtt',
            })

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': self._proto_relative_url(video.get('screencap')) or (
                self._og_search_thumbnail(webpage) if webpage else None),
            'timestamp': parse_iso8601(video.get('created')) or unified_timestamp(
                video.get('createdFormatted')),
            'formats': formats,
            'subtitles': subtitles,
        }
