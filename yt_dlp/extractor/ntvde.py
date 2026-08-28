from .common import InfoExtractor
from ..utils import (
    int_or_none,
    strip_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class NTVDeIE(InfoExtractor):
    IE_NAME = 'n-tv.de'
    _VALID_URL = r'https?://(?:www\.)?n-tv\.de/mediathek/(?:videos|magazine)/[^/?#]+/[^/?#]+-(?:article|id)(?P<id>\d+)\.html'
    _GEO_COUNTRIES = ['DE']
    _HEADERS = {'Referer': 'https://www.n-tv.de/'}

    _TESTS = [{
        'url': 'https://www.n-tv.de/mediathek/videos/technik/OpenAI-stoppt-Astra-wegen-moeglicher-Cyber-Gefahr-KI-koennte-selbststaendig-zuschlagen-id31172518.html',
        'info_dict': {
            'id': '31172518',
            'ext': 'mp4',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg|webp)',
            'title': 'OpenAI stoppt "Astra" wegen möglicher Cyber-Gefahr',
            'alt_title': 'KI könnte selbstständig zuschlagen',
            'description': 'Inzwischen häufen sich Vorfälle, bei denen KI eigenständig Sicherheitslücken in fremden Programmen findet und diese für Hacks ausnutzt. OpenAI gibt jetzt bekannt, das Modell "Astra" künftig in einem abgeschotteten Umfeld weitergetestet wird.',
            'duration': 90,
            'timestamp': 1786188600,
            'upload_date': '20260808',
        },
        'skip': 'CloudFront geo-restricted to Germany; streaming.n-tv.de / bot-cf.n-tv.de return HTTP 403 outside DE (X-Forwarded-For is ignored)',
    }, {
        'url': 'http://www.n-tv.de/mediathek/videos/panorama/Schnee-und-Glaette-fuehren-zu-zahlreichen-Unfaellen-und-Staus-article14438086.html',
        'info_dict': {
            'id': '14438086',
            'ext': 'mp4',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg|webp)',
            'title': 'Schnee und Glätte führen zu zahlreichen Unfällen und Staus',
            'alt_title': 'Winterchaos auf deutschen Straßen',
            'description': 'Schnee und Glätte sorgen deutschlandweit für einen chaotischen Start in die Woche: Auf den Straßen kommt es zu kilometerlangen Staus und Dutzenden Glätteunfällen. In Düsseldorf und München wirbelt der Schnee zudem den Flugplan durcheinander. Dutzende Flüge landen zu spät, einige fallen ganz aus.',
            'duration': 67,
            'timestamp': 1422892797,
            'upload_date': '20150202',
        },
        'skip': 'CloudFront geo-restricted to Germany; streaming.n-tv.de / bot-cf.n-tv.de return HTTP 403 outside DE (X-Forwarded-For is ignored)',
    }, {
        'url': 'https://www.n-tv.de/mediathek/magazine/auslandsreport/Juedische-Siedler-wollten-Rache-die-wollten-nur-toeten-article24523089.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        areas = traverse_obj(
            self._search_nextjs_data(webpage, video_id),
            ('props', 'pageProps', 'resp', 'data', 'areas', {dict}))
        article = traverse_obj(areas, ('meta', ..., 'model', 'article', {dict}), get_all=False) or {}
        video_model = traverse_obj(areas, (
            'main', ..., 'items',
            lambda _, v: isinstance(traverse_obj(v, ('model', 'video')), dict),
            'model', {dict}), get_all=False) or {}
        vdata = video_model.get('video') or {}

        formats = []
        added = set()
        for format_id, key in (
            ('http', 'botUrl'),
            ('http-prog', 'web-prog'),
            ('http-mp4', 'mp4'),
        ):
            media_url = url_or_none(vdata.get(key))
            if media_url and media_url not in added:
                added.add(media_url)
                formats.append({
                    'format_id': format_id,
                    'url': media_url,
                    'http_headers': self._HEADERS,
                })
        hls = url_or_none(vdata.get('web-hls') or vdata.get('ios'))
        if hls:
            formats.extend(self._extract_m3u8_formats(
                hls, video_id, 'mp4', m3u8_id='hls', fatal=False, headers=self._HEADERS))
        dash = url_or_none(vdata.get('web-dash') or vdata.get('android-dash'))
        if dash:
            formats.extend(self._extract_mpd_formats(
                dash, video_id, fatal=False, mpd_id='dash', headers=self._HEADERS))

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            **traverse_obj(video_model, {
                'title': (('headline', 'title'), {strip_or_none}),
                'alt_title': ('kicker', {strip_or_none}),
                'description': ('leadtext', {strip_or_none}),
                'thumbnail': ('image', 'defaultUrl', {url_or_none}),
                'duration': ('durationMillis', {lambda x: int_or_none(x, scale=1000)}),
                'timestamp': ('publishedAt', {unified_timestamp}),
            }),
            **traverse_obj(article, {
                'title': ('headline', {strip_or_none}),
                'alt_title': ('kicker', {strip_or_none}),
                'description': ('leadtext', {strip_or_none}),
                'timestamp': ('publishedAt', {unified_timestamp}),
            }),
            'formats': formats,
        }
