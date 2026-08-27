from .common import InfoExtractor
from ..utils import strip_jsonp, unified_strdate, url_or_none


class ElPaisIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^.]+\.)?elpais\.com/.*/(?P<id>[^/#?]+)\.html(?:$|[?#])'
    IE_DESC = 'El País'

    _TESTS = [{
        'url': 'http://elcomidista.elpais.com/elcomidista/2016/02/24/articulo/1456340311_668921.html#?id_externo_nwl=newsletter_diaria20160303t',
        'md5': '4e79ac0d710eabf4c311e70d26d21612',
        'info_dict': {
            'id': '1456340311_668921',
            'ext': 'mp4',
            'title': 'Cómo hacer el mejor café con cafetera italiana',
            'description': 'Que sí, que las cápsulas son cómodas. Pero si le pides algo más a la vida, quizá deberías aprender a usar bien la cafetera italiana. No tienes más que ver este vídeo y seguir sus siete normas básicas.',
            'upload_date': '20160303',
            'timestamp': 1456988735,
            'duration': 88,
            'thumbnail': r're:https?://.*',
        },
    }, {
        'url': 'http://blogs.elpais.com/la-voz-de-inaki/2014/02/tiempo-nuevo-recetas-viejas.html',
        'md5': '98406f301f19562170ec071b83433d55',
        'info_dict': {
            'id': 'tiempo-nuevo-recetas-viejas',
            'ext': 'mp4',
            'title': 'Tiempo nuevo, recetas viejas',
            'description': 'De lunes a viernes, a partir de las ocho de la mañana, Iñaki Gabilondo nos cuenta su visión de la actualidad nacional e internacional.',
            'upload_date': '20140206',
        },
        'skip': 'This blog post is no longer available',
    }, {
        'url': 'http://elpais.com/elpais/2017/01/26/ciencia/1485456786_417876.html',
        'md5': 'cd8cba33f974f69ed82df788ad43eef8',
        'info_dict': {
            'id': '1485456786_417876',
            'ext': 'mp4',
            'title': 'Hallado un barco de la antigua Roma que naufragó en Baleares hace 1.800 años',
            'description': 'La nave portaba cientos de ánforas y se hundió cerca de la isla de Cabrera por razones desconocidas',
            'upload_date': '20170127',
            'timestamp': 1485523831,
            'thumbnail': r're:https?://.*',
        },
    }, {
        'url': 'http://epv.elpais.com/epv/2017/02/14/programa_la_voz_de_inaki/1487062137_075943.html',
        'info_dict': {
            'id': '1487062137_075943',
            'ext': 'mp4',
            'title': 'Disyuntivas',
            'description': 'Dudas en los partidos políticos tras los fastos congresuales: Podemos tiene que optar entre integrar o depurar. Ambas salidas tienen riesgos',
            'upload_date': '20170214',
            'timestamp': 1487062127,
            'thumbnail': r're:https?://.*',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Current pages expose the media URL in schema.org VideoObject JSON-LD.
        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        # encodingFormat is often advertised as video/mpeg for actual MP4 files.
        json_ld.pop('ext', None)
        video_url = url_or_none(json_ld.get('url'))
        thumbnail = None
        title = json_ld.get('title')
        upload_date = None

        if not video_url:
            yt_id = self._search_regex(
                r'(?:youtube\.com/embed/|youtube\.com/watch\?v=)([\w-]{11})',
                webpage, 'youtube id', default=None)
            if yt_id:
                return self.url_result(
                    f'https://www.youtube.com/watch?v={yt_id}', ie='Youtube', video_id=yt_id)

            prefix = self._html_search_regex(
                r'var\s+url_cache\s*=\s*"([^"]+)";', webpage, 'URL prefix')
            id_multimedia = self._search_regex(
                r"id_multimedia\s*=\s*'([^']+)'", webpage, 'ID multimedia', default=None)
            if id_multimedia:
                url_info = self._download_json(
                    'http://elpais.com/vdpep/1/?pepid=' + id_multimedia, video_id, transform_source=strip_jsonp)
                video_suffix = url_info['mp4']
            else:
                video_suffix = self._search_regex(
                    r"(?:URLMediaFile|urlVideo_\d+)\s*=\s*url_cache\s*\+\s*'([^']+)'", webpage, 'video URL')
            video_url = prefix + video_suffix
            thumbnail_suffix = self._search_regex(
                r"(?:URLMediaStill|urlFotogramaFijo_\d+)\s*=\s*url_cache\s*\+\s*'([^']+)'",
                webpage, 'thumbnail URL', default=None)
            if thumbnail_suffix:
                thumbnail = prefix + thumbnail_suffix
            title = title or self._html_search_regex(
                (r"tituloVideo\s*=\s*'([^']+)'",
                 r'<h2 class="entry-header entry-title.*?>(.*?)</h2>',
                 r'<h1[^>]+class="titulo"[^>]*>([^<]+)'),
                webpage, 'title', default=None)
            upload_date = unified_strdate(self._search_regex(
                r'<p class="date-header date-int updated"\s+title="([^"]+)">',
                webpage, 'upload date', default=None) or self._html_search_meta(
                'datePublished', webpage, 'timestamp'))

        return {
            'id': video_id,
            'url': video_url,
            'title': title or self._og_search_title(webpage),
            'description': self._og_search_description(webpage) or json_ld.get('description'),
            'thumbnail': thumbnail or self._og_search_thumbnail(webpage),
            'timestamp': json_ld.get('timestamp'),
            'duration': json_ld.get('duration'),
            'upload_date': upload_date,
        }
