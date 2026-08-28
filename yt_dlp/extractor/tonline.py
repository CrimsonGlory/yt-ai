from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    strip_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class TOnlineIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 't-online.de'
    _VALID_URL = r'https?://(?:www\.)?t-online\.de/(?:tv|video)/(?:[^/?#]+/)*id_(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.t-online.de/video/ratgeber/raetsel/id_91901180/hermann-gitter-raetsel-mit-optischer-taeuschung-fuehrt-zur-verzweiflung.html',
        'md5': 'd63989f0fd3aaa919cdea8f66d505689',
        'info_dict': {
            'id': '91901180',
            'ext': 'mp4',
            'title': 'Hermann-Gitter: Rätsel mit optischer Täuschung führt zur Verzweiflung',
            'description': 't-online fordert Sie im Video regelmäßig mit kniffligen Rätseln heraus. Halten Sie sich für ein "Superhirn"? ',
            'duration': 51,
            'timestamp': 1648209780,
            'upload_date': '20220325',
            'thumbnail': r're:https?://images\.t-online\.de/.+',
        },
    }, {
        'url': 'http://www.t-online.de/tv/sport/fussball/id_79166266/drittes-remis-zidane-es-muss-etwas-passieren-.html',
        'skip': 'video gone',
        'md5': '7d94dbdde5f9d77c5accc73c39632c29',
        'info_dict': {
            'id': '79166266',
            'ext': 'mp4',
            'title': 'Drittes Remis! Zidane: "Es muss etwas passieren"',
            'description': 'Es läuft nicht rund bei Real Madrid. Das 1:1 gegen den SD Eibar war das dritte Unentschieden in Folge in der Liga.',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video = traverse_obj(
            self._search_nextjs_data(webpage, video_id, default={}),
            ('props', 'pageProps', 'page', 'video', {dict})) or {}
        element = traverse_obj(video, ('element', {dict})) or {}

        json_ld = self._search_json_ld(webpage, video_id, default={}) or {}
        json_ld.pop('ext', None)

        stream_url = url_or_none(element.get('src')) or url_or_none(json_ld.pop('url', None))
        formats, subtitles = [], {}
        if stream_url and determine_ext(stream_url) == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id='hls')
            # CMAF renditions are single files; HLS --test only fetches the init MAP.
            for hls_fmt in list(formats):
                m3u8_url = hls_fmt.get('url') or ''
                if determine_ext(m3u8_url) != 'm3u8':
                    continue
                playlist = self._download_webpage(
                    m3u8_url, video_id, 'Downloading media playlist', fatal=False)
                map_uri = self._search_regex(
                    r'#EXT-X-MAP:URI="([^"]+)"', playlist or '', 'cmaf map', default=None)
                if not map_uri:
                    continue
                formats.append({
                    **traverse_obj(hls_fmt, {
                        'width': 'width',
                        'height': 'height',
                        'fps': 'fps',
                        'tbr': 'tbr',
                        'vcodec': 'vcodec',
                        'acodec': 'acodec',
                        'dynamic_range': 'dynamic_range',
                    }),
                    'format_id': (hls_fmt.get('format_id') or 'hls').replace('hls', 'http', 1),
                    'url': urljoin(m3u8_url, map_uri),
                    'ext': 'mp4',
                })
        elif stream_url:
            formats.append({'url': stream_url})
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        for sub in traverse_obj(element, ('subtitles', ..., {dict})):
            sub_url = url_or_none(sub.get('url'))
            if not sub_url:
                continue
            lang = sub.get('language') or 'de'
            subtitles.setdefault(lang, []).append({
                'url': sub_url,
                'name': sub.get('label'),
            })

        poster = traverse_obj(element, ('poster', 'picture', 'sources', 0, 'src', {str}))
        if poster:
            poster = poster.replace('__WIDTH__', '1200')

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles or None,
            'title': (
                json_ld.get('title')
                or strip_or_none(video.get('headlineSEO'))
                or strip_or_none(video.get('headline'))
                or video_id),
            'description': json_ld.get('description'),
            'duration': int_or_none(traverse_obj(
                element, ('content', 'duration'))) or json_ld.get('duration'),
            'timestamp': json_ld.get('timestamp'),
            'thumbnail': url_or_none(poster) or traverse_obj(
                json_ld, ('thumbnails', 0, 'url', {url_or_none})) or json_ld.get('thumbnail'),
        }
