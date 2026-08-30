from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class SasflixIE(InfoExtractor):
    IE_NAME = 'sasflix'
    IE_DESC = 'Sasflix'
    _UUID_RE = r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}'
    _VALID_URL = rf'https?://(?:www\.)?sasflix\.ru/topics/(?P<id>{_UUID_RE})'
    _TESTS = [{
        'url': 'https://sasflix.ru/topics/a7851209-c06a-446a-9adc-aaf92ef8fae0',
        'md5': '7b3996a4374c6b33fa87b67968faf1fd',
        'info_dict': {
            'id': 'a7851209-c06a-446a-9adc-aaf92ef8fae0',
            'ext': 'mp4',
            'title': 'Сильный паспорт // Долину обездолили // Венесуэле хана №177',
            'description': 'Лидерская программа «100 Лидеров» - это шанс получить ценные навыки, опыт и вознаграждение мирового уровня. Подробнее: https://clck.ru/3Qqy3V',
            'thumbnail': r're:https?://sasflix\.ru/api/.+',
            'duration': 2024,
            'timestamp': 1766070581,
            'upload_date': '20251218',
            'view_count': int,
            'comment_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': ['Новости'],
        },
        'params': {'format': 'http-original'},
    }, {
        'url': 'https://www.sasflix.ru/topics/a7851209-c06a-446a-9adc-aaf92ef8fae0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        topic_id = self._match_id(url)
        topic = self._download_json(
            f'https://sasflix.ru/api/web/topics/{topic_id}', topic_id)

        video_id = traverse_obj(topic, (
            (('video', 'id'), (
                'content', 'blocks', lambda _, v: v.get('type') == 'video', 'data', 'uuid')),
            {str}, any, {require('video id')}))
        video_meta = traverse_obj(topic, (
            'content', 'blocks', lambda _, v: (
                v.get('type') == 'video' and traverse_obj(v, ('data', 'uuid')) == video_id),
            'data', {dict}, any)) or {}

        if topic.get('access') is False:
            self.raise_login_required(
                'This video is only available to subscribers', method='password')

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'https://sasflix.ru/api/video/{video_id}', topic_id, 'mp4',
            m3u8_id='hls', fatal=False)

        http_heights = set()
        for fmt in tuple(formats):
            height = fmt.get('height')
            if not height or height in http_heights:
                continue
            http_heights.add(height)
            formats.append({
                'url': f'https://sasflix.ru/api/video/{video_id}/download/{height}',
                'format_id': f'http-{height}',
                'height': height,
                'width': fmt.get('width'),
                'ext': 'ts',
            })
        formats.append({
            'url': f'https://sasflix.ru/api/video/{video_id}/download',
            'format_id': 'http-original',
            'ext': 'mp4',
            **traverse_obj(video_meta, {
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'filesize': ('size', {int_or_none}),
            }),
        })

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=topic_id)

        cover_id = traverse_obj(topic, ('cover', 'uuid', {str}))
        thumbnail = (
            f'https://sasflix.ru/api/image/{cover_id}' if cover_id
            else f'https://sasflix.ru/api/poster/{video_id}')

        return {
            'id': topic_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': url_or_none(thumbnail),
            **traverse_obj(topic, {
                'title': ('title', {str}),
                'description': ('teaser', {str}),
                'timestamp': ('published_at', {parse_iso8601}),
                'view_count': ('views_count', {int_or_none}),
                'comment_count': ('comments_count', {int_or_none}),
                'like_count': ('reactions', '1', {int_or_none}),
                'dislike_count': ('reactions', '2', {int_or_none}),
                'tags': ('tags', ..., 'title', {str}, filter, all, filter),
            }),
            'duration': int_or_none(video_meta.get('duration')) or traverse_obj(
                topic, ('video', 'duration', {int_or_none})),
        }
