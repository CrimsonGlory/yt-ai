from urllib.parse import urlparse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    remove_end,
    traverse_obj,
    url_or_none,
    urljoin,
)


class AnonMP4IE(InfoExtractor):
    IE_DESC = 'AnonMP4'
    _VALID_URL = r'https?://(?:www\.)?anonmp4\.(?:art|to)/(?:v|embed|d)/(?P<id>[A-Za-z0-9]+)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?anonmp4\.(?:art|to)/embed/[A-Za-z0-9]+)']
    _TESTS = [{
        'url': 'https://anonmp4.art/v/gfFKPZb6t2HURbQ',
        'md5': '72c375f5cafcc8b7c3c4817b15ea0362',
        'info_dict': {
            'id': 'gfFKPZb6t2HURbQ',
            'ext': 'mp4',
            'title': 'trucks_on_the_moon.mp4',
            'thumbnail': r're:https?://.+',
            'duration': 6.0,
        },
    }, {
        'url': 'https://anonmp4.art/embed/gfFKPZb6t2HURbQ',
        'only_matching': True,
    }, {
        'url': 'https://anonmp4.to/v/gfFKPZb6t2HURbQ',
        'only_matching': True,
    }, {
        'url': 'https://anonmp4.art/d/gfFKPZb6t2HURbQ',
        'only_matching': True,
    }]

    def _extract_stream(self, api_url, video_id, referer, note='Downloading stream JSON'):
        stream = self._download_json(api_url, video_id, note, headers={'Referer': referer})
        error_type = traverse_obj(stream, ('type', {str}))
        if error_type in ('notready', 'remotepending'):
            raise ExtractorError('This video is still processing', expected=True)

        original = urljoin(api_url, traverse_obj(
            stream, 'orignalmp4', 'originalmp4', get_all=False))
        hls_url = urljoin(api_url, traverse_obj(stream, 'hls'))

        if error_type == 'nothls' and original:
            return {
                'formats': [{
                    'url': original,
                    'format_id': 'http',
                    'ext': 'mp4',
                }],
                'subtitles': {},
                **traverse_obj(stream, {
                    'thumbnail': ('thumbnail', {url_or_none}),
                    'duration': ('duration', {float_or_none}),
                }),
            }

        if stream.get('success') is False or stream.get('status') not in (None, 'ok'):
            raise ExtractorError(
                traverse_obj(stream, 'error', 'message', get_all=False) or 'Video unavailable',
                expected=True)

        formats, subtitles = [], {}
        if hls_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls')
        if original:
            formats.append({
                'url': original,
                'format_id': 'http',
                'ext': 'mp4',
                'quality': 1,
            })

        for sub in traverse_obj(stream, ('subtitles', lambda _, v: url_or_none(v['url']))) or []:
            lang = traverse_obj(sub, 'language', {str}) or 'und'
            self._merge_subtitles({lang: [{'url': sub['url']}]}, target=subtitles)

        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        return {
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(stream, {
                'thumbnail': ('thumbnail', {url_or_none}),
                'duration': ('duration', {float_or_none}),
            }),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = urlparse(url).hostname or 'anonmp4.art'
        referer = f'https://{host}/'
        webpage = self._download_webpage(f'https://{host}/v/{video_id}', video_id)

        status = self._search_regex(
            r'VIDEO_STATUS\s*=\s*["\']([^"\']+)["\']', webpage, 'status', default='active')
        if status in ('pending', 'processing'):
            raise ExtractorError('This video is still processing', expected=True)
        if status == 'failed':
            raise ExtractorError('This video failed to process', expected=True)
        if status == 'not_found':
            raise ExtractorError('This video does not exist', expected=True)

        api_url = self._search_regex(
            r'SINGLE_API_URL\s*=\s*["\'](https?://[^"\']+)["\']', webpage, 'API URL')
        video_type = self._search_regex(
            r'VIDEOTYPE\s*=\s*["\'](\d+)["\']', webpage, 'video type', default='0')

        title = (
            self._search_regex(
                r'VIDEO_TITLE\s*=\s*["\']([^"\']+)["\']', webpage, 'title', default=None)
            or remove_end(self._html_extract_title(webpage, default=''), ' - AnonMP4')
            or None)

        formats, subtitles = [], {}
        thumbnail = duration = None
        if video_type == '1':
            track_list = self._download_json(
                api_url, video_id, 'Downloading track list', headers={'Referer': referer})
            tracks = traverse_obj(
                track_list, ('tracks', lambda _, v: url_or_none(v['track_url']))) or []
            if not tracks:
                raise ExtractorError('Could not load track list', expected=True)
            for i, track in enumerate(tracks):
                lang = traverse_obj(track, 'track_name', {str}) or f'track{i}'
                try:
                    data = self._extract_stream(
                        track['track_url'], video_id, referer,
                        note=f'Downloading {lang} stream JSON')
                except ExtractorError as e:
                    self.report_warning(f'Failed to load track {lang}: {e}')
                    continue
                for fmt in data['formats']:
                    fmt['language'] = lang
                formats.extend(data['formats'])
                self._merge_subtitles(data.get('subtitles'), target=subtitles)
                thumbnail = thumbnail or data.get('thumbnail')
                duration = duration or data.get('duration')
        else:
            data = self._extract_stream(api_url, video_id, referer)
            formats, subtitles = data['formats'], data['subtitles']
            thumbnail, duration = data.get('thumbnail'), data.get('duration')

        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
            'duration': duration,
        }
