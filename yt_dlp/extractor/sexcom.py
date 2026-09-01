from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    str_or_none,
    unified_timestamp,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class SexComIE(InfoExtractor):
    IE_NAME = 'sex.com'
    IE_DESC = 'Sex.com'
    _VALID_URL = r'https?://(?:www\.)?sex\.com/(?:[a-z]{2}/)?(?:(?:gay|trans)/)?videos/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://www.sex.com/en/videos/1008955',
            'md5': 'a772dfb826d223bafbde12df7eac0b70',
            'info_dict': {
                'id': '1008955',
                'ext': 'mp4',
                'title': 'Amateur Fat Ass Latina Fucked Deep By Euro BWC In Fake Casting',
                'description': 'md5:df9f5dd40082fc40d84d426c39b1a824',
                'thumbnail': r're:https?://images\.sxccdn\.com/videos/1008955/.+',
                'duration': 634,
                'timestamp': 1785571804,
                'upload_date': '20260801',
                'uploader': 'Latina Casting',
                'uploader_id': '9745',
                'view_count': int,
                'like_count': int,
                'dislike_count': int,
                'cast': ['Andressa', 'steven hard'],
                'categories': [
                    'Amateur',
                    'Babe',
                    'Big Ass',
                    'Big Tits',
                    'Blowjob',
                    'Casting',
                    'Deepthroat',
                    'Hardcore',
                    'Latina',
                    'Rough Sex',
                ],
                'tags': 'count:15',
                'age_limit': 18,
            },
            'params': {
                # fMP4 HLS: native --test only fetches the EXT-X-MAP init segment
                'external_downloader': 'ffmpeg',
            },
        },
        {
            'url': 'https://www.sex.com/de/videos/1008955',
            'only_matching': True,
        },
        {
            'url': 'https://www.sex.com/en/gay/videos/1008955',
            'only_matching': True,
        },
        {
            'url': 'https://sex.com/en/videos/1008955',
            'only_matching': True,
        },
    ]
    _CDN_HOST = 'videos2.sex.com'

    def _apply_cloudfront_cookies(self, cookies, video_id):
        for name, value in (cookies or {}).items():
            if name.startswith('CloudFront-') and value:
                self._set_cookie(self._CDN_HOST, name, value, path=f'/{video_id}', secure=True)

    def _parse_nextjs_payload(self, webpage, video_id):
        cookies, video, details, is_premium = {}, {}, {}, False
        for data in self._search_nextjs_v13_data(webpage, video_id, fatal=False).values():
            if not isinstance(data, dict):
                continue
            cf_cookies = traverse_obj(data, ('cookies', {dict})) or {}
            if 'CloudFront-Policy' in cf_cookies:
                cookies = cf_cookies
            candidate = traverse_obj(data, ('video', {dict})) or {}
            if str_or_none(candidate.get('id')) == video_id:
                if not video or isinstance(candidate.get('channel'), dict):
                    video = candidate
            if isinstance(data.get('videoDetails'), dict):
                details = data['videoDetails']
            if data.get('isPremiumVideo'):
                is_premium = True
        return cookies, video, details, is_premium

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        cookies, video, details, is_premium = self._parse_nextjs_payload(webpage, video_id)
        self._apply_cloudfront_cookies(cookies, video_id)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        hls_url = url_or_none(json_ld.get('url'))
        src = traverse_obj(video, ('sources', 0, 'src', {str}))
        if src:
            hls_url = urljoin(f'https://{self._CDN_HOST}/{video_id}/', src) or hls_url
        if not hls_url:
            hls_url = url_or_none(
                self._search_regex(r'<source[^>]+src=["\'](https?://[^"\']+\.m3u8)', webpage, 'hls url', default=None),
            )

        headers = {
            'Referer': 'https://www.sex.com/',
            'Origin': 'https://www.sex.com',
        }
        formats, subtitles = [], {}
        if hls_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', headers=headers, fatal=False,
            )
        if not formats:
            if is_premium or video.get('premiumInfo'):
                self.raise_login_required('This video is only available for premium members', method='any')
            raise ExtractorError('No video sources found', expected=True)

        json_ld.pop('url', None)
        tags = traverse_obj(details, ('tags', ..., 'name', {str}))
        categories = traverse_obj(details, ('tags', lambda _, t: t.get('isCategory'), 'name', {str}))
        ld_raw = (
            self._search_json(
                r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>',
                webpage,
                'JSON-LD',
                video_id,
                end_pattern='</script>',
                fatal=False,
            )
            or {}
        )

        return {
            **json_ld,
            'id': video_id,
            'title': (video.get('title') or json_ld.get('title') or self._og_search_title(webpage, default=None)),
            'description': json_ld.get('description') or self._og_search_description(webpage, default=None),
            'thumbnail': json_ld.get('thumbnail') or self._og_search_thumbnail(webpage, default=None),
            'duration': int_or_none(video.get('durationSec')) or json_ld.get('duration'),
            'timestamp': (
                parse_iso8601(video.get('publishedAt'))
                or unified_timestamp(video.get('publishedAt'))
                or json_ld.get('timestamp')
            ),
            'uploader': traverse_obj(video, ('channel', 'name', {str})),
            'uploader_id': str_or_none(video.get('channelId') or traverse_obj(video, ('channel', 'id'))),
            'view_count': int_or_none(video.get('viewCount')) or json_ld.get('view_count'),
            'like_count': int_or_none(video.get('likeCount')),
            'dislike_count': int_or_none(video.get('dislikeCount')),
            'cast': traverse_obj(ld_raw, ('actor', ..., 'name', {str})) or None,
            'categories': categories or None,
            'tags': tags or None,
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
        }
