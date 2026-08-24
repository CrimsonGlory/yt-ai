from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class GodTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?godtube\.com/(?:watch/\?v=|video/)(?P<id>[\da-zA-Z-]+)'
    _TESTS = [
        {
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
        },
    ]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')

        config = self._download_xml(
            f'https://www.godtube.com/resource/mediaplayer/{video_id.lower()}.xml',
            video_id, 'Downloading player config XML', fatal=False)

        video_url = uploader = timestamp = duration = thumbnail = title = None
        if config is not None:
            video_url = getattr(config.find('file'), 'text', None)
            uploader = getattr(config.find('author'), 'text', None)
            timestamp = parse_iso8601(getattr(config.find('date'), 'text', None))
            duration = parse_duration(getattr(config.find('duration'), 'text', None))
            thumbnail = getattr(config.find('image'), 'text', None)

        media = self._download_xml(
            f'https://www.godtube.com/media/xml/?v={video_id}', video_id,
            'Downloading media XML', fatal=False)
        if media is not None:
            title = getattr(media.find('title'), 'text', None)

        if not video_url:
            webpage = self._download_webpage(url, video_id)
            json_ld = self._search_json_ld(webpage, video_id, default={})
            video_url = (
                json_ld.get('url') or json_ld.get('contentUrl')
                or self._og_search_video_url(webpage, default=None))
            title = title or json_ld.get('title') or self._og_search_title(webpage, default=video_id)
            thumbnail = thumbnail or self._og_search_thumbnail(webpage)
            html5 = self._parse_html5_media_entries(url, webpage, video_id)
            if html5 and not video_url:
                return {
                    **html5[0],
                    'id': video_id,
                    'title': title,
                    'thumbnail': thumbnail,
                    'uploader': uploader,
                }

        return {
            'id': video_id,
            'url': video_url,
            'title': title or video_id,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'duration': duration,
        }
