from .common import InfoExtractor
from .dailymotion import DailymotionIE
from .youtube import YoutubeIE
from ..utils import ExtractorError, traverse_obj


class ImagenTVIE(InfoExtractor):
    IE_NAME = 'imagentv'
    IE_DESC = 'Imagen Televisión'
    _VALID_URL = (
        r'https?://(?:www\.)?imagentv\.com/'
        r'(?P<id>en-vivo|(?:(?:guadalajara|monterrey|puebla)/)?'
        r'(?:noticias|teleseries|entretenimiento|deportes)/[^/?#]+/[^/?#]+)/?')
    _TESTS = [{
        'url': 'https://www.imagentv.com/noticias/que-importa/que-importa-programa-completo-28-de-agosto-de-2026',
        'md5': '21bea32ea6d54c06ada5efe851185ae3',
        'info_dict': {
            'id': 'xb1z26i',
            'ext': 'mp4',
            'title': 'Qué Importa | Programa completo 28 de agosto de 2026',
            'description': '',
            'thumbnail': r're:https?://s\d+\.dmcdn\.net/.+',
            'duration': 1162,
            'timestamp': 1787982913,
            'upload_date': '20260829',
            'uploader': 'Imagen Noticias',
            'uploader_id': 'x1y5oif',
            'age_limit': 0,
            'view_count': int,
            'like_count': int,
            'tags': list,
        },
        'params': {'external_downloader': 'ffmpeg'},
        'add_ie': ['Dailymotion'],
    }, {
        # Teleseries episode (Dailymotion is often Mexico-geo-restricted)
        'url': 'https://www.imagentv.com/teleseries/legado-de-amor/e-24-legado-de-amor-propuesta-de-matrimonio',
        'only_matching': True,
    }, {
        'url': 'https://www.imagentv.com/teleseries/josue-y-la-tierra-prometida/e-97-josue-y-la-tierra-prometida-la-condena',
        'only_matching': True,
    }, {
        'url': 'https://www.imagentv.com/guadalajara/noticias/imagen-noticias-guadalajara-tercera-emision/noticias-gdl-con-ricardo-camarena-programa-del-28082026',
        'only_matching': True,
    }, {
        'url': 'https://www.imagentv.com/en-vivo',
        'only_matching': True,
    }]

    def _extract_host_result(self, video, webpage=None):
        video = video or {}
        dm_id = (
            traverse_obj(video, ('daily_motion', 'id', {str}))
            or traverse_obj(video, ('dailymotion_id', {str})))
        if not dm_id and webpage:
            dm_id = self._search_regex(
                r'window\.IdVideoNode\s*=\s*["\'](\w+)', webpage,
                'dailymotion id', default=None)
        yt_id = traverse_obj(video, ('youtube', 'embed_id', {str}))
        video_type = traverse_obj(video, (('type_video', 'type'), {str}), get_all=False)

        if video_type == '2' and yt_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={yt_id}', YoutubeIE, yt_id)
        if dm_id:
            return self.url_result(
                f'https://www.dailymotion.com/video/{dm_id}', DailymotionIE, dm_id)
        if yt_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={yt_id}', YoutubeIE, yt_id)

        raise ExtractorError('No Dailymotion or YouTube video found', expected=True)

    def _real_extract(self, url):
        display_id = self._match_id(url).rstrip('/')

        if display_id == 'en-vivo':
            live = self._download_json(
                'https://www.imagentv.com/api/v2/application/livestreaming',
                display_id, query={'device': 'web'})
            return self._extract_host_result(
                traverse_obj(live, ('video', {dict})) or live)

        webpage = self._download_webpage(url, display_id)
        settings = self._search_json(
            r'jQuery\.extend\(Drupal\.settings\s*,', webpage,
            'drupal settings', display_id, end_pattern=r'\);', fatal=False)
        item = traverse_obj(settings, ('itv_content_result', 'items', {dict})) or {}
        return self._extract_host_result(item, webpage)
