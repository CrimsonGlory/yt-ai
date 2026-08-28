import json
import re

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import ExtractorError, url_or_none
from ..utils.traversal import require, traverse_obj


class NetAppBaseIE(InfoExtractor):
    _COVEO_ORG = 'netappproductiono5s3vzkp'
    _COVEO_SEARCH_HUB = 'Marketing Prod Stardust Search Hub'

    def _youtube_result(self, youtube_id, **kwargs):
        return self.url_result(
            f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id,
            url_transparent=True, **kwargs)


class NetAppVideoIE(NetAppBaseIE):
    _VALID_URL = (
        r'https?://(?:media\.netapp\.com/video-detail|(?:www\.)?netapp\.com/(?:[a-z]{2}(?:-[a-z]+)?/)?video)/'
        r'(?P<id>(?!collections(?:/|$))(?:[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}|[\w-]{11}))')
    _TESTS = [{
        'url': 'https://www.netapp.com/video/EdwQT_bxVcc/seamless-storage-for-modern-kubernetes-deployments/',
        'md5': 'a0f19fa81d8e6dd63de2f2f51a79bf71',
        'info_dict': {
            'id': 'EdwQT_bxVcc',
            'ext': 'mp4',
            'title': 'Seamless storage for modern Kubernetes deployments',
            'description': 'md5:054e859c9f4b71f144c8075c4a152dc4',
            'duration': 2159,
            'uploader': 'NetApp',
            'uploader_id': '@netapp',
            'uploader_url': 'https://www.youtube.com/@netapp',
            'channel': 'NetApp',
            'channel_id': 'UCraITOUxo4l3oYQBH8fofyw',
            'channel_url': 'https://www.youtube.com/channel/UCraITOUxo4l3oYQBH8fofyw',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'view_count': int,
            'categories': ['Science & Technology'],
            'tags': 'count:16',
            'thumbnail': r're:https://i\.ytimg\.com/vi/EdwQT_bxVcc/.+',
            'timestamp': 1762353779,
            'upload_date': '20251105',
            'availability': 'unlisted',
            'live_status': 'not_live',
            'playable_in_embed': True,
            'age_limit': 0,
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
        'url': 'https://media.netapp.com/video-detail/da25fc01-82ad-5284-95bc-26920200a222/seamless-storage-for-modern-kubernetes-deployments',
        'only_matching': True,
    }, {
        'url': 'https://www.netapp.com/de/video/EdwQT_bxVcc/seamless-storage-for-modern-kubernetes-deployments/',
        'only_matching': True,
    }, {
        'url': 'https://media.netapp.com/video-detail/45593e5d-cf1c-5996-978c-c9081906e69f/unleash-ai-innovation-with-your-data-with-the-netapp-platform',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if len(video_id) == 11:
            return self._youtube_result(video_id)

        webpage = self._download_webpage(url, video_id, impersonate=True)
        youtube_url = next(YoutubeIE._extract_embed_urls(url, webpage), None)
        if not youtube_url:
            youtube_id = self._search_regex(
                r'(?:youtube\.com/embed/|youtube\.com/watch\?v=)([\w-]{11})',
                webpage, 'youtube id', default=None)
            if youtube_id:
                youtube_url = f'https://www.youtube.com/watch?v={youtube_id}'
        if not youtube_url:
            raise ExtractorError('Unable to extract YouTube embed', expected=True)
        return self.url_result(youtube_url, YoutubeIE, url_transparent=True)


class NetAppCollectionIE(NetAppBaseIE):
    _VALID_URL = (
        r'https?://(?:media\.netapp\.com/collection|(?:www\.)?netapp\.com/(?:[a-z]{2}(?:-[a-z]+)?/)?video/collections)'
        r'/(?P<id>[^/?#]+)')
    _TESTS = [{
        'url': 'https://www.netapp.com/video/collections/ai-and-analytics/',
        'info_dict': {
            'id': 'ai-and-analytics',
            'title': 'AI and analytics',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://media.netapp.com/collection/9820e190-f2a6-47ac-9c0a-98e5e64234a4',
        'info_dict': {
            'title': 'Featured sessions',
            'id': '9820e190-f2a6-47ac-9c0a-98e5e64234a4',
        },
        'playlist_count': 4,
        'skip': 'Brightcove collection API is gone',
    }]

    def _real_extract(self, url):
        collection_id = self._match_id(url)
        if re.fullmatch(r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}', collection_id):
            raise ExtractorError(
                'This Brightcove collection URL is no longer available', expected=True)

        webpage = self._download_webpage(url, collection_id, impersonate=True)
        title = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage)

        token = traverse_obj(
            self._download_json(
                'https://www.netapp.com/api/coveo-token', collection_id,
                note='Downloading Coveo token', impersonate=True),
            ('token', {str}, {require('Coveo token')}))
        escaped_title = (title or collection_id).replace('\\', '\\\\').replace('"', '\\"')
        results = self._download_json(
            f'https://{self._COVEO_ORG}.org.coveo.com/rest/search/v2',
            collection_id, note='Downloading collection results',
            data=json.dumps({
                'q': '',
                'aq': f'@ogtype=="Media" AND @facet_mediacollection_label_mktg=="{escaped_title}"',
                'numberOfResults': 100,
                'searchHub': self._COVEO_SEARCH_HUB,
            }).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            })

        entries = []
        for video_url in traverse_obj(results, ('results', ..., 'clickUri', {url_or_none})):
            if NetAppVideoIE.suitable(video_url):
                entries.append(self.url_result(video_url, NetAppVideoIE))
        return self.playlist_result(entries, collection_id, title)
