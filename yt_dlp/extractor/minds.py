from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    format_field,
    int_or_none,
    str_or_none,
    strip_or_none,
)


class MindsBaseIE(InfoExtractor):
    _VALID_URL_BASE = r'https?://(?:www\.)?minds\.com/'

    def _call_api(self, path, video_id, resource, query=None, **kwargs):
        api_url = 'https://www.minds.com/api/' + path
        token = self._get_cookies(api_url).get('XSRF-TOKEN')
        return self._download_json(
            api_url, video_id, f'Downloading {resource} JSON metadata', headers={
                'Referer': 'https://www.minds.com/',
                'X-XSRF-TOKEN': token.value if token else '',
            }, query=query, **kwargs)

    def _fetch_entity(self, entity_id, urn_type='activity'):
        data = self._call_api(
            'v2/entities/', entity_id, 'entity', query={
                'urns': f'urn:{urn_type}:{entity_id}',
                'as_activities': '0',
            })
        entities = data.get('entities') if isinstance(data, dict) else None
        return entities[0] if entities else None


class MindsIE(MindsBaseIE):
    IE_NAME = 'minds'
    _VALID_URL = MindsBaseIE._VALID_URL_BASE + r'(?:media|newsfeed|archive/view)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.minds.com/media/100000000000086822',
        'md5': '564fde8f0b5c4ed3596ea7e026748648',
        'info_dict': {
            'id': '100000000000086822',
            'ext': 'mp4',
            'title': 'Minds intro sequence',
            'thumbnail': r're:https?://.+\.png',
            'uploader_id': 'ottman',
            'upload_date': '20130524',
            'timestamp': 1369404826,
            'uploader': 'Bill Ottman',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': ['animation'],
            'comment_count': int,
            'license': 'attribution-cc',
            'uploader_url': 'https://www.minds.com/ottman',
        },
    }, {
        # entity.type == 'activity' and empty title
        'url': 'https://www.minds.com/newsfeed/798025111988506624',
        'md5': '35b6ed189d60a96cf8c067d15114a9ea',
        'info_dict': {
            'id': '798022190320226304',
            'ext': 'mp4',
            'title': '798022190320226304',
            'uploader': 'ColinFlaherty',
            'upload_date': '20180111',
            'timestamp': 1515639316,
            'uploader_id': 'ColinFlaherty',
            'uploader_url': 'https://www.minds.com/ColinFlaherty',
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'thumbnail': r're:https?://.+\.png',
        },
    }, {
        'url': 'https://www.minds.com/archive/view/715172106794442752',
        'only_matching': True,
    }, {
        # youtube perma_url
        'url': 'https://www.minds.com/newsfeed/1197131838022602752',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        entity_id = self._match_id(url)
        entity = self._fetch_entity(entity_id)
        if not entity:
            raise ExtractorError('Unable to fetch entity metadata', expected=True)

        if entity.get('type') == 'activity':
            if entity.get('custom_type') == 'video':
                custom_data = entity.get('custom_data')
                video_id = str_or_none(
                    custom_data.get('guid') if isinstance(custom_data, dict) else None,
                ) or str_or_none(entity.get('entity_guid')) or entity_id
                if video_id != entity_id:
                    video_entity = self._fetch_entity(video_id, 'video') or self._fetch_entity(video_id)
                    if video_entity:
                        entity = video_entity
            else:
                return self.url_result(entity['perma_url'])
        else:
            video_id = entity_id

        # v2/media/video is login-gated; public downloads use this redirect
        formats = [{
            'format_id': 'source',
            'url': f'https://www.minds.com/api/v3/media/video/download/{video_id}',
            'ext': 'mp4',
        }]

        owner = entity.get('ownerObj') or {}
        uploader_id = owner.get('username')

        tags = entity.get('tags')
        if tags and isinstance(tags, str):
            tags = [tags]

        thumbnail = None
        poster = entity.get('thumbnail_src')
        if poster:
            urlh = self._request_webpage(poster, video_id, fatal=False)
            if urlh:
                thumbnail = urlh.url

        return {
            'id': video_id,
            'title': entity.get('title') or video_id,
            'formats': formats,
            'description': clean_html(entity.get('description')) or None,
            'license': str_or_none(entity.get('license') or None),
            'timestamp': int_or_none(entity.get('time_created')),
            'uploader': strip_or_none(owner.get('name')),
            'uploader_id': uploader_id,
            'uploader_url': format_field(uploader_id, None, 'https://www.minds.com/%s'),
            'view_count': int_or_none(entity.get('play:count')),
            'like_count': int_or_none(entity.get('thumbs:up:count')),
            'dislike_count': int_or_none(entity.get('thumbs:down:count')),
            'tags': tags,
            'comment_count': int_or_none(entity.get('comments:count')),
            'thumbnail': thumbnail,
        }


class MindsFeedBaseIE(MindsBaseIE):
    _PAGE_SIZE = 150

    def _entries(self, feed_id):
        query = {'limit': self._PAGE_SIZE, 'sync': 1}
        i = 1
        while True:
            data = self._call_api(
                f'v2/feeds/container/{feed_id}/videos',
                feed_id, f'page {i}', query)
            entities = data.get('entities') or []
            for entity in entities:
                guid = entity.get('guid')
                if not guid:
                    continue
                yield self.url_result(
                    'https://www.minds.com/newsfeed/' + guid,
                    MindsIE.ie_key(), guid)
            query['from_timestamp'] = data['load-next']
            if not (query['from_timestamp'] and len(entities) == self._PAGE_SIZE):
                break
            i += 1

    def _real_extract(self, url):
        feed_id = self._match_id(url)
        feed = self._call_api(
            f'v1/{self._FEED_PATH}/{feed_id}',
            feed_id, self._FEED_TYPE)[self._FEED_TYPE]

        return self.playlist_result(
            self._entries(feed['guid']), feed_id,
            strip_or_none(feed.get('name')),
            strip_or_none(feed.get('briefdescription')))


class MindsChannelIE(MindsFeedBaseIE):
    _FEED_TYPE = 'channel'
    IE_NAME = 'minds:' + _FEED_TYPE
    _VALID_URL = MindsBaseIE._VALID_URL_BASE + r'(?!(?:newsfeed|media|api|archive|groups)/)(?P<id>[^/?&#]+)'
    _FEED_PATH = 'channel'
    _TEST = {
        'url': 'https://www.minds.com/ottman',
        'info_dict': {
            'id': 'ottman',
            'title': 'Bill Ottman',
            'description': 'Co-creator & CEO @minds',
        },
        'playlist_mincount': 54,
    }


class MindsGroupIE(MindsFeedBaseIE):
    _FEED_TYPE = 'group'
    IE_NAME = 'minds:' + _FEED_TYPE
    _VALID_URL = MindsBaseIE._VALID_URL_BASE + r'groups/profile/(?P<id>[0-9]+)'
    _FEED_PATH = 'groups/group'
    _TEST = {
        'url': 'https://www.minds.com/groups/profile/785582576369672204/feed/videos',
        'info_dict': {
            'id': '785582576369672204',
            'title': 'Cooking Videos',
            'description': str,
        },
        'playlist_mincount': 1,
    }
