from .common import InfoExtractor
from .youtube import YoutubeIE
from .zype import ZypeIE
from ..utils import (
    ExtractorError,
    unescapeHTML,
)


class FreespeechIE(InfoExtractor):
    IE_NAME = 'freespeech.org'
    _VALID_URL = r'https?://(?:www\.)?freespeech\.org/(?:live-tv|(?:stories|documentaries)/(?P<id>[^/?#]+))'
    _TESTS = [{
        'url': 'https://freespeech.org/documentaries/resisterhood/',
        'md5': 'bcc0d116048d2c582b80c586c8b14dac',
        'info_dict': {
            'id': '69a716297b58ab3fc0acdf41',
            'ext': 'mp4',
            'title': 'Resisterhood',
            'display_id': 'resisterhood-documentary',
            'description': 'md5:6ea0741842b84a793cc0254110a131f5',
            'thumbnail': r're:https?://.*\.jpe?g',
            'timestamp': 1773792000,
            'upload_date': '20260318',
            'duration': 5708,
            'view_count': int,
            'average_rating': int,
        },
        'add_ie': ['Zype'],
    }, {
        'url': 'http://www.freespeech.org/stories/fcc-announces-net-neutrality-rollback-whats-stake/',
        'skip': 'video gone',
        'info_dict': {
            'id': 'waRk6IPqyWM',
            'ext': 'mp4',
            'title': 'What\'s At Stake - Net Neutrality Special',
            'description': 'Presented by MNN and FSTV',
            'upload_date': '20170728',
            'uploader_id': 'freespeechtv',
            'uploader': 'freespeechtv',
        },
    }, {
        'url': 'https://freespeech.org/live-tv/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_valid_url(url).group('id') or 'live-tv'
        webpage = self._download_webpage(url, display_id, impersonate=True)

        zype_url = self._search_regex(
            r'((?:https?:)?//player\.zype\.com/embed/[\da-fA-F]+\.(?:js|json|html)\?[^"\'\s<>]+)',
            webpage, 'zype url', default=None)
        if zype_url:
            return self.url_result(self._proto_relative_url(unescapeHTML(zype_url)), ZypeIE)

        youtube_url = self._search_regex(
            r'data-video-url="([^"]+)"', webpage, 'youtube url', default=None)
        if not youtube_url:
            youtube_url = next(YoutubeIE._extract_embed_urls(url, webpage), None)
        if not youtube_url:
            raise ExtractorError('Unable to extract video embed', expected=True)
        return self.url_result(youtube_url, YoutubeIE)
