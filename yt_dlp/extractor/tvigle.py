import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_age_limit,
    try_get,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class TvigleIE(InfoExtractor):
    IE_NAME = 'tvigle'
    IE_DESC = 'Интернет-телевидение Tvigle.ru'
    _VALID_URL = r'https?://(?:www\.)?(?:tvigle\.ru/(?:[^/]+/)+(?P<display_id>[^/]+)/?$|cloud\.tvigle\.ru/video/(?P<id>\d+))'
    _EMBED_REGEX = [r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//cloud\.tvigle\.ru/video/.+?)\1']

    _GEO_BYPASS = False
    _GEO_COUNTRIES = ['RU']

    _TESTS = [{
        'url': 'https://www.tvigle.ru/video/kharms-2023/',
        'md5': '9a6f4b8569018345796f8320a84c1251',
        'info_dict': {
            'id': '5839601',
            'display_id': 'kharms-2023',
            'ext': 'mp4',
            'title': 'Хармс',
            'description': '',
            'thumbnail': '/res/2026/07/08/498c04e3-cc37-43f4-ba7a-d45de69ca892.jpg',
            'duration': 793.088,
            'age_limit': 16,
        },
        'params': {
            'format': 'mp4-360p',
        },
    }, {
        'url': 'http://www.tvigle.ru/video/sokrat/',
        'info_dict': {
            'id': '1848932',
            'display_id': 'sokrat',
            'ext': 'mp4',
            'title': 'Сократ',
            'description': 'md5:d6b92ffb7217b4b8ebad2e7665253c17',
            'duration': 6586,
            'age_limit': 12,
        },
        'skip': 'video unpublished',
    }, {
        'url': 'http://www.tvigle.ru/video/vladimir-vysotskii/vedushchii-teleprogrammy-60-minut-ssha-o-vladimire-vysotskom/',
        'info_dict': {
            'id': '5142516',
            'ext': 'flv',
            'title': 'Ведущий телепрограммы «60 минут» (США) о Владимире Высоцком',
            'description': 'md5:027f7dc872948f14c96d19b4178428a4',
            'duration': 186.080,
            'age_limit': 0,
        },
        'skip': 'video unpublished',
    }, {
        'url': 'https://cloud.tvigle.ru/video/5267604/',
        'only_matching': True,
    }]

    def _cloud_id_from_next_data(self, next_data, display_id):
        fallback = (
            traverse_obj(next_data, ('props', 'pageProps', 'fallback', {dict}))
            or traverse_obj(next_data, ('pageProps', 'fallback', {dict}))
            or {})

        def iter_dicts(obj):
            if isinstance(obj, dict):
                yield obj
                for value in obj.values():
                    yield from iter_dicts(value)
            elif isinstance(obj, list):
                for value in obj:
                    yield from iter_dicts(value)

        slug_id = any_id = None
        for item in iter_dicts(fallback):
            content_id = item.get('content_id')
            if not content_id or item.get('content_provider') not in (None, 'cloud'):
                continue
            if item.get('slug') == display_id:
                slug_id = content_id
                break
            if any_id is None:
                any_id = content_id
        video_id = slug_id or any_id
        return str(video_id) if video_id else None

    def _extract_cloud_id(self, url, webpage, display_id):
        video_id = self._html_search_regex(
            (r'<div[^>]+class=["\']player["\'][^>]+id=["\'](\d+)',
             r'cloudId\s*=\s*["\'](\d+)',
             r'class="video-preview current_playing" id="(\d+)"'),
            webpage, 'video id', default=None)
        if video_id:
            return video_id

        next_data = self._search_nextjs_data(webpage, display_id, default={})
        video_id = self._cloud_id_from_next_data(next_data, display_id)
        if video_id:
            return video_id

        build_id = next_data.get('buildId')
        path = urllib.parse.urlparse(url).path.rstrip('/')
        if not build_id or not path:
            raise ExtractorError('Unable to extract video id')

        next_json = self._download_json(
            urljoin(url, f'/_next/data/{build_id}{path}.json'),
            display_id, 'Downloading Next.js data')
        video_id = self._cloud_id_from_next_data(next_json, display_id)
        if not video_id:
            raise ExtractorError('Unable to extract video id')
        return video_id

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        if not video_id:
            webpage = self._download_webpage(url, display_id)
            video_id = self._extract_cloud_id(url, webpage, display_id)

        video_data = self._download_json(
            f'https://cloud.tvigle.ru/api/play/video/{video_id}/',
            display_id or video_id)

        item = video_data['playlist']['items'][0]

        videos = item.get('videos')

        error_message = item.get('errorMessage')
        if not videos and error_message:
            if item.get('isGeoBlocked') is True:
                self.raise_geo_restricted(
                    msg=error_message, countries=self._GEO_COUNTRIES)
            else:
                raise ExtractorError(
                    f'{self.IE_NAME} returned error: {error_message}',
                    expected=True)

        title = item['title']
        description = item.get('description')
        thumbnail = item.get('thumbnail')
        duration = float_or_none(item.get('durationMilliseconds'), 1000)
        age_limit = parse_age_limit(item.get('ageRestrictions'))

        formats = []
        for vcodec, url_or_fmts in item['videos'].items():
            if vcodec == 'hls':
                m3u8_url = url_or_none(url_or_fmts)
                if not m3u8_url:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            elif vcodec == 'dash':
                mpd_url = url_or_none(url_or_fmts)
                if not mpd_url:
                    continue
                formats.extend(self._extract_mpd_formats(
                    mpd_url, video_id, mpd_id='dash', fatal=False))
            else:
                if not isinstance(url_or_fmts, dict):
                    continue
                for format_id, video_url in url_or_fmts.items():
                    if format_id == 'm3u8':
                        continue
                    video_url = url_or_none(video_url)
                    if not video_url:
                        continue
                    height = self._search_regex(
                        r'^(\d+)[pP]$', format_id, 'height', default=None)
                    filesize = int_or_none(try_get(
                        item, lambda x: x['video_files_size'][vcodec][format_id]))
                    formats.append({
                        'url': video_url,
                        'format_id': f'{vcodec}-{format_id}',
                        'vcodec': vcodec,
                        'height': int_or_none(height),
                        'filesize': filesize,
                    })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
            'formats': formats,
        }
