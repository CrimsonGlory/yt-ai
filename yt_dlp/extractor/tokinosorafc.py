import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TokinoSoraFCIE(InfoExtractor):
    IE_NAME = 'tokinosora-fc'
    IE_DESC = 'ときのそらオフィシャルファンクラブ'
    _VALID_URL = r'https?://(?:www\.)?tokinosora-fc\.com/(?:video|live|audio)/(?P<id>sm\w+)'
    _WEBPAGE_BASE = 'https://tokinosora-fc.com'
    _API_BASE = 'https://api.tokinosora-fc.com/fc'
    _TESTS = [
        {
            'url': 'https://tokinosora-fc.com/video/smfffrGV2zykD3456gXWNvCg',
            'md5': '8e6579c837ccb1006158cfafa631c4b9',
            'info_dict': {
                'id': 'smfffrGV2zykD3456gXWNvCg',
                'ext': 'mp4',
                'title': '【一般販開始】ときのそら 6th Anniversary Party 「Keep Shininʼ」',
                'description': 'md5:6a0421b7c7f5a3b883c282cec1a81b9c',
                'channel': 'ときのそらオフィシャルファンクラブ',
                'channel_url': 'https://tokinosora-fc.com',
                'thumbnail': r're:https://cdn\.tokinosora-fc\.com/public_html/.+',
                'duration': 23,
                'timestamp': 1711155600,
                'upload_date': '20240323',
                'live_status': 'not_live',
                'view_count': int,
                'comment_count': int,
            },
        },
        {
            'url': 'https://tokinosora-fc.com/video/smcZ6Ezx4mQcgHAMRkHX4rMj',
            'only_matching': True,
        },
        {
            'url': 'https://tokinosora-fc.com/video/smYYioKjMmT8Fp6iUo7CmvfJ',
            'only_matching': True,
        },
        {
            'url': 'https://tokinosora-fc.com/live/smXZQEDmkrc8xPHtL5tmMS7D',
            'only_matching': True,
        },
    ]

    def _call_api(self, path, video_id, fanclub_site_id=None, fatal=True, **kwargs):
        headers = {
            'fc_use_device': 'null',
            'Origin': self._WEBPAGE_BASE,
            'Referer': f'{self._WEBPAGE_BASE}/',
            **(kwargs.pop('headers', None) or {}),
        }
        if fanclub_site_id is not None:
            headers['fc_site_id'] = str(fanclub_site_id)
        response = self._download_json(f'{self._API_BASE}/{path}', video_id, headers=headers, fatal=fatal, **kwargs)
        if not isinstance(response, dict):
            if fatal:
                raise ExtractorError('Unable to fetch API data', video_id=video_id)
            return {}
        if 'error' in response:
            if not fatal:
                return {}
            raise ExtractorError(f"API returned an error: {response['error']}", video_id=video_id, expected=True)
        return response.get('data') or {}

    def _get_fanclub_site_id(self, video_id):
        settings = self._download_json(
            f'{self._WEBPAGE_BASE}/site/settings.json',
            video_id,
            note='Downloading site settings',
            errnote='Unable to download site settings',
        )
        fanclub_id = traverse_obj(settings, ('fanclub_site_id', {int_or_none}))
        if not fanclub_id:
            raise ExtractorError('Unable to determine fanclub site id', video_id=video_id)
        return fanclub_id

    def _get_channel_name(self, fanclub_site_id, video_id):
        return traverse_obj(
            self._call_api(
                f'fanclub_sites/{fanclub_site_id}/page_base_info',
                video_id,
                fanclub_site_id=fanclub_site_id,
                fatal=False,
                note='Fetching channel info',
                errnote='Unable to fetch channel info',
            ),
            ('fanclub_site', 'fanclub_site_name', {str}),
        )

    def _get_age_limit(self, fanclub_site_id, video_id):
        return traverse_obj(
            self._call_api(
                f'fanclub_sites/{fanclub_site_id}/user_info',
                video_id,
                fanclub_site_id=fanclub_site_id,
                fatal=False,
                data=b'null',
                note='Fetching channel user info',
                errnote='Unable to fetch channel user info',
            ),
            ('fanclub_site', 'content_provider', 'age_limit', {int_or_none}),
        )

    def _real_extract(self, url):
        video_id = self._match_id(url)
        fanclub_site_id = self._get_fanclub_site_id(video_id)
        video_page = (
            self._call_api(
                f'video_pages/{video_id}',
                video_id,
                fanclub_site_id=fanclub_site_id,
                note='Fetching video page info',
                errnote='Unable to fetch video page info',
            ).get('video_page')
            or {}
        )

        live_status, session_payload = self._get_live_status(video_id, video_page)
        delivery_id = traverse_obj(video_page, ('video_delivery_target', 'id', {int_or_none}))
        formats = []
        if live_status != 'is_upcoming':
            formats = self._extract_media_formats(video_id, fanclub_site_id, video_page, session_payload, delivery_id)

        return {
            'id': video_id,
            'formats': formats,
            '_format_sort_fields': ('tbr', 'vcodec', 'acodec'),
            'channel': self._get_channel_name(fanclub_site_id, video_id),
            'channel_url': self._WEBPAGE_BASE,
            'age_limit': self._get_age_limit(fanclub_site_id, video_id),
            'live_status': live_status,
            'release_timestamp': unified_timestamp(video_page.get('live_scheduled_start_at')),
            **traverse_obj(
                video_page,
                {
                    'title': ('title', {str}),
                    'thumbnail': ('thumbnail_url', {url_or_none}),
                    'description': ('description', {str}),
                    'timestamp': ('released_at', {unified_timestamp}),
                    'duration': ('active_video_filename', 'length', {int_or_none}),
                    'comment_count': ('video_aggregate_info', 'number_of_comments', {int_or_none}),
                    'view_count': ('video_aggregate_info', 'total_views', {int_or_none}),
                    'tags': ('video_tags', ..., 'tag', {str}),
                },
            ),
            '__post_extractor': self.extract_comments(
                content_code=video_id,
                fanclub_site_id=fanclub_site_id,
                comment_group_id=traverse_obj(video_page, ('video_comment_setting', 'comment_group_id', {str})),
            ),
        }

    def _extract_media_formats(self, video_id, fanclub_site_id, video_page, session_payload, delivery_id):
        m3u8_url = traverse_obj(video_page, ('video_stream', 'authenticated_url', {url_or_none}))
        if m3u8_url:
            session_id = traverse_obj(
                self._call_api(
                    f'video_pages/{video_id}/session_ids',
                    f'{video_id}/session',
                    fanclub_site_id=fanclub_site_id,
                    fatal=False,
                    data=json.dumps(session_payload).encode(),
                    headers={'Content-Type': 'application/json'},
                    note='Getting session id',
                    errnote='Unable to get session id',
                ),
                ('session_id', {str}),
            )
            if not session_id:
                if delivery_id != 2:
                    self.raise_login_required('This content is only available for fan club members')
                raise ExtractorError('Unable to get session id', video_id=video_id, expected=True)
            return self._extract_m3u8_formats(m3u8_url.format(session_id=session_id), video_id, 'mp4', m3u8_id='hls')

        if delivery_id != 2:
            self.raise_login_required('This content is only available for fan club members')
        self.raise_no_formats('No media found', expected=True, video_id=video_id)
        return []

    def _get_live_status(self, video_id, video_page):
        video_type = video_page.get('type')
        live_finished_at = video_page.get('live_finished_at')
        payload = {}
        if video_type == 'vod':
            live_status = 'was_live' if live_finished_at else 'not_live'
        elif video_type == 'live':
            if not video_page.get('live_started_at'):
                start_at = video_page.get('live_scheduled_start_at')
                msg = f'This live event will begin at {start_at} UTC' if start_at else 'This event has not started yet'
                self.raise_no_formats(msg, expected=True, video_id=video_id)
                return 'is_upcoming', payload
            if not live_finished_at:
                live_status = 'is_live'
            else:
                live_status = 'was_live'
                payload = {'broadcast_type': 'dvr'}
                allow_dvr = traverse_obj(video_page, ('video', 'allow_dvr_flg'))
                convert_vod = traverse_obj(video_page, ('video', 'convert_to_vod_flg'))
                if not (allow_dvr and convert_vod):
                    raise ExtractorError(
                        'Live was ended, there is no video for download.', video_id=video_id, expected=True,
                    )
        else:
            raise ExtractorError(f'Unknown type: {video_type}', video_id=video_id)

        self.write_debug(f'{video_id}: video_type={video_type}, live_status={live_status}')
        return live_status, payload

    def _get_comments(self, content_code, fanclub_site_id, comment_group_id):
        if not comment_group_id:
            return
        item_id = f'{content_code}/comments'
        comment_access_token = traverse_obj(
            self._call_api(
                f'video_pages/{content_code}/comments_user_token',
                item_id,
                fanclub_site_id=fanclub_site_id,
                fatal=False,
                note='Getting comment token',
                errnote='Unable to get comment token',
            ),
            ('access_token', {str}),
        )
        if not comment_access_token:
            return

        comment_list = self._download_json(
            'https://comm-api.sheeta.com/messages.history',
            video_id=item_id,
            note='Fetching comments',
            errnote='Unable to fetch comments',
            fatal=False,
            headers={'Content-Type': 'application/json'},
            query={
                'sort_direction': 'asc',
                'limit': int_or_none(self._configuration_arg('max_comments', [''])[0]) or 120,
            },
            data=json.dumps(
                {
                    'token': comment_access_token,
                    'group_id': comment_group_id,
                },
            ).encode(),
        )
        for comment in traverse_obj(comment_list, ...):
            yield traverse_obj(
                comment,
                {
                    'author': ('nickname', {str}),
                    'author_id': ('sender_id', {str_or_none}),
                    'id': ('id', {str_or_none}),
                    'text': ('message', {str}),
                    'timestamp': (('updated_at', 'sent_at', 'created_at'), {unified_timestamp}),
                    'author_is_uploader': ('sender_id', {lambda x: x == '-1'}),
                },
                get_all=False,
            )
