import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    merge_dicts,
    parse_iso8601,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class WCVBIE(InfoExtractor):
    IE_NAME = 'wcvb'
    IE_DESC = 'WCVB Channel 5 Boston (Hearst TV)'
    _VALID_URL = r'https?://(?:www\.)?wcvb\.com/article/(?:[^/?#]+/)?(?P<id>\d+)/?(?:[?#]|$)'
    _TESTS = [
        {
            'url': 'https://www.wcvb.com/article/video-sunny-monday-storms-and-showers-tuesday/73564166',
            'md5': 'e99f55bbcde7f5aded1115dce76feb9f',
            'info_dict': {
                'id': 'a86317fd-f812-44f1-b72a-58aa04b3b8df',
                'ext': 'mp4',
                'title': 'Video: Sunny Monday, storms and showers Tuesday',
                'description': 'md5:14f94d65439bf5c64ddb73cbeb95a8ec',
                'thumbnail': r're:https?://.+',
                'duration': 186,
                'timestamp': 1788129093,
                'upload_date': '20260830',
                'uploader': 'WCVB US',
                'display_id': '73564166',
                'creators': ['David Williams'],
                'tags': [
                    'warm Sunday',
                    'videocast',
                    'cooler weather',
                    'new england',
                    'storms',
                    'showers',
                    'rain',
                    'forecast',
                    'weather',
                    'Stormteam 5',
                    'Massachusetts',
                    'boston',
                    'wcvb',
                ],
            },
        },
        {
            'url': 'https://www.wcvb.com/article/boat-whale-rye-nh-capsized-video/61678814',
            'info_dict': {
                'id': '61678814',
                'title': 'Whale lands on boat off New Hampshire coast, throwing people into ocean',
            },
            'playlist_mincount': 3,
            'params': {'skip_download': True},
        },
        {
            'url': 'https://wcvb.com/article/boat-whale-rye-nh-capsized-video/61678814',
            'only_matching': True,
        },
    ]

    def _extract_article(self, webpage, display_id):
        for mobj in re.finditer(r'self\.__next_f\.push\(', webpage):
            if not webpage.startswith('[', mobj.end()):
                continue
            payload = self._parse_json(webpage[mobj.end() :], display_id, fatal=False, ignore_extra=True)
            if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], str):
                continue
            if 'voltronArticle' not in payload[1]:
                continue
            article = self._search_json(r'"voltronArticle"\s*:', payload[1], 'article data', display_id, fatal=False)
            if article:
                return article
        raise ExtractorError('Unable to extract article data', expected=True)

    def _parse_video(self, video, article, display_id):
        video_id = traverse_obj(video, ('videoId', {str}))
        formats = []
        for transcoding in traverse_obj(video, ('transcodings', ..., {dict})):
            url = traverse_obj(transcoding, ('full_url', {url_or_none}))
            if not url:
                continue
            status = traverse_obj(transcoding, ('status', {str}))
            if status and status.lower() != 'complete':
                continue
            formats.append(
                {
                    'url': url,
                    'format_id': traverse_obj(transcoding, ('mapped_preset_name', {str}), ('preset_name', {str})),
                    'width': int_or_none(transcoding.get('width')),
                    'height': int_or_none(transcoding.get('height')),
                    'tbr': int_or_none(transcoding.get('bitrate')),
                    'fps': int_or_none(transcoding.get('frame_rate')),
                },
            )
        if not formats:
            self.raise_no_formats('No video transcodings found', video_id=video_id, expected=True)

        def split_tags(value):
            if not isinstance(value, str):
                return None
            return [tag.strip() for tag in value.split(',') if tag.strip()] or None

        return merge_dicts(
            {
                'id': video_id,
                'display_id': display_id,
                'formats': formats,
            },
            traverse_obj(
                video,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                    'thumbnail': ('croppedPreviewImage', {url_or_none}),
                    'duration': ('duration', {int_or_none}),
                    'timestamp': (('created_at', 'updated_at'), {parse_iso8601}, any),
                    'uploader': ('source', 'title', {str}),
                },
            ),
            traverse_obj(
                article,
                {
                    'title': ('title', {str}),
                    'description': (
                        [
                            ('metadata', 'seo_meta_description', {str}),
                            ('metadata', 'social_dek', {clean_html}),
                            ('metadata', 'dek', {clean_html}),
                        ],
                        any,
                    ),
                    'timestamp': ('publish_from', {parse_iso8601}),
                    'uploader': ('publish_source', 'title', {str}),
                    'tags': ('metadata', 'seo_meta_keywords', {split_tags}),
                    'creators': ('authors', ..., 'profile', 'display_name', {strip_or_none}),
                },
            ),
        )

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        article = self._extract_article(webpage, display_id)
        videos = traverse_obj(
            article,
            (
                'media',
                lambda _, v: v.get('media_type') == 'video' and v.get('videoId') and v.get('transcodings'),
                {dict},
            ),
        )
        if not videos:
            raise ExtractorError('No video found on this page', expected=True)

        entries = [self._parse_video(video, article, display_id) for video in videos]
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, display_id, traverse_obj(article, ('title', {str})), multi_video=True)
