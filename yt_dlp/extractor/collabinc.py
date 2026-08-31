from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CollabIncIE(InfoExtractor):
    IE_NAME = 'collabinc'
    IE_DESC = 'Collab.inc video library'
    _VALID_URL = r'https?://(?:(?:www|vl|dashboard)\.)?collab\.inc/(?:videos|api/public_video_library)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://vl.collab.inc/videos/553891',
        'md5': '0fa12ad4913c9a6ffd10766dbdde9d21',
        'info_dict': {
            'id': '553891',
            'ext': 'mp4',
            'title': 'Collab Clips MPUGC - Getting ducks out of garage',
            'description': 'md5:89314a7cb927cdcf44a96f349d6265d6',
            'thumbnail': r're:https?://collab-media-assets\.s3-us-west-2\.amazonaws\.com/.+\.jpg',
            'duration': 11,
            'timestamp': 1717098181,
            'upload_date': '20240530',
            'display_id': '5548610291',
            'average_rating': 3.7,
            'view_count': int,
            'tags': 'count:43',
        },
    }, {
        'url': 'https://dashboard.collab.inc/api/public_video_library/553891',
        'only_matching': True,
    }, {
        'url': 'https://www.collab.inc/videos/553891',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._download_json(
            f'https://dashboard.collab.inc/api/public_video_library/{video_id}',
            video_id, headers={'Accept': 'application/json'})

        hls_url = traverse_obj(video, ('hls_stream', {url_or_none}))
        if not hls_url:
            self.raise_no_formats('No HLS stream', expected=True, video_id=video_id)

        formats, subtitles = [], {}
        clean_url = hls_url.replace('/watermarked_hls/', '/hls/')
        if clean_url != hls_url:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                clean_url, video_id, 'mp4', m3u8_id='hls', preference=1, fatal=False)
            for f in fmts:
                f.setdefault('format_note', 'unwatermarked')
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        fmts, subs = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4',
            m3u8_id='hls-wm' if formats else 'hls',
            preference=-1 if formats else None, fatal=False)
        if '/watermarked_hls/' in hls_url:
            for f in fmts:
                f.setdefault('format_note', 'watermarked')
        formats.extend(fmts)
        self._merge_subtitles(subs, target=subtitles)

        if not formats:
            self.raise_no_formats('No playable formats', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(video, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('thumbnail_url', {url_or_none}),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('created_at', {unified_timestamp}),
                'view_count': ('views', {int_or_none}),
                'average_rating': ('rating', {float_or_none}),
                'display_id': ('uid', {str}),
                'location': ('location', {str}, filter),
                'tags': ('tags', ..., {str}),
            }),
        }
