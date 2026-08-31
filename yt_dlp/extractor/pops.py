from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_age_limit,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PopsIE(InfoExtractor):
    IE_NAME = 'pops'
    IE_DESC = 'POPS'
    _VALID_URL = r'https?://(?:www\.)?pops\.vn/video/(?:[^/?#]*-)?(?P<id>[0-9a-f]{24})'
    _TESTS = [{
        'url': 'https://pops.vn/video/truc-nhan-hua-kim-tuyen-cham-gan-them-thuong-official-mv-645dee634507cb005fbe2328',
        'md5': '641c895b3e9a54e0903f5722bab90b78',
        'info_dict': {
            'id': '-i20u77xp1E',
            'ext': 'mp4',
            'title': 'Trúc Nhân x Hứa Kim Tuyền | Chạm Gần Thêm Thương | Official MV',
            'description': 'md5:0d7dcde6279c040415dc267818d46230',
            'duration': 310,
            'uploader': 'Trúc Nhân',
            'uploader_id': '@trucnhanchannel',
            'uploader_url': 'https://www.youtube.com/@trucnhanchannel',
            'channel': 'Trúc Nhân',
            'channel_id': 'UC9c3qUdRWmMic4-5yTjvCNA',
            'channel_url': 'https://www.youtube.com/channel/UC9c3qUdRWmMic4-5yTjvCNA',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1683892808,
            'upload_date': '20230512',
            'release_timestamp': 1683892808,
            'release_date': '20230512',
            'release_year': 2023,
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Music'],
            'tags': 'count:12',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
            'heatmap': 'count:100',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
        ],
    }, {
        'url': 'https://pops.vn/video/645dee634507cb005fbe2328',
        'only_matching': True,
    }, {
        'url': 'https://www.pops.vn/video/mua-2-biet-doi-th-squad-tap-5-2-cau-be-than-va-cau-be-bong-ma-6a6338c9934e9f002e1861bc',
        'only_matching': True,
    }, {
        'url': 'https://pops.vn/video/doraemon-s9-tap-417-hat-dau-ac-quy-bi-day-6013831da0c3120034d08bf6',
        'only_matching': True,
    }]

    @staticmethod
    def _normalize_source_url(source_url):
        """POPS sometimes concatenates query params with '&' instead of '?'."""
        if source_url and '.m3u8&' in source_url:
            return source_url.replace('.m3u8&', '.m3u8?', 1)
        if source_url and '.mpd&' in source_url:
            return source_url.replace('.mpd&', '.mpd?', 1)
        return source_url

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = traverse_obj(
            self._search_nextjs_data(webpage, video_id),
            ('props', 'pageProps', {dict})) or {}
        video_detail = traverse_obj(page_props, ('videoDetail', {dict})) or {}
        video_info = traverse_obj(video_detail, ('videoInfo', {dict})) or {}

        if not video_info and not video_detail:
            raise ExtractorError('Unable to extract video data', expected=True)

        if traverse_obj(video_info, 'isAppliedDRM'):
            self.report_drm(video_id)

        if video_detail.get('isRestrictedContentData'):
            self.raise_geo_restricted(countries=traverse_obj(
                video_info, ('regionRestriction', 'blocked', ..., {str})))

        youtube_id = str_or_none(video_info.get('youtubeID'))
        source_type = (video_detail.get('sourceType') or '').lower()
        if not youtube_id and source_type in ('yt', 'youtube'):
            youtube_id = str_or_none(video_detail.get('sourceResId'))
        source_url = self._normalize_source_url(url_or_none(video_detail.get('sourceLink')))
        if not youtube_id and source_url:
            youtube_id = self._search_regex(
                r'youtube\.com/streaming/[^/]+/[^/]+/(?P<ytid>[^/?#]+)/index\.m3u8',
                source_url, 'youtube id', default=None)

        if youtube_id and YoutubeIE.suitable(youtube_id):
            return self.url_result(youtube_id, YoutubeIE, youtube_id)

        if page_props.get('isPaid') and not video_info.get('isUnlocked'):
            self.raise_login_required('This video requires a POPS account')

        formats, subtitles = [], {}
        ext = determine_ext(source_url)
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                source_url, video_id, 'mp4', m3u8_id='hls')
        elif ext == 'mpd':
            formats, subtitles = self._extract_mpd_formats_and_subtitles(
                source_url, video_id, mpd_id='dash')
        elif source_url:
            formats = [{'url': source_url, 'ext': ext or 'mp4'}]

        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(video_info, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('thumbnails', ('maxres', 'high', 'hi', 'medium', 'default'), 'url', {url_or_none}),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('publishedAt', {parse_iso8601}),
                'like_count': ('totalLike', {int_or_none}),
                'age_limit': ('mpaa', 'name', {parse_age_limit}),
                'release_timestamp': ('releaseAt', {parse_iso8601}),
                'release_year': ('releasedYear', {int_or_none}),
            }),
        }
