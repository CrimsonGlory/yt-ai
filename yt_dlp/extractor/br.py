from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    join_nonempty,
    mimetype2ext,
    unified_strdate,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class BRIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'Bayerischer Rundfunk'
    _GEO_COUNTRIES = ['DE']
    _VALID_URL = r'https?://(?:www\.)?br(?:-klassik)?\.de/(?:[a-z0-9\-_]+/)+(?P<id>[a-z0-9\-_]+)\.html'

    _TESTS = [{
        'url': 'http://www.br.de/mediathek/video/sendungen/abendschau/betriebliche-altersvorsorge-104.html',
        'md5': '83a0477cf0b8451027eb566d88b51106',
        'info_dict': {
            'id': '48f656ef-287e-486f-be86-459122db22cc',
            'ext': 'mp4',
            'title': 'Die böse Überraschung',
            'description': 'md5:ce9ac81b466ce775b8018f6801b48ac9',
            'duration': 180,
            'uploader': 'Reinhard Weber',
            'upload_date': '20150422',
        },
        'skip': '404 not found',
    }, {
        'url': 'http://www.br.de/nachrichten/oberbayern/inhalt/muenchner-polizeipraesident-schreiber-gestorben-100.html',
        'md5': 'af3a3a4aa43ff0ce6a89504c67f427ef',
        'info_dict': {
            'id': 'a4b83e34-123d-4b81-9f4e-c0d3121a4e05',
            'ext': 'flv',
            'title': 'Manfred Schreiber ist tot',
            'description': 'md5:b454d867f2a9fc524ebe88c3f5092d97',
            'duration': 26,
        },
        'skip': '404 not found',
    }, {
        'url': 'https://www.br-klassik.de/audio/peeping-tom-premierenkritik-dance-festival-muenchen-100.html',
        'md5': '8b5b27c0b090f3b35eac4ab3f7a73d3d',
        'info_dict': {
            'id': '74c603c9-26d3-48bb-b85b-079aeed66e0b',
            'ext': 'aac',
            'title': 'Kurzweilig und sehr bewegend',
            'description': 'md5:0351996e3283d64adeb38ede91fac54e',
            'duration': 296,
        },
        'skip': '404 not found',
    }, {
        'url': 'http://www.br.de/radio/bayern1/service/team/videos/team-video-erdelt100.html',
        'md5': 'dbab0aef2e047060ea7a21fc1ce1078a',
        'info_dict': {
            'id': '6ba73750-d405-45d3-861d-1ce8c524e059',
            'display_id': 'team-video-erdelt100',
            'ext': 'mp4',
            'title': 'Umweltbewusster Häuslebauer',
            'description': 'md5:d52dae9792d00226348c1dbb13c9bae2',
            'duration': 116,
            'thumbnail': r're:https?://www\.br\.de/.+\.jpg',
            'uploader': 'Uwe Erdelt, Udine Fraatz, Bayerischer Rundfunk',
            'upload_date': '20090807',
            'channel': 'Bayern 1',
            'series': 'Uwe Erdelt',
        },
        'params': {'format': 'best[protocol=https]'},
    }, {
        'url': 'http://www.br.de/nachrichten/index.html',
        'skip': 'video gone',
        'md5': '23bca295f1650d698f94fc570977dae3',
        'info_dict': {
            'id': 'index',
            'ext': 'mp4',
            'title': 'Folge 1 - Metaphysik',
            'description': 'md5:bb659990e9e59905c3d41e369db1fbe3',
            'duration': 893,
            'uploader': 'Eva Maria Steimle',
            'upload_date': '20170208',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        media_info_path = self._search_regex(
            r'(["\'])(?P<url>(?:https?:)?(?://[^/]+)?/[^"\']+~mediaInfo\.json(?:\?[^"\']*)?)\1',
            webpage, 'media info URL', group='url')
        media_info = self._download_json(
            urljoin(url, media_info_path), display_id, 'Downloading media JSON')
        video_id = traverse_obj(media_info, ('id', {str})) or display_id
        piano = traverse_obj(
            media_info, ('pluginData', 'trackingPiano@all', 'avContent', {dict})) or {}

        formats, subtitles = [], {}
        for stream in traverse_obj(media_info, ('streams', ..., {dict})):
            is_audio = stream.get('isAudioOnly')
            for media in traverse_obj(stream, ('media', ..., {dict})):
                media_url = url_or_none(self._proto_relative_url(media.get('url')))
                if not media_url:
                    continue
                ext = determine_ext(media_url) or mimetype2ext(media.get('mimeType'))
                if ext == 'm3u8':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                    continue
                height = int_or_none(media.get('maxVResolutionPx'))
                formats.append({
                    'url': media_url,
                    'ext': ext or mimetype2ext(media.get('mimeType')),
                    'format_id': join_nonempty('http', height and f'{height}p'),
                    'width': int_or_none(media.get('maxHResolutionPx')),
                    'height': height,
                    'vcodec': 'none' if is_audio else media.get('videoCodec'),
                })

        if not formats and media_info.get('isGeoBlocked'):
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        json_ld = self._search_json_ld(webpage, display_id, default={})
        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (
                piano.get('seitentitel')
                or self._html_search_meta('DCTERMS.title', webpage, default=None)
                or traverse_obj(media_info, ('meta', ('title', 'seriesTitle'), {str}, filter, any))
                or json_ld.get('title')),
            'description': (
                media_info.get('comment')
                or json_ld.get('description')
                or self._og_search_description(webpage)),
            'duration': (
                int_or_none(traverse_obj(media_info, ('meta', 'durationSeconds')))
                or int_or_none(piano.get('av_content_duration'), scale=1000)
                or int_or_none(traverse_obj(
                    media_info, ('pluginData', 'trackingAgf@all', 'clipData', 'length')))
                or int_or_none(self._og_search_property(
                    'video:duration', webpage, default=None))),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader': self._html_search_meta('DCTERMS.creator', webpage, default=None),
            'upload_date': unified_strdate(
                piano.get('datum')
                or self._html_search_meta('DCTERMS.date', webpage, default=None)),
            'channel': piano.get('av_broadcaster'),
            'series': traverse_obj(media_info, ('meta', 'seriesTitle', {str})),
            'is_live': bool(media_info.get('live')),
        }
