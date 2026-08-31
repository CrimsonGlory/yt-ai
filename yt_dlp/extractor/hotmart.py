from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class HotmartIE(InfoExtractor):
    IE_NAME = 'hotmart'
    IE_DESC = 'Hotmart Player'
    _VALID_URL = r'https?://player\.hotmart\.com/(?:vl/)?embed/(?P<id>[A-Za-z0-9]+)(?:[/?#]|$)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://player\.hotmart\.com/(?:vl/)?embed/[^"\']+)\1']
    _TESTS = [{
        'url': 'https://player.hotmart.com/embed/YRlz0nrjLw',
        'md5': '06175a24c9381d61b9304908404a56d6',
        'info_dict': {
            'id': 'YRlz0nrjLw',
            'ext': 'mp4',
            'title': 'YRlz0nrjLw',
            'thumbnail': r're:https?://img-akm\.play\.hotmart\.com/video/YRlz0nrjLw/thumbnail/.+',
            'duration': 140,
            'timestamp': 1750953413,
            'upload_date': '20250626',
        },
    }, {
        'url': 'https://player.hotmart.com/embed/QZPl6Gw9Zw',
        'only_matching': True,
    }, {
        'url': 'https://player.hotmart.com/embed/Nq7BgloxRA?signature=abc&token=aa2d356b-e2f0-45e8-9725-e0efc7b5d29c&user=94011085',
        'only_matching': True,
    }, {
        'url': 'https://player.hotmart.com/vl/embed/jnRvQeYZQr?enable-controls=true&autoplay=false',
        'only_matching': True,
    }]
    _MEDIA_HEADERS = {
        'Referer': 'https://player.hotmart.com/',
        'Origin': 'https://player.hotmart.com',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = traverse_obj(
            self._search_nextjs_data(webpage, video_id),
            ('props', 'pageProps', {dict})) or {}

        error = traverse_obj(page_props, ('error', {dict}))
        if error:
            status = traverse_obj(error, ('statusCode', {int_or_none}))
            message = traverse_obj(error, ('title', {str})) or 'Hotmart player error'
            if status == 401:
                self.raise_login_required()
            raise ExtractorError(message, expected=True)

        app_data = traverse_obj(page_props, ('applicationData', {dict}))
        if not app_data:
            raise ExtractorError('Unable to extract application data')

        if app_data.get('isDrmEnabled'):
            self.report_drm(video_id)

        formats, subtitles = [], {}
        for m3u8_url in orderedSet(traverse_obj(app_data, (
            'mediaAssets', ..., ('url', 'urlEncrypted'), {url_or_none},
        ))):
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', headers=self._MEDIA_HEADERS)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if not formats:
            self.raise_no_formats('No media assets found', expected=True, video_id=video_id)

        for f in formats:
            f.setdefault('http_headers', {}).update(self._MEDIA_HEADERS)

        return {
            'id': video_id,
            'title': traverse_obj(app_data, ('mediaTitle', {str}, filter)) or video_id,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': self._MEDIA_HEADERS,
            **traverse_obj(app_data, {
                'thumbnail': ('thumbnailUrl', {url_or_none}),
                'duration': ('mediaDuration', {int_or_none}),
                'timestamp': ('finishTranscodeDate', {int_or_none(scale=1000)}),
            }),
        }
