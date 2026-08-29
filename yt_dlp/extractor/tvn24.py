from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    unescapeHTML,
    url_or_none,
)


class TVN24IE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:(?!eurosport)[^/]+\.)?tvn24(?:bis)?\.pl/(?:[^/?#]+/)*(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://tvn24.pl/najnowsze/radoslaw-piesiewicz-doprowadzony-do-sadu-relacja-jerzego-korczynskiego-vd9211480',
        'md5': 'e73298468e652f262eb9ee8f552d9deb',
        'info_dict': {
            'id': '9211480',
            'ext': 'mp4',
            'title': 'Radosław Piesiewicz doprowadzony do sądu. Relacja Jerzego Korczyńskiego',
            'description': 'Radosław Piesiewicz doprowadzony do sądu. Relacja Jerzego Korczyńskiego',
            'thumbnail': r're:https?://.*',
            'duration': 207,
            'timestamp': 1787951672,
            'upload_date': '20260828',
        },
    }, {
        'url': 'http://www.tvn24.pl/wiadomosci-z-kraju,3/oredzie-artura-andrusa,702428.html',
        'skip': 'video gone',
        'md5': 'fbdec753d7bc29d96036808275f2130c',
        'info_dict': {
            'id': '1584444',
            'ext': 'mp4',
            'title': '"Święta mają być wesołe, dlatego, ludziska, wszyscy pod jemiołę"',
            'description': 'Wyjątkowe orędzie Artura Andrusa, jednego z gości Szkła kontaktowego.',
            'thumbnail': 're:https?://.*[.]jpeg',
        },
    }, {
        # different layout
        'url': 'https://tvnmeteo.tvn24.pl/magazyny/maja-w-ogrodzie,13/odcinki-online,1,4,1,0/pnacza-ptaki-i-iglaki-odc-691-hgtv-odc-29,1771763.html',
        'skip': 'video gone',
        'info_dict': {
            'id': '1771763',
            'ext': 'mp4',
            'title': 'Pnącza, ptaki i iglaki (odc. 691 /HGTV odc. 29)',
            'thumbnail': 're:https?://.*',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://fakty.tvn24.pl/ogladaj-online,60/53-konferencja-bezpieczenstwa-w-monachium,716431.html',
        'only_matching': True,
    }, {
        'url': 'http://sport.tvn24.pl/pilka-nozna,105/ligue-1-kamil-glik-rozcial-glowe-monaco-tylko-remisuje-z-bastia,716522.html',
        'only_matching': True,
    }, {
        'url': 'http://tvn24bis.pl/poranek,146,m/gen-koziej-w-tvn24-bis-wracamy-do-czasow-zimnej-wojny,715660.html',
        'only_matching': True,
    }, {
        'url': 'https://www.tvn24.pl/magazyn-tvn24/angie-w-jednej-czwartej-polka-od-szarej-myszki-do-cesarzowej-europy,119,2158',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        def extract_json(attr, name, default=None, fatal=False):
            return self._parse_json(
                self._search_regex(
                    rf'\b{attr}=(["\'])(?P<json>(?!\1).+?)\1', webpage,
                    name, group='json', default=default, fatal=fatal) or '{}',
                display_id, transform_source=unescapeHTML, fatal=fatal)

        def iter_video_objects(obj):
            if isinstance(obj, dict):
                types = obj.get('@type')
                if types == 'VideoObject' or (isinstance(types, list) and 'VideoObject' in types):
                    yield obj
                for value in obj.values():
                    yield from iter_video_objects(value)
            elif isinstance(obj, list):
                for value in obj:
                    yield from iter_video_objects(value)

        formats = []
        quality_data = extract_json('data-quality', 'formats')
        if isinstance(quality_data, dict):
            for format_id, format_url in quality_data.items():
                if not url_or_none(format_url):
                    continue
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'height': int_or_none(str(format_id).rstrip('p')),
                })

        json_ld = self._search_json_ld(
            webpage, display_id, expected_type='VideoObject', default={})
        if not url_or_none(json_ld.get('url')):
            for video_obj in iter_video_objects(list(self._yield_json_ld(
                    webpage, display_id, default=[]))):
                json_ld = self._json_ld(video_obj, display_id, expected_type='VideoObject')
                if url_or_none(json_ld.get('url')):
                    break

        media_url = url_or_none(json_ld.get('url'))
        if media_url and not formats:
            if determine_ext(media_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, display_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append({'url': media_url})

        share_params = extract_json('data-share-params', 'share params')
        video_id = None
        if isinstance(share_params, dict):
            video_id = share_params.get('id')
        if not video_id:
            video_id = self._search_regex(
                r'vd(\d+)', display_id, 'video id', default=None) or self._search_regex(
                r'data-vid-id=["\'](\d+)', webpage, 'video id',
                default=None) or self._search_regex(
                r',(\d+)\.html', url, 'video id', default=None) or self._search_regex(
                r'(?:st|vc)(\d+)', display_id, 'video id', default=display_id)

        title = (
            json_ld.get('title')
            or self._og_search_title(webpage, default=None)
            or self._search_regex(
                r'<h\d+[^>]+class=["\']magazineItemHeader[^>]+>(.+?)</h',
                webpage, 'title'))

        description = json_ld.get('description') or self._og_search_description(
            webpage, default=None)
        thumbnail = (
            json_ld.get('thumbnail')
            or self._og_search_thumbnail(webpage, default=None)
            or self._html_search_regex(
                r'\bdata-poster=(["\'])(?P<url>(?!\1).+?)\1', webpage,
                'thumbnail', group='url', default=None))
        if not thumbnail:
            thumbs = json_ld.get('thumbnails') or []
            if thumbs and isinstance(thumbs[0], dict):
                thumbnail = thumbs[0].get('url')
            elif thumbs and isinstance(thumbs[0], str):
                thumbnail = thumbs[0]

        return {
            'id': str(video_id),
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': json_ld.get('duration'),
            'timestamp': json_ld.get('timestamp'),
            'formats': formats,
        }
