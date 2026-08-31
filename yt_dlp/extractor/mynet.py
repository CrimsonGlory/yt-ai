from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    js_to_json,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class MyNetIE(InfoExtractor):
    IE_NAME = 'mynet'
    IE_DESC = 'Mynet Video'
    _VALID_URL = (
        r'https?://(?:www\.)?mynet\.com/[^/?#]+-(?P<id>\d+)-myvideo',
        r'https?://(?:www\.)?mynet\.com/tv/embed/(?P<id>\d+)',
        r'https?://(?:www\.)?mynet\.com/amp/[^/?#]+-izle-(?P<id>\d+)\.html',
    )
    _EMBED_REGEX = [r'<iframe[^>]+\bid=["\']mynetVideoEmbed["\'][^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?mynet\.com/tv/embed/\d+[^"\']*)']
    _TESTS = [{
        'url': 'https://www.mynet.com/yunanistanda-muhimmat-deposunda-patlama-8205260-myvideo',
        'md5': '2e23105d3da1a6b0caf04b6935c0bbd8',
        'info_dict': {
            'id': '8205260',
            'ext': 'mp4',
            'title': 'Yunanistan’da mühimmat deposunda patlama',
            'thumbnail': r're:https://imgmyntv\.mynet\.com/images/8205260/.+',
            'duration': 29,
        },
        'params': {'format': 'http'},
    }, {
        'url': 'https://www.mynet.com/tv/embed/8205260',
        'only_matching': True,
    }, {
        'url': 'https://www.mynet.com/el-yapimi-sualti-kamerasi-2686013-myvideo',
        'only_matching': True,
    }, {
        'url': 'https://www.mynet.com/amp/yunanistanda-muhimmat-deposunda-patlama-izle-8205260.html',
        'only_matching': True,
    }]

    def _add_media_url(self, formats, subtitles, video_id, media_url, seen):
        media_url = url_or_none(media_url)
        if not media_url:
            return
        key = media_url.split('://', 1)[-1]
        if key in seen:
            return
        seen.add(key)
        if determine_ext(media_url) == 'm3u8':
            hls_formats, hls_subs = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_formats)
            self._merge_subtitles(hls_subs, target=subtitles)
            return
        formats.append({
            'url': media_url,
            'format_id': 'http',
            'ext': determine_ext(media_url, 'mp4'),
        })

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            f'https://www.mynet.com/tv/embed/{video_id}', video_id)

        video_info = self._search_json(
            r'\bvideoInfo\s*=', webpage, 'video info', video_id,
            end_pattern=r',\s*playerOptions', transform_source=js_to_json)

        formats, subtitles, seen = [], {}, set()
        media = traverse_obj(video_info, ('media', {dict})) or {}
        for level in traverse_obj(media, ('level', ..., {dict})) or []:
            self._add_media_url(
                formats, subtitles, video_id, level.get('source'), seen)
        self._add_media_url(
            formats, subtitles, video_id, media.get('source'), seen)
        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        return {
            'id': video_id,
            'title': (traverse_obj(video_info, ('videoTitle', {unescapeHTML}))
                      or self._html_extract_title(webpage)),
            'thumbnail': traverse_obj(video_info, ('posterURL', {url_or_none})),
            'duration': traverse_obj(video_info, ('duration', {int_or_none})),
            'formats': formats,
            'subtitles': subtitles,
            'webpage_url': traverse_obj(video_info, ('videoPageURL', {url_or_none})) or url,
        }
