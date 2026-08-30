from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ForendorsIE(InfoExtractor):
    IE_NAME = 'forendors'
    IE_DESC = 'Forendors'
    _VALID_URL = r'https?://(?:www\.)?forendors\.cz/p/(?P<id>[0-9a-fA-F]+)'
    _API_BASE = 'https://api.forendors.cz'
    _API_HEADERS = {
        'Accept': 'application/json',
        'Origin': 'https://www.forendors.cz',
        'Referer': 'https://www.forendors.cz/',
    }
    _TESTS = [{
        'url': 'https://www.forendors.cz/p/733045644230530172',
        'md5': '1d555bfb22876d9437d924c654a4d47f',
        'info_dict': {
            'id': '733045644230530172',
            'ext': 'mp4',
            'title': 'Představujeme vám nový editor příspěvků!',
            'description': 'md5:1acbacd98f526d4599a30c073bb3d595',
            'thumbnail': 'https://pickey-prod.fra1.digitaloceanspaces.com/production/public/posts/68/2/image_670c0c0c80db92.97989983_d.jpg',
            'duration': 61,
            'timestamp': 1728842653,
            'upload_date': '20241013',
            'like_count': int,
            'comment_count': int,
            'uploader': 'Forendors',
            'uploader_id': 'forendors',
            'uploader_url': 'https://www.forendors.cz/forendors',
            'channel': 'Forendors',
            'channel_id': 'forendors',
            'channel_url': 'https://www.forendors.cz/forendors',
        },
    }, {
        # Public audio-only post
        'url': 'https://www.forendors.cz/p/978976916205871012',
        'only_matching': True,
    }, {
        'url': 'https://forendors.cz/p/733045644230530172',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        post = self._download_json(
            f'{self._API_BASE}/post/{video_id}', video_id, headers=self._API_HEADERS)

        if traverse_obj(post, 'is_accessible') is False:
            self.raise_login_required(
                'This post is only available to Forendors subscribers', method='cookies')

        media = traverse_obj(post, (
            'components', lambda _, v: (
                v.get('type') in ('video', 'audio')
                and v.get('has_media_processed', True)
                and v.get('detail_id')), {dict})) or []
        component = next((c for c in media if c.get('type') == 'video'), None) or traverse_obj(
            media, (0, {dict}))
        if not component:
            raise ExtractorError('This post has no video or audio', expected=True)

        detail_id = component['detail_id']
        playback = self._download_json(
            f'{self._API_BASE}/post/video/{detail_id}', video_id,
            'Downloading playback JSON', query={'type': 'url'},
            headers=self._API_HEADERS)
        playback_url = traverse_obj(playback, ('playback_url', {url_or_none}))
        if not playback_url:
            raise ExtractorError('No playback URL available', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            playback_url, video_id, 'm4a' if component.get('type') == 'audio' else 'mp4',
            m3u8_id='hls')

        handle = traverse_obj(post, ('author_info', 'handle', {str}))
        channel_url = f'https://www.forendors.cz/{handle}' if handle else None
        uploader = traverse_obj(post, ('author_info', 'name', {str}))

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': traverse_obj(post, ('title', {str})),
            'description': join_nonempty(*traverse_obj(post, (
                'components', lambda _, v: v.get('type') == 'text', 'text', {clean_html},
            )), delim='\n\n') or traverse_obj(post, (('perex', 'annotation'), {clean_html}, any)),
            'thumbnail': traverse_obj(component, (
                'cover', ('desktop', 'mobile'), {url_or_none}, any,
            )) or traverse_obj(post, ('author_info', 'avatars', 'social_avatar', {url_or_none})),
            'duration': traverse_obj(component, ('length', {int_or_none})),
            'timestamp': traverse_obj(post, ('published_at', {parse_iso8601})),
            'like_count': traverse_obj(post, ('likes_count', {int_or_none})),
            'comment_count': traverse_obj(post, ('comments_count', {int_or_none})),
            'uploader': uploader,
            'uploader_id': handle,
            'uploader_url': channel_url,
            'channel': uploader,
            'channel_id': handle or traverse_obj(post, ('author_info', 'id', {str_or_none})),
            'channel_url': channel_url,
        }
