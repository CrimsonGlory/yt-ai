from .common import InfoExtractor
from .youtube import YoutubeIE


class UnityIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = (
        r'https?://(?:www\.)?unity3d\.com/learn/tutorials/(?:[^/]+/)*(?P<id>[^/?#&]+)',
        r'https?://(?:www\.)?learn\.unity\.com/(?:course/[^/?#]+/)?tutorial/(?P<id>[^/?#&]+)',
    )
    _TESTS = [{
        'url': 'https://unity3d.com/learn/tutorials/tutorial/introduction-to-unity-studio',
        'md5': 'd79bc354eeb679b0054b2f4eb8a85b00',
        'info_dict': {
            'id': 'elSPChXnOhA',
            'ext': 'mp4',
            'title': 'Unity Studio – Getting Started: Introduction & First Project',
            'description': 'md5:3f0577bd1341a38cc17b16d4a25c81ea',
            'duration': 92,
            'uploader': 'Unity',
            'uploader_id': '@unity',
            'uploader_url': 'https://www.youtube.com/@unity',
            'channel': 'Unity',
            'channel_id': 'UCG08EqOAXJk_YXPDsAvReSg',
            'channel_url': 'https://www.youtube.com/channel/UCG08EqOAXJk_YXPDsAvReSg',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'age_limit': 0,
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Gaming'],
            'tags': ['Unity3d', 'Unity', 'Unity Technologies', 'Games', 'Game Development', 'Game Dev', 'Game Engine'],
            'timestamp': 1774377691,
            'upload_date': '20260324',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
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
        'url': 'https://unity3d.com/learn/tutorials/topics/animation/animate-anything-mecanim',
        'skip': 'video gone',
        'info_dict': {
            'id': 'jWuNtik0C8E',
            'ext': 'mp4',
            'title': 'Live Training 22nd September 2014 -  Animate Anything',
            'description': 'md5:e54913114bd45a554c56cdde7669636e',
            'duration': 2893,
            'uploader': 'Unity',
            'uploader_id': 'Unity3D',
            'upload_date': '20140926',
        },
    }, {
        'url': 'https://unity3d.com/learn/tutorials/projects/2d-ufo-tutorial/following-player-camera?playlist=25844',
        'only_matching': True,
    }, {
        'url': 'https://learn.unity.com/tutorial/introduction-to-unity-studio',
        'only_matching': True,
    }, {
        'url': 'https://learn.unity.com/course/get-started-with-unity-studio/tutorial/introduction-to-unity-studio',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        youtube_id = self._search_regex(
            (r'data-video-id="([_0-9A-Za-z-]+)"',
             r'(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/)|youtu\.be/)([0-9A-Za-z_-]{11})'),
            webpage, 'youtube ID')
        return self.url_result(
            f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id)
