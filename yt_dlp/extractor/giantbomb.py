from .common import InfoExtractor
from .jwplatform import JWPlatformIE
from ..utils import (
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class GiantBombIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?giantbomb\.com/(?:videos|shows)/'
        r'(?!random(?:[/?#]|$))(?P<id>[^?#]+?)(?:/(?P<legacy_id>\d+-\d+))?/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://giantbomb.com/videos/non-subscriber-video',
        'md5': 'f6ab1bce3f3450c214dddd3d3478ed0e',
        'info_dict': {
            'id': 'qIsgFXX7',
            'ext': 'mp4',
            'title': 'NON SUBSCRIBER VIDEO',
            'description': 'This video shows for non-members during paid events.',
            'display_id': 'non-subscriber-video',
            'duration': 29.0,
            'thumbnail': 'https://cdn.jwplayer.com/v2/media/qIsgFXX7/poster.jpg?width=720',
            'timestamp': 1086099480,
            'upload_date': '20040601',
        },
        'params': {
            # Prefer progressive MP4 so the live test is not HLS-only
            'format': 'best[protocol=https][ext=mp4]/best',
        },
    }, {
        'url': 'http://www.giantbomb.com/videos/quick-look-destiny-the-dark-below/2300-9782/',
        'skip': '404',
        'md5': '132f5a803e7e0ab0e274d84bda1e77ae',
        'info_dict': {
            'id': '2300-9782',
            'display_id': 'quick-look-destiny-the-dark-below',
            'ext': 'mp4',
            'title': 'Quick Look: Destiny: The Dark Below',
            'description': 'md5:0aa3aaf2772a41b91d44c63f30dfad24',
            'duration': 2399,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.giantbomb.com/shows/ben-stranding/2970-20212',
        'only_matching': True,
    }, {
        'url': 'https://giantbomb.com/videos/quick-looks/blood-dungeon',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        slug = self._match_id(url).strip('/')

        video = traverse_obj(self._download_json(
            'https://giantbomb.com/api/videos', slug,
            query={'where[slug][equals]': slug, 'limit': '1'},
            impersonate=True), ('docs', 0, {dict}))

        if not video:
            webpage = self._download_webpage(url, slug, impersonate=True)
            video_id = self._search_regex(r'videoId\\?":(\d+)', webpage, 'video id')
            video = self._download_json(
                f'https://giantbomb.com/api/videos/{video_id}', video_id,
                impersonate=True)

        info = {
            'display_id': slug,
            **traverse_obj(video, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'timestamp': (('publishedAt', 'publishDate'), {parse_iso8601}, any),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
            }),
        }

        jw_id = traverse_obj(video, ('jwMediaIdFree', {str}, filter))
        if jw_id:
            return self.url_result(
                f'jwplatform:{jw_id}', ie=JWPlatformIE, video_id=jw_id,
                url_transparent=True, **info)

        youtube_url = traverse_obj(video, ('youtubeUrl', {url_or_none}))
        if youtube_url:
            return self.url_result(
                youtube_url, ie='Youtube', url_transparent=True, **info)

        self.raise_login_required(
            'This video is only available for Giant Bomb Premium subscribers')
