from .common import InfoExtractor
from ..utils import (
    int_or_none,
    try_get,
)
from ..utils.traversal import traverse_obj


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
        'url': 'http://www.20min.ch/story/live-interview-herr-blocher-was-verdienen-sie-wenn-russland-sanktionen-fallen-103621700',
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
        # FIXME: Update _VALID_URL
        'url': 'https://www.20min.ch/story/so-kommen-sie-bei-eis-und-schnee-sicher-an-557858045456',
        'info_dict': {
            'id': '523629',
            'ext': 'mp4',
            'title': 'So kommen Sie bei Eis und Schnee sicher an',
            'description': 'md5:117c212f64b25e3d95747e5276863f7d',
        },
    }]

    def _real_extract(self, url):
        m = self._match_valid_url(url)
        video_id = m.group('id') or m.group('id2') or m.group('id3') or m.group('id4')

        video = {}
        api = self._download_json(
            f'https://api.20min.ch/video/{video_id}/show',
            video_id, fatal=False)
        if isinstance(api, dict):
            video = api.get('content') or api

        webpage = None
        if not video.get('title'):
            webpage = self._download_webpage(url, video_id)
            nextjs = self._search_nextjs_data(webpage, video_id, default={})
            video = video or traverse_obj(nextjs, ('props', 'pageProps', 'content')) or {}
            if not video:
                video = {
                    'title': self._og_search_title(webpage, default=video_id),
                    'lead': self._og_search_description(webpage),
                    'thumbnail': self._og_search_thumbnail(webpage),
                }

        title = video.get('title') or video_id

        formats = []
        for quality, (format_id, p) in enumerate([('sd', ''), ('hd', 'h')]):
            formats.append({
                'format_id': format_id,
                'url': f'https://podcast.20min-tv.ch/podcast/20min/{video_id}{p}.mp4',
                'quality': quality,
            })
        if webpage is None:
            webpage = self._download_webpage(url, video_id, fatal=False) or ''
        og_video = self._og_search_video_url(webpage, default=None) if webpage else None
        if og_video:
            formats.append({'url': og_video, 'quality': 2})
        m3u8_url = self._search_regex(
            r'(https?://[^"\']+\.m3u8[^"\']*)', webpage or '', 'm3u8', default=None)
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False) or [])

        description = video.get('lead')
        thumbnail = video.get('thumbnail')

        def extract_count(kind):
            return try_get(
                video,
                lambda x: int_or_none(x['communityobject'][f'thumbs_{kind}']))

        like_count = extract_count('up')
        dislike_count = extract_count('down')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }
