from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ProjectVeritasIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?projectveritas\.com/(?P<type>news|video)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.projectveritas.com/news/exclusive-inside-the-new-york-and-new-jersey-hospitals-battling-coronavirus/',
        'md5': 'c85ddbec51777dd8cc8d239dcd5fd511',
        'info_dict': {
            'id': '4jzp1CPGIrGiyUD06mFWP7',
            'ext': 'mp4',
            'title': 'Inside New York and New Jersey Hospitals',
            'thumbnail': r're:https?://images\.ctfassets\.net/.+',
            'timestamp': 1585347794,
            'upload_date': '20200327',
        },
    }, {
        'url': 'https://www.projectveritas.com/video/ilhan-omar-connected-ballot-harvester-in-cash-for-ballots-scheme-car-is-full/',
        'skip': 'video gone',
        'info_dict': {
            'id': 'c5aab304-a56b-54b1-9f0b-03b77bc5f2f6',
            'ext': 'mp4',
            'title': 'Ilhan Omar connected Ballot Harvester in cash-for-ballots scheme: "Car is full" of absentee ballots',
            'upload_date': '20200927',
            'thumbnail': 'md5:194b8edf0e2ba64f25500ff4378369a4',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video = traverse_obj(self._search_nextjs_v13_data(webpage, display_id), (
            ..., 'video', {dict}, any))
        playback_id = traverse_obj(video, ('muxAsset', 'playbackId', {str}))
        if not playback_id:
            raise ExtractorError('No video on the provided url.', expected=True)
        video_id = traverse_obj(video, ('sys', 'id', {str})) or display_id
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'https://stream.mux.com/{playback_id}.m3u8', video_id, 'mp4')
        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'timestamp': traverse_obj(
                video, ('muxAsset', 'created_at', {int_or_none}),
                ('image', 'sys', 'firstPublishedAt', {parse_iso8601})),
            **traverse_obj(video, {
                'title': ('title', {str}),
                'thumbnail': ('image', 'url', {url_or_none}),
                'duration': ('muxAsset', 'duration', {float_or_none}),
            }),
        }
