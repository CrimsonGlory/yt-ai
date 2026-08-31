from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    merge_dicts,
    orderedSet,
    traverse_obj,
    url_or_none,
)


class PornHatIE(InfoExtractor):
    IE_DESC = 'pornhat.com'
    _VALID_URL = (
        r'https?://(?:www\.)?pornhat\.com/'
        r'(?:embed/(?P<embed_id>\d+)|video/(?:(?P<video_id>\d+)/)?(?P<slug>[^/?#]+))')
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?pornhat\.com/embed/\d+)']
    _TESTS = [{
        'url': 'https://www.pornhat.com/video/cover-girl-ava-koxxx-at-milf-video/',
        'md5': '6aeab66e7da052699c6013803a761af6',
        'info_dict': {
            'id': '507630',
            'ext': 'mp4',
            'display_id': 'cover-girl-ava-koxxx-at-milf-video',
            'title': 'Cover-girl Ava Koxxx at milf video',
            'description': 'md5:2fca3d3f07b2cf65c1f0785215f97c83',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg|png)',
            'duration': 359,
            'timestamp': 1734570309,
            'upload_date': '20241219',
            'view_count': int,
            'uploader': 'Adult Prime',
            'cast': ['Ava Koxxx'],
            'tags': ['blowjob', 'big tits', 'big ass', 'big cock', 'doggystyle', 'brunette', 'cowgirl', 'oral', 'missionary', 'milf', 'side fuck', 'curvy', 'long legs', 'long hair', 'straight hair'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.pornhat.com/video/507630/cover-girl-ava-koxxx-at-milf-video/',
        'only_matching': True,
    }, {
        'url': 'https://www.pornhat.com/embed/507630',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('embed_id') or mobj.group('video_id')
        display_id = mobj.group('slug') or video_id
        webpage = self._download_webpage(url, display_id)

        if not video_id:
            video_id = (
                self._html_search_regex(
                    r'\bdata-video_id=["\'](\d+)', webpage, 'video id', default=None)
                or self._search_regex(
                    r'/embed/(\d+)', webpage, 'video id', default=None)
                or self._search_regex(
                    r'/videos_screenshots/\d+/(\d+)/', webpage, 'video id',
                    default=display_id))

        media_urls, thumbnail = [], None
        for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
            thumbnail = thumbnail or entry.get('thumbnail')
            for fmt in entry.get('formats') or []:
                src = url_or_none(fmt.get('url'))
                if src and '/get_file/' in src and '_preview' not in src:
                    media_urls.append(src)
        media_urls = orderedSet(media_urls)

        if not media_urls:
            canonical = self._search_regex(
                (r'<link[^>]+href="(https?://(?:www\.)?pornhat\.com/video/[^"]+)"[^>]*rel="canonical"',
                 r'<link[^>]+rel="canonical"[^>]+href="(https?://(?:www\.)?pornhat\.com/video/[^"]+)"',
                 r"window\.location\s*=\s*'(https?://(?:www\.)?pornhat\.com/video/[^']+)'"),
                webpage, 'canonical URL', default=None)
            if canonical:
                return self.url_result(canonical, ie=self.ie_key())
            raise ExtractorError('No video source found', expected=True)

        formats, subtitles = [], {}
        for media_url in media_urls:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                headers={'Referer': url})
            if hls_fmts:
                formats, subtitles = hls_fmts, hls_subs
                break
            formats.append({
                'url': media_url,
                'ext': 'mp4',
                'http_headers': {'Referer': url},
            })

        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)

        schema = self._search_json(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>',
            webpage, 'json-ld', video_id, default={})

        return merge_dicts(json_ld, {
            'id': video_id,
            'display_id': display_id,
            'title': (
                json_ld.get('title')
                or self._og_search_title(webpage, default=None)
                or self._html_extract_title(webpage)),
            'description': (
                json_ld.get('description')
                or self._og_search_description(webpage)),
            'thumbnail': (
                thumbnail
                or json_ld.get('thumbnail')
                or self._og_search_thumbnail(webpage, default=None)),
            'duration': json_ld.get('duration') or int_or_none(self._search_regex(
                r'\$duration_video\s*=\s*(\d+)', webpage, 'duration', default=None)),
            'cast': traverse_obj(schema, ('actor', ..., {str})) or None,
            'tags': traverse_obj(schema, ('keywords', ..., {str})) or None,
            'formats': formats,
            'subtitles': subtitles or None,
            'age_limit': 18,
        })
