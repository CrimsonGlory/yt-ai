import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    unified_timestamp,
    url_or_none,
)


class TwentyMinutenIE(InfoExtractor):
    IE_NAME = '20min'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?20min\.ch/
                        (?:
                            videotv/*\?.*?\bvid=(?P<id>\d+)
                            |videoplayer/videoplayer\.html\?.*?\bvideoId@(?P<id2>\d+)
                            |video/(?:[^/?#]*-)?(?P<id3>\d+)
                            |story/(?:[^/?#]*-)?(?P<id4>\d+)
                        )
                    '''
    _EMBED_REGEX = [r'<iframe[^>]+src=(["\'])(?P<url>(?:(?:https?:)?//)?(?:www\.)?20min\.ch/videoplayer/videoplayer.html\?.*?\bvideoId@\d+.*?)\1']
    _TESTS = [{
        'url': 'https://www.20min.ch/video/abruzzen-touristen-kommen-dem-hirsch-zu-nah-er-wehrt-sich-mit-dem-geweih-103621983',
        'md5': '51e5434e7e9d8acc92cdca3b7ecf2bff',
        'info_dict': {
            'id': '103621983',
            'ext': 'mp4',
            'title': 'Touristen kommen dem Hirsch zu nah: Er wehrt sich mit dem Geweih',
            'description': 'md5:e6c7f6ba8b8402fad06e0b3b84aa4b79',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 34,
            'timestamp': 1787584088,
            'upload_date': '20260824',
        },
    }, {
        'url': 'http://www.20min.ch/story/live-interview-herr-blocher-was-verdienen-sie-wenn-russland-sanktionen-fallen-103621700',
        'skip': 'ticker page; use dedicated /video/ URLs',
        'md5': 'e7264320db31eed8c38364150c12496e',
        'info_dict': {
            'id': '103621700',
            'ext': 'mp4',
            'title': '85 000 Franken für 15 perfekte Minuten',
            'thumbnail': r're:https?://.+\.jpg',
        },
    }, {
        'url': 'http://www.20min.ch/videoplayer/videoplayer.html?params=client@twentyDE|videoId@523629',
        'skip': 'video gone',
        'info_dict': {
            'id': '523629',
            'ext': 'mp4',
            'title': 'So kommen Sie bei Eis und Schnee sicher an',
            'description': 'md5:117c212f64b25e3d95747e5276863f7d',
            'thumbnail': r're:https?://.+\.jpg',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.20min.ch/videotv/?cid=44&vid=468738',
        'only_matching': True,
    }]
    _WEBPAGE_TESTS = [{
        'url': 'https://www.20min.ch/story/so-kommen-sie-bei-eis-und-schnee-sicher-an-557858045456',
        'skip': 'story URLs are extracted natively',
        'info_dict': {
            'id': '523629',
            'ext': 'mp4',
            'title': 'So kommen Sie bei Eis und Schnee sicher an',
            'description': 'md5:117c212f64b25e3d95747e5276863f7d',
        },
    }]

    def _find_unity_video(self, obj, depth=0):
        if not obj or depth > 20:
            return None
        if isinstance(obj, dict):
            if url_or_none(obj.get('url_high')) or (
                    obj.get('video_id') and url_or_none(obj.get('url_low') or obj.get('url_adaptive'))):
                return obj
            for value in obj.values():
                found = self._find_unity_video(value, depth + 1)
                if found:
                    return found
        elif isinstance(obj, (list, tuple)):
            for value in obj:
                found = self._find_unity_video(value, depth + 1)
                if found:
                    return found
        return None

    def _legacy_unity_id(self, video_id):
        slug = re.sub(r'[^a-z0-9]', '', video_id.lower())[:12]
        template = 'uv10xxxxxx'
        if not slug or len(slug) >= len(template):
            return None
        return template[:-len(slug)] + slug

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        legacy_id = mobj.group('id') or mobj.group('id2')
        video_id = mobj.group('id3') or mobj.group('id4') or legacy_id

        data = self._download_json(
            f'https://api.20min.ch/content/6/content/{video_id}',
            video_id, fatal=False)
        webpage = None
        video = self._find_unity_video(data)
        if not video:
            webpage = self._download_webpage(url, video_id)
            video = self._find_unity_video(
                self._search_nextjs_data(webpage, video_id, default={}))

        if not video and legacy_id:
            unity_id = self._legacy_unity_id(legacy_id)
            if unity_id:
                video = {
                    'video_id': unity_id,
                    'url_low': f'https://unityvideo.appuser.ch/video/{unity_id}.mp4',
                    'url_high': f'https://unityvideo.appuser.ch/video/{unity_id}h.mp4',
                    'url_adaptive': f'https://unityvideo.appuser.ch/video/{unity_id}/playlist.m3u8',
                    'thumbnail': f'https://unitythumb.appuser.ch/frames/{unity_id}/frame-1-{unity_id[2:]}.jpg',
                }

        if not video:
            raise ExtractorError('Unable to extract video', expected=True)

        formats = []
        for format_id, key, quality in (('sd', 'url_low', 0), ('hd', 'url_high', 1)):
            format_url = url_or_none(video.get(key))
            if format_url:
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'quality': quality,
                })
        for m3u8_id, key in (('hls', 'url_adaptive'), ('hls-crop', 'url_cropped_adaptive')):
            m3u8_url = url_or_none(video.get(key))
            if m3u8_url:
                formats.extend(self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', m3u8_id=m3u8_id, fatal=False) or [])

        title = video.get('title')
        if not title:
            if webpage is None:
                webpage = self._download_webpage(url, video_id, fatal=False) or ''
            title = self._og_search_title(webpage, default=video_id)

        description = video.get('lead')
        if isinstance(description, dict):
            description = description.get('text')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': url_or_none(video.get('thumbnail')),
            'duration': int_or_none(video.get('duration')),
            'timestamp': unified_timestamp(video.get('date')),
            'formats': formats,
        }
