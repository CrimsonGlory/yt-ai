import base64
import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    update_url_query,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class OnePlus1VideoIE(InfoExtractor):
    IE_NAME = '1plus1.video'
    IE_DESC = '1+1 video'
    _VALID_URL = r'https?://(?:www\.)?1plus1\.video/(?:(?:ru|ua)/)?video/(?:embed|card)/(?P<id>[\w-]+)'
    _EMBED_REGEX = [rf'<iframe[^>]+\b(?:data-)?src=(["\'])(?P<url>{_VALID_URL}.*?)\1']
    _TESTS = [{
        'url': 'https://1plus1.video/video/embed/4ROYeBLt',
        'md5': '890c5c6c4815f1faf33c7f67a545fc24',
        'info_dict': {
            'id': '4ROYeBLt',
            'ext': 'mp4',
            'title': 'У Стокгольмі звільнили росіянку, яка образила українку',
            'thumbnail': 'https://images.1plus1.video/card-5/4ROYeBLt/preview.jpg',
            'duration': 234,
            'timestamp': 1651044708,
            'upload_date': '20220427',
            'view_count': int,
        },
    }, {
        'url': 'https://1plus1.video/video/card/4ROYeBLt',
        'only_matching': True,
    }, {
        'url': 'https://1plus1.video/ru/video/embed/4ROYeBLt',
        'only_matching': True,
    }, {
        'url': 'https://1plus1.video/video/embed/4ROYeBLt?autoplay=0&tl=0&l=ua',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if re.search(r'/video/embed/', url):
            webpage = self._download_webpage(url, video_id)
        else:
            webpage = self._download_webpage(
                f'https://1plus1.video/video/embed/{video_id}', video_id)

        player_b64 = self._search_regex(
            r'new\s+OVVA\s*\(\s*["\'][^"\']+["\']\s*,\s*["\'](?P<b64>[A-Za-z0-9+/=]+)["\']',
            webpage, 'OVVA player data', group='b64')
        player = self._parse_json(
            base64.b64decode(player_b64).decode(), video_id)

        balancer = traverse_obj(player, ('balancer', {url_or_none}))
        if not balancer:
            self.raise_no_formats('No balancer URL in OVVA player data', expected=True)

        urlh = self._request_webpage(
            update_url_query(balancer, {'return_http': 'true'}),
            video_id, note='Resolving balancer URL')
        manifest_url = urlh.url

        ext = determine_ext(manifest_url, 'mp4')
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                manifest_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats, subtitles = [{'url': manifest_url, 'ext': ext}], {}

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)
        description = json_ld.get('description')
        if description in ('', '...'):
            json_ld.pop('description', None)
            description = None

        return {
            **json_ld,
            'id': video_id,
            'title': traverse_obj(player, ('title', {str})) or json_ld.get('title'),
            'description': description,
            'thumbnail': (
                traverse_obj(player, ('poster', {url_or_none}))
                or self._og_search_thumbnail(webpage, default=None)),
            'duration': int_or_none(player.get('duration')) or json_ld.get('duration'),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True if player.get('live') else None,
        }
