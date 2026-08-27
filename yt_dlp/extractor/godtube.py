from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class GodTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?godtube\.com/(?:watch/\?v=|video/)(?P<id>[\da-zA-Z-]+)'
    _TESTS = [{
        'url': 'https://www.godtube.com/watch/?v=GYZGDPNX',
        'md5': 'cdc2e3d05fd7f0518cb6b44d26003b60',
        'info_dict': {
            'id': 'GYZGDPNX',
            'ext': 'mp4',
            'title': "Lyric Video Bryan and Katie Torwalt 'My Refuge'",
            'duration': 287,
            'timestamp': 1773247020,
            'uploader': 'Bryan and Katie Torwalt',
            'upload_date': '20260311',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg)',
            'description': str,
        },
    }, {
        'url': 'https://www.godtube.com/watch/?v=0C0CNNNU',
        'skip': 'video gone',
        'md5': '77108c1e4ab58f48031101a1a2119789',
        'info_dict': {
            'id': '0C0CNNNU',
            'ext': 'mp4',
            'title': 'Woman at the well.',
            'duration': 159,
            'timestamp': 1205712000,
            'uploader': 'beverlybmusic',
            'upload_date': '20080317',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = url_or_none(self._html_search_meta('contentUrl', webpage, default=None))
        title = self._html_search_meta('name', webpage, default=None) or self._og_search_title(webpage, default=None)
        thumbnail = self._html_search_meta('thumbnailUrl', webpage, default=None) or self._og_search_thumbnail(webpage)
        duration = parse_duration(self._html_search_meta('duration', webpage, default=None))
        timestamp = parse_iso8601(self._html_search_meta('uploadDate', webpage, default=None))
        description = self._og_search_description(webpage, default=None)
        uploader = self._html_search_regex(
            r'<div class="user[^"]*">\s*<a[^>]+title="([^"]+)"', webpage, 'uploader', default=None)

        if not video_url:
            player = self._search_json(
                r'var\s+bpConfig\s*=', webpage, 'player config', video_id, fatal=False)
            video = traverse_obj(player, ('video', 'Video', 0, {dict})) or {}
            video_url = self._proto_relative_url(traverse_obj(video, ('source', 'sd', {url_or_none})))
            title = title or traverse_obj(video, ('title', {unescapeHTML}))
            thumbnail = thumbnail or traverse_obj(
                video, (('image', 'thumbnail'), {url_or_none}), get_all=False)

        if not video_url:
            config = self._download_xml(
                f'https://www.godtube.com/resource/mediaplayer/{video_id.lower()}.xml',
                video_id, 'Downloading player config XML', fatal=False)
            if config:
                video_url = getattr(config.find('file'), 'text', None)
                uploader = uploader or getattr(config.find('author'), 'text', None)
                timestamp = timestamp or parse_iso8601(getattr(config.find('date'), 'text', None))
                duration = duration or parse_duration(getattr(config.find('duration'), 'text', None))
                thumbnail = thumbnail or getattr(config.find('image'), 'text', None)

            media = self._download_xml(
                f'https://www.godtube.com/media/xml/?v={video_id}', video_id,
                'Downloading media XML', fatal=False)
            if media:
                title = title or getattr(media.find('title'), 'text', None)

        if not video_url:
            yt_id = self._html_search_regex(
                r'<lite-youtube[^>]+\bvideoid=["\'](?P<id>[\w-]+)',
                webpage, 'youtube id', default=None, group='id')
            if yt_id:
                return self.url_result(yt_id, 'Youtube', yt_id)
            self.raise_no_formats('Unable to extract video URL', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'url': video_url,
            'title': title or video_id,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'duration': duration,
        }
