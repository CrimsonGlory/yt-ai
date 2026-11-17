import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    make_archive_id,
    parse_iso8601,
    str_or_none,
    traverse_obj,
    url_or_none,
    urljoin,
)


class KhanAcademyBaseIE(InfoExtractor):
    _VALID_URL_TEMPL = r'https?://(?:www\.)?khanacademy\.org/(?P<id>(?:[^/]+/){%s}%s[^?#/&]+)'

    def _parse_video(self, video):
        return {
            '_type': 'url_transparent',
            'url': video['youtubeId'],
            'id': video['youtubeId'],
            'ie_key': 'Youtube',
            **traverse_obj(video, {
                'display_id': ('id', {str_or_none}),
                'title': ('translatedTitle', {str}),
                'thumbnail': ('thumbnailUrls', ..., 'url', {url_or_none}),
                'duration': ('duration', {int_or_none}),
                'description': ('description', {str}),
            }, get_all=False),
        }

    def _call_graphql(self, display_id, variables):
        if not hasattr(self, '_pcv'):
            self._pcv = traverse_obj(self._download_json(
                'https://www.khanacademy.org/_fastly/published-content-version/en',
                display_id, 'Downloading published content version', fatal=False),
                ('publishedContentVersion', {str}))
        query = {
            'fastly_cacheable': 'persist_until_publish',
            'hash': self._GRAPHQL_HASH,
            'variables': json.dumps(variables),
            'lang': 'en',
        }
        if self._pcv:
            query['pcv'] = self._pcv
        return self._download_json(
            f'https://www.khanacademy.org/api/internal/graphql/{self._GRAPHQL_OPERATION}',
            display_id, query=query)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        content = traverse_obj(self._call_graphql(display_id, {
            'path': display_id,
            'countryCode': 'US',
        }), ('data', 'contentRoute', ('listedPathData', 'unlistedPathData'), any))
        return self._parse_component_props(content, display_id)


class KhanAcademyIE(KhanAcademyBaseIE):
    IE_NAME = 'khanacademy'
    _VALID_URL = KhanAcademyBaseIE._VALID_URL_TEMPL % ('4', 'v/')
    _GRAPHQL_OPERATION = 'ContentRouteLessonAndContentData'
    _GRAPHQL_HASH = '183983073'
    _TEST = {
        'url': 'https://www.khanacademy.org/computing/computer-science/cryptography/crypt/v/one-time-pad',
        'md5': 'a23b02ebfe243e169c2b6121f65bea46',
        'info_dict': {
            'id': 'FlIG3TvQCBQ',
            'ext': 'mp4',
            'title': 'The one-time pad',
            'description': 'The perfect cipher',
            'display_id': '716378217',
            'duration': 176,
            'uploader': 'Khan Academy',
            'uploader_id': '@khanacademy',
            'uploader_url': 'https://www.youtube.com/@khanacademy',
            'upload_date': '20120411',
            'timestamp': 1334170113,
            'license': 'cc-by-nc-sa',
            'live_status': 'not_live',
            'channel': 'Khan Academy',
            'channel_id': 'UC4a-Gbdw7vOaccHmFo40b9g',
            'channel_url': 'https://www.youtube.com/channel/UC4a-Gbdw7vOaccHmFo40b9g',
            'channel_is_verified': True,
            'playable_in_embed': True,
            'categories': ['Education'],
            'creators': ['Brit Cruise'],
            'tags': [],
            'age_limit': 0,
            'availability': 'public',
            'comment_count': int,
            'channel_follower_count': int,
            'thumbnail': str,
            'view_count': int,
            'like_count': int,
            'heatmap': list,
            'media_type': 'video',
        },
        'add_ie': ['Youtube'],
        'skip': "YouTube bot-check from this environment: Sign in to confirm you're not a bot (cookies required)",
    }

    def _parse_component_props(self, component_props, display_id):
        video = component_props['content']
        return {
            **self._parse_video(video),
            **traverse_obj(video, {
                'creators': ('authorNames', ..., {str}),
                'timestamp': ('dateAdded', {parse_iso8601}),
                'license': ('kaUserLicense', {str}),
            }),
        }


class KhanAcademyUnitIE(KhanAcademyBaseIE):
    IE_NAME = 'khanacademy:unit'
    _VALID_URL = (KhanAcademyBaseIE._VALID_URL_TEMPL % ('1,2', '')) + '/?(?:[?#&]|$)'
    _GRAPHQL_OPERATION = 'FetchContentData'
    _GRAPHQL_HASH = '416280634'
    _TESTS = [{
        'url': 'https://www.khanacademy.org/computing/computer-science/cryptography',
        'info_dict': {
            'id': 'x48c910b6',
            'title': 'Cryptography',
            'description': 'How have humans protected their secret messages through history? What has changed today?',
            'display_id': 'computing/computer-science/cryptography',
            '_old_archive_ids': ['khanacademyunit cryptography'],
        },
        'playlist_mincount': 31,
    }, {
        'url': 'https://www.khanacademy.org/computing/computer-science',
        'info_dict': {
            'id': 'x301707a0',
            'title': 'Computer science theory',
            'description': 'md5:20a0c2d331e5d0e609872629079e6ec8',
            'display_id': 'computing/computer-science',
            '_old_archive_ids': ['khanacademyunit computer-science'],
        },
        'playlist_mincount': 50,
    }]

    def _fetch_curation(self, path, display_id):
        content_json = traverse_obj(self._call_graphql(display_id, {
            'path': path.lstrip('/'),
            'queryParams': '',
            'countryCode': 'US',
        }), ('data', 'contentJson', {str}))
        if not content_json:
            return {}
        return traverse_obj(json.loads(content_json), ('componentProps', 'curation', {dict})) or {}

    def _video_entries(self, curation):
        for item in traverse_obj(curation, (
            'tabs', ..., 'modules', ..., 'tutorials', ..., 'contentItems',
            lambda _, v: v.get('kind') == 'Video' and v.get('nodeUrl'),
        )):
            yield self.url_result(
                urljoin('https://www.khanacademy.org', item['nodeUrl']),
                KhanAcademyIE, title=item.get('title'))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        curation = self._fetch_curation(display_id, display_id)
        entries = list(self._video_entries(curation))
        for path in traverse_obj(curation, (
            'tabs', ..., 'modules', ..., 'modules',
            lambda _, v: v.get('kind') == 'SubjectPageTopicCard',
            'url', {str},
        )):
            entries.extend(self._video_entries(
                self._fetch_curation(path, display_id)))

        slug = display_id.rsplit('/', 1)[-1]
        return self.playlist_result(
            entries,
            display_id=display_id,
            id=curation.get('unitId') or curation.get('courseId'),
            title=curation.get('title'),
            description=curation.get('description'),
            _old_archive_ids=[make_archive_id(self, slug)] if slug else None,
        )
