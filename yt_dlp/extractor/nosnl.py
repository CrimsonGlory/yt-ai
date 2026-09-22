from .common import InfoExtractor
from ..utils import int_or_none, parse_duration, parse_iso8601, traverse_obj, url_or_none


class NOSNLArticleIE(InfoExtractor):
    _VALID_URL = r'https?://nos\.nl/(?P<type>video|(\w+/)?\w+)/?\d+-(?P<display_id>[\w-]+)'
    _TESTS = [
        {
            # only 1 video
            'url': 'https://nos.nl/nieuwsuur/artikel/2440353-verzakking-door-droogte-dreigt-tot-een-miljoen-kwetsbare-huizen',
            'skip': 'stale test sample / site changed',
            'info_dict': {
                'id': '2440340',
                'ext': 'mp4',
                'description': 'md5:5f83185d902ac97af3af4bed7ece3db5',
                'title': '\'We hebben een huis vol met scheuren\'',
                'duration': 95.0,
                'thumbnail': 'https://cdn.nos.nl/image/2022/08/12/887149/3840x2160a.jpg',
            },
        }, {
            # more than 1 video
            'url': 'https://nos.nl/artikel/2440409-vannacht-sliepen-weer-enkele-honderden-asielzoekers-in-ter-apel-buiten',
            'skip': 'stale test sample / site changed',
            'info_dict': {
                'id': '2440409',
                'title': 'Vannacht sliepen weer enkele honderden asielzoekers in Ter Apel buiten',
                'description': 'md5:72b1e1674d798460e79d78fa37e9f56d',
                'tags': ['aanmeldcentrum', 'Centraal Orgaan opvang asielzoekers', 'COA', 'asielzoekers', 'Ter Apel'],
                'modified_timestamp': 1660452773,
                'modified_date': '20220814',
                'upload_date': '20220813',
                'thumbnail': 'https://cdn.nos.nl/image/2022/07/18/880346/1024x576a.jpg',
                'timestamp': 1660401384,
                'categories': ['Regionaal nieuws', 'Binnenland'],
            },
            'playlist_count': 2,
        }, {
            # audio + video
            'url': 'https://nos.nl/artikel/2440789-wekdienst-16-8-groningse-acties-tien-jaar-na-zware-aardbeving-femke-bol-in-actie-op-ek-atletiek',
            'info_dict': {
                'id': '2440789',
                'title': 'Wekdienst 16/8: Groningse acties tien jaar na zware aardbeving • Femke Bol in actie op EK atletiek ',
                'description': 'md5:0bd277ed7a44fc15cb12a9d27d8f6641',
                'tags': ['wekdienst'],
                'modified_date': '20220816',
                'modified_timestamp': 1660625449,
                'timestamp': 1660625449,
                'upload_date': '20220816',
                'thumbnail': r're:https://images\.cdn\.nos\.nl/.+',
                'categories': ['Binnenland', 'Buitenland'],
            },
            'playlist_count': 2,
        }, {
            # video url
            'url': 'https://nos.nl/video/2452718-xi-en-trudeau-botsen-voor-de-camera-op-g20-top-je-hebt-gelekt',
            'skip': 'stale test sample / site changed',
            'info_dict': {
                'id': '2452718',
                'title': 'Xi en Trudeau botsen voor de camera op G20-top: \'Je hebt gelekt\'',
                'modified_date': '20221117',
                'description': 'md5:61907dac576f75c11bf8ffffd4a3cc0f',
                'tags': ['Xi', 'Trudeau', 'G20', 'indonesié'],
                'upload_date': '20221117',
                'thumbnail': 'https://cdn.nos.nl/image/2022/11/17/916155/1024x576a.jpg',
                'modified_timestamp': 1668663388,
                'timestamp': 1668663388,
                'categories': ['Buitenland'],
            },
            'playlist_mincount': 1,
        },
    ]

    def _labels(self, value):
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return traverse_obj(value, (..., 'label', {str})) or None
        return value or None

    def _iter_media(self, node):
        if isinstance(node, list):
            for child in node:
                yield from self._iter_media(child)
            return
        if not isinstance(node, dict):
            return
        kind = node.get('__typename') or node.get('type')
        if kind in ('VideoElement', 'AudioElement', 'video', 'audio'):
            yield node
            return
        for value in node.values():
            if isinstance(value, (dict, list)):
                yield from self._iter_media(value)

    def _video_url(self, item):
        source = traverse_obj(item, ('source', 'url', {url_or_none}))
        if source:
            return source
        return traverse_obj(item, (
            'videoAsset', 'formats', lambda _, v: (
                'mpegurl' in (v.get('mimetype') or '') or '.m3u8' in (v.get('url') or '')),
            'url', {url_or_none}), get_all=False)

    def _thumbnails(self, item):
        images = traverse_obj(item, ('imagesByRatio', ...))
        if images and isinstance(images[0], list):
            images = images[0]
        if not images:
            images = traverse_obj(item, ('videoAsset', 'imageAsset', 'Ratio16x9', ...)) or []
        thumbnails = []
        for image in images:
            if not isinstance(image, dict):
                continue
            url = url_or_none(image.get('url')) or traverse_obj(image, ('url', ...), get_all=False)
            if url:
                thumbnails.append({
                    'url': url,
                    'width': int_or_none(image.get('width')),
                    'height': int_or_none(image.get('height')),
                })
        return thumbnails

    def _entries(self, nodes, display_id):
        for item in self._iter_media(nodes):
            kind = item.get('__typename') or item.get('type')
            if kind in ('VideoElement', 'video'):
                video_url = self._video_url(item)
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                    video_url, display_id, ext='mp4', fatal=False) if video_url else ([], {})
                yield {
                    'id': str(item.get('id') or traverse_obj(item, ('videoAsset', 'id')) or display_id),
                    'title': item.get('title'),
                    'description': item.get('description'),
                    'formats': formats,
                    'subtitles': subtitles,
                    'duration': (
                        int_or_none(traverse_obj(item, ('videoAsset', 'durationInSeconds')))
                        or parse_duration(item.get('duration'))),
                    'thumbnails': self._thumbnails(item),
                }
            elif kind in ('AudioElement', 'audio'):
                yield {
                    'id': str(item.get('id') or traverse_obj(item, ('asset', 'id')) or display_id),
                    'title': item.get('title'),
                    'description': item.get('description'),
                    'url': traverse_obj(item, ('media', 'src'), ('asset', 'formats', ..., 'url'), get_all=False),
                    'ext': 'mp3',
                }

    def _real_extract(self, url):
        site_type, display_id = self._match_valid_url(url).group('type', 'display_id')
        if site_type != 'video' and '/video/' in url:
            site_type = 'video'
        webpage = self._download_webpage(url, display_id)

        page = self._search_nextjs_data(webpage, display_id)['props']['pageProps']
        data = page.get('data') or page.get('article') or {}
        if site_type == 'video' and isinstance(data.get('video'), dict):
            media_root = [data['video']]
        elif isinstance(data.get('items'), list):
            media_root = data['items']
        else:
            media_root = data.get('content') or []
        return {
            '_type': 'playlist',
            'entries': self._entries(media_root, display_id),
            'id': str(data['id']),
            'title': data.get('title') or self._html_search_meta(['title', 'og:title', 'twitter:title'], webpage),
            'description': (data.get('description')
                            or self._html_search_meta(['description', 'twitter:description', 'og:description'], webpage)),
            'tags': self._labels(data.get('keywords')),
            'modified_timestamp': parse_iso8601(data.get('modifiedAt')),
            'thumbnail': (
                url_or_none(data.get('shareImageSrc'))
                or traverse_obj(data, ('indexImage', 'Ratio16x9', -1, 'url', {url_or_none}))
                or self._html_search_meta(['og:image', 'twitter:image'], webpage)),
            'timestamp': parse_iso8601(data.get('publishedAt') or data.get('createdAt')),
            'categories': self._labels(data.get('categories')),
        }
