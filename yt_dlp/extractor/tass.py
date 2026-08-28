from .common import InfoExtractor
from ..utils import (
    traverse_obj,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class TassIE(InfoExtractor):
    _VALID_URL = r'https?://(?:tass\.ru|itar-tass\.com)/[^/]+/(?P<id>\d+)'
    _CDN_BASE = 'https://cdn-storage-media.tass.ru/'
    _TESTS = [{
        'url': 'http://tass.ru/obschestvo/1586870',
        'md5': '3b4cdd011bc59174596b6145cda474a4',
        'info_dict': {
            'id': '1586870',
            'ext': 'mp4',
            'title': 'Посетителям московского зоопарка показали красную панду',
            'description': 'Приехавшую из Дублина Зейну можно увидеть в павильоне "Кошки тропиков"',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1416500844,
            'upload_date': '20141120',
        },
    }, {
        'url': 'http://itar-tass.com/obschestvo/1600009',
        'only_matching': True,
    }]

    def _media_url(self, path):
        if not path:
            return None
        return path if path.startswith('http') else urljoin(self._CDN_BASE, path)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        article = self._download_json(
            f'https://tass.ru/tbp/api/v1/content/{video_id}', video_id,
            query={'lang': 'ru'}, impersonate=True)['result']

        formats, seen = [], set()
        media_paths = []
        main_video = traverse_obj(article, ('main_media', 'video', 'url', {str}))
        if main_video:
            media_paths.append(main_video)
        media_paths.extend(traverse_obj(
            article, ('material_media', 'videos', ..., 'url', {str})) or [])
        for path in media_paths:
            video_url = self._media_url(path)
            if not video_url or video_url in seen:
                continue
            seen.add(video_url)
            formats.append({'url': video_url, 'ext': 'mp4'})

        m3u8_url = url_or_none(traverse_obj(article, ('stream', 'm3u8', {str})))
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        return {
            'id': video_id,
            **traverse_obj(article, {
                'title': ('title', {str}),
                'description': (('lead', 'meta_description'), {str}, filter, any),
                'thumbnail': ('main_media', 'video', 'preview', {url_or_none}),
                'timestamp': ('published_dt', {unified_timestamp}),
            }),
            'formats': formats,
        }
