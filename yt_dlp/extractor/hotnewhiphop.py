from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import ExtractorError


class HotNewHipHopIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?hotnewhiphop\.com/(?:[^/?#]*\.)?(?P<id>\d+)(?:-[^/?#]+)?(?:\.html)?/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.hotnewhiphop.com/964555-kanye-west-comeback-hnhh-tv',
        'md5': '80df74f111a471584698322a011e4f3f',
        'info_dict': {
            'id': '80_XD4sYxfo',
            'ext': 'mp4',
            'title': 'Can Kanye West Make A Comeback?',
            'description': 'md5:916d632450ca23f23115ff3752057c84',
            'media_type': 'video',
            'uploader': 'HotNewHipHop',
            'uploader_id': '@HotNewHipHop',
            'uploader_url': 'https://www.youtube.com/@HotNewHipHop',
            'channel': 'HotNewHipHop',
            'channel_id': 'UCKaDN209nOLUabc-ftR_lng',
            'channel_url': 'https://www.youtube.com/channel/UCKaDN209nOLUabc-ftR_lng',
            'channel_is_verified': True,
            'channel_follower_count': int,
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'age_limit': 0,
            'duration': 509,
            'thumbnail': r're:https?://i\.ytimg\.com/vi/.+',
            'categories': ['Music'],
            'tags': 'count:24',
            'timestamp': 1765474699,
            'upload_date': '20251211',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
        ],
    }, {
        'url': 'http://www.hotnewhiphop.com/freddie-gibbs-lay-it-down-song.1435540.html',
        'skip': 'video gone',
        'md5': '2c2cd2f76ef11a9b3b581e8b232f3d96',
        'info_dict': {
            'id': '1435540',
            'ext': 'mp3',
            'title': 'Freddie Gibbs - Lay It Down',
        },
    }, {
        'url': 'https://www.hotnewhiphop.com/1007296-zilla-westside-gunn',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        youtube_id = self._search_regex(
            (r'<amp-youtube[^>]+\bdata-videoid=["\']([0-9A-Za-z_-]{11})',
             r'(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/)|youtu\.be/)([0-9A-Za-z_-]{11})'),
            webpage, 'youtube id', default=None)
        if not youtube_id:
            raise ExtractorError('No video found', expected=True)

        return self.url_result(
            f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id)
