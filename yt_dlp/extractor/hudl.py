import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    parse_qs,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class HudlIE(InfoExtractor):
    IE_NAME = 'hudl'
    IE_DESC = 'Hudl Fan / Hudl TV broadcasts'
    _VALID_URL = (
        r'https?://(?:www\.)?fan\.hudl\.com/(?:[^?#]*/)?watch\?(?:[^#]*&)?(?:ib|b)=(?P<id>[^&#]+)',
        r'https?://vcloud\.hudl\.com/broadcast/embed/(?P<id>\d+)',
    )
    _EMBED_REGEX = [r'<iframe[^>]+src=(["\'])(?P<url>https?://vcloud\.hudl\.com/broadcast/embed/\d+)\1']
    _GRAPHQL_URL = 'https://www.hudl.com/api/public/graphql/query'
    _GRAPHQL_QUERY = '''query Web_Fan_GetBroadcast_r1($broadcastId: ID, $internalBroadcastId: String) {
  broadcast(broadcastId: $broadcastId, internalBroadcastId: $internalBroadcastId) {
    available
    broadcastDateUtc
    broadcastId
    description
    downloadUrl
    duration
    hidden
    id
    internalId
    largeThumbnail
    liveDuration
    mediumThumbnail
    requireLogin
    siteSlug
    siteTitle
    smallThumbnail
    status
    title
  }
}'''
    _TESTS = [{
        'url': 'https://fan.hudl.com/_/_/_/organization/_/_/watch?b=QnJvYWRjYXN0ODc2ODA2',
        'md5': '739e5e7c476d274394d5c9e0d0c23a7f',
        'info_dict': {
            'id': '876806',
            'ext': 'mp4',
            'title': 'Girl\'s Basketball Top 5 | Week 5',
            'thumbnail': r're:https://d3erbgikz6mtmj\.cloudfront\.net/.+',
            'timestamp': 1704387900,
            'upload_date': '20240104',
            'channel': 'Hudl | Top Videos',
            'channel_id': 'hudltopvideos',
            'display_id': 'QnJvYWRjYXN0ODc2ODA2',
            'duration': 62.891,
            'live_status': 'was_live',
        },
    }, {
        'url': 'https://fan.hudl.com/_/_/_/organization/_/_/watch?ib=876806',
        'only_matching': True,
    }, {
        'url': 'https://vcloud.hudl.com/broadcast/embed/876806',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        query = parse_qs(url)
        graphql_id = traverse_obj(query, ('b', 0, {str}))
        internal_id = traverse_obj(query, ('ib', 0, {str}))
        url_id = self._match_id(url)
        if graphql_id and graphql_id.isdigit() and not internal_id:
            internal_id, graphql_id = graphql_id, None
        if not graphql_id and not internal_id:
            if url_id.isdigit():
                internal_id = url_id
            else:
                graphql_id = url_id

        display_id = graphql_id or internal_id
        data = self._download_json(
            self._GRAPHQL_URL, display_id, 'Downloading broadcast GraphQL JSON',
            data=json.dumps({
                'operationName': 'Web_Fan_GetBroadcast_r1',
                'query': self._GRAPHQL_QUERY,
                'variables': {
                    'broadcastId': graphql_id,
                    'internalBroadcastId': internal_id,
                },
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://fan.hudl.com',
                'Referer': 'https://fan.hudl.com/',
            })
        broadcast = traverse_obj(data, ('data', 'broadcast', {dict}))
        if not broadcast:
            raise ExtractorError(
                traverse_obj(data, ('errors', 0, 'message', {str})) or 'Broadcast not found',
                expected=True)

        video_id = traverse_obj(broadcast, ('internalId', {str})) or internal_id or display_id
        require_login = (traverse_obj(broadcast, ('requireLogin', {str})) or 'no').lower()
        if require_login not in ('no', 'false', '0'):
            self.raise_login_required('This Hudl broadcast requires a login or purchase')
        if broadcast.get('available') is False:
            raise ExtractorError('This broadcast is unavailable', expected=True)

        vmap = self._download_xml(
            f'https://vcloud.hudl.com/api/broadcast/vmap/{video_id}',
            video_id, 'Downloading broadcast VMAP', fatal=False)
        content = None if vmap is None else vmap.find('.//Content')
        stream_url = url_or_none((content.text or '').strip() if content is not None else None)
        if not stream_url:
            stream_url = f'https://vcloud.hudl.com/file/broadcast/{video_id}.m3u8?hfr=1'

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            stream_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
        download_url = traverse_obj(broadcast, ('downloadUrl', {url_or_none}))
        if download_url:
            formats.append({
                'url': download_url,
                'format_id': 'http',
                'quality': 1,
            })
        if not formats:
            self.raise_no_formats('No playable formats', expected=True, video_id=video_id)

        status = (traverse_obj(broadcast, ('status', {str})) or '').lower()
        duration = (
            traverse_obj(broadcast, ('duration', {int_or_none}, filter))
            or traverse_obj(broadcast, ('liveDuration', {int_or_none}, filter))
            or parse_duration(content.get('duration') if content is not None else None))

        return {
            'id': video_id,
            'display_id': traverse_obj(broadcast, ('id', {str})) or graphql_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': duration,
            'live_status': {
                'live': 'is_live',
                'archived': 'was_live',
                'upcoming': 'is_upcoming',
            }.get(status),
            **traverse_obj(broadcast, {
                'title': ('title', {str}),
                'description': ('description', {str}, filter),
                'thumbnail': (('largeThumbnail', 'mediumThumbnail', 'smallThumbnail'), {url_or_none}, any),
                'timestamp': ('broadcastDateUtc', {unified_timestamp}),
                'channel': ('siteTitle', {str}),
                'channel_id': ('siteSlug', {str}),
            }),
        }
