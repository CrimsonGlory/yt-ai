import functools
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    extract_attributes,
    get_element_html_by_id,
    int_or_none,
    parse_iso8601,
    url_or_none,
    urlencode_postdata,
)
from ..utils.traversal import traverse_obj


class MurrtubeIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                        (?:
                            murrtube:|
                            https?://murrtube\.net/(?:v/|videos/(?P<slug>[a-z0-9-]+?)-)
                        )
                        (?P<id>[A-Z0-9]{4}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})
                    '''
    _TESTS = [{
        'url': 'https://murrtube.net/videos/inferno-x-skyler-148b6f2a-fdcc-4902-affe-9c0f41aaaca0',
        'md5': '99c6c5e0a8b1414cf4f52042b6166827',
        'info_dict': {
            'id': '148b6f2a-fdcc-4902-affe-9c0f41aaaca0',
            'ext': 'mp4',
            'title': 'Inferno X Skyler',
            'description': 'Humping a very good slutty sheppy (roomate)',
            'uploader': 'Inferno Wolf',
            'uploader_id': 'inferno-wolf',
            'age_limit': 18,
            'thumbnail': r're:https://storage\.murrtube\.net/.+',
            'duration': 284,
            'timestamp': 1588431972,
            'upload_date': '20200502',
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'tags': list,
        },
        # CMAF HLS --test only fetches the fMP4 init fragment (~1KB)
        'file_minsize': None,
    }, {
        'url': 'https://murrtube.net/v/0J2Q',
        'md5': '174fe9d6c9e664fdb042e85d0dbffc49',
        'info_dict': {
            'id': 'fcfd303b-0002-4da9-9a9f-bef8ce4c0f0d',
            'ext': 'mp4',
            'uploader': 'Hayel',
            'uploader_id': 'hayel',
            'title': 'Who\'s in charge now?',
            'description': 'md5:cede015b6b02805b002766e5dea328da',
            'age_limit': 18,
            'thumbnail': r're:https://storage\.murrtube\.net/.+',
            'duration': 331,
            'timestamp': 1653039644,
            'upload_date': '20220520',
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'tags': list,
        },
        'file_minsize': None,
    }]

    def _real_initialize(self):
        homepage = self._download_webpage(
            'https://murrtube.net', None, note='Getting session token')
        self._request_webpage(
            'https://murrtube.net/accept_age_check', None, 'Setting age cookie',
            data=urlencode_postdata(self._hidden_inputs(homepage)))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        medium = traverse_obj(
            get_element_html_by_id('app', webpage),
            ({extract_attributes}, 'data-page', {json.loads}, 'props', 'medium'))
        if not medium:
            raise ExtractorError('Unable to extract video data')

        video_id = medium.get('id') or display_id
        hls_url = traverse_obj(medium, ('hls_url', {url_or_none}))
        if not hls_url:
            raise ExtractorError('Unable to extract HLS URL', expected=True)

        return {
            'id': video_id,
            'age_limit': 18,
            'formats': self._extract_m3u8_formats(hls_url, video_id, 'mp4'),
            **traverse_obj(medium, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('thumbnail_url', {url_or_none}),
                'uploader': ('user', 'name', {str}),
                'uploader_id': ('user', 'slug', {str}),
                'duration': ('duration', {int_or_none}),
                'view_count': ('views_count', {int_or_none}),
                'like_count': ('likes_count', {int_or_none}),
                'comment_count': ('comments_count', {int_or_none}),
                'timestamp': ('published_at', {parse_iso8601}),
                'tags': ('tags', ..., 'name', {str}),
            }),
        }


class MurrtubeUserIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'Murrtube user profile'
    _VALID_URL = r'https?://murrtube\.net/(?P<id>[^/]+)$'
    _TESTS = [{
        'url': 'https://murrtube.net/stormy',
        'skip': 'video gone',
        'info_dict': {
            'id': 'stormy',
        },
        'playlist_mincount': 27,
    }]
    _PAGE_SIZE = 10

    def _download_gql(self, video_id, op, note=None, fatal=True):
        result = self._download_json(
            'https://murrtube.net/graphql',
            video_id, note, data=json.dumps(op).encode(), fatal=fatal,
            headers={'Content-Type': 'application/json'})
        return result['data']

    def _fetch_page(self, username, user_id, page):
        data = self._download_gql(username, {
            'operationName': 'Media',
            'variables': {
                'limit': self._PAGE_SIZE,
                'offset': page * self._PAGE_SIZE,
                'sort': 'latest',
                'userId': user_id,
            },
            'query': '''\
query Media($q: String, $sort: String, $userId: ID, $offset: Int!, $limit: Int!) {
  media(q: $q, sort: $sort, userId: $userId, offset: $offset, limit: $limit) {
    id
    __typename
  }
}'''},
            f'Downloading page {page + 1}')
        if data is None:
            raise ExtractorError(f'Failed to retrieve video list for page {page + 1}')

        media = data['media']

        for entry in media:
            yield self.url_result('murrtube:{}'.format(entry['id']), MurrtubeIE.ie_key())

    def _real_extract(self, url):
        username = self._match_id(url)
        data = self._download_gql(username, {
            'operationName': 'User',
            'variables': {
                'id': username,
            },
            'query': '''\
query User($id: ID!) {
  user(id: $id) {
    id
    __typename
  }
}'''},
            'Downloading user info')
        if data is None:
            raise ExtractorError('Failed to fetch user info')

        user = data['user']

        entries = OnDemandPagedList(functools.partial(
            self._fetch_page, username, user.get('id')), self._PAGE_SIZE)

        return self.playlist_result(entries, username)
