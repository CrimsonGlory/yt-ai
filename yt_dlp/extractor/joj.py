import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    format_field,
    int_or_none,
    js_to_json,
    try_get,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class JojIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:
                        joj:|
                        https?://media\.joj\.sk/embed/|
                        https?://play\.joj\.sk/(?:videos|player)/
                    )
                    (?P<id>[^/?#^]+)
                '''
    _EMBED_REGEX = [r'<iframe\b[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//media\.joj\.sk/embed/(?:(?!\1).)+)\1']
    _TESTS = [{
        'url': 'https://play.joj.sk/videos/jBwogmVECP3LppXbdfLE',
        'skip': 'site unavailable',
        'md5': '553f89bd753c7c00bb6fb7181f97d55a',
        'info_dict': {
            'id': 'jBwogmVECP3LppXbdfLE',
            'ext': 'mp4',
            'title': 'Play-On: Nitra vs. Košice (3. Finálový zápas)',
            'description': 'Sleduj priamy prenos finále hokejovej extraligy spolu s Borisom Valábikom a Mariánom Gáborikom v novom unikátnom formáte! Iba na JOJ PLAY! Vysielanie sa začne 5 minút pred začiatkom zápasu. Verzia live.',
            'duration': 5,
            'thumbnail': r're:https?://.+',
        },
    }, {
        'url': 'https://media.joj.sk/embed/a388ec4c-6019-4a4a-9312-b1bee194e932',
        'skip': 'Cloudflare managed challenge',
        'info_dict': {
            'id': 'a388ec4c-6019-4a4a-9312-b1bee194e932',
            'ext': 'mp4',
            'title': 'NOVÉ BÝVANIE',
            'duration': 3118,
            'thumbnail': r're:https?://img\.joj\.sk/.+',
        },
    }, {
        'url': 'https://media.joj.sk/embed/CSM0Na0l0p1',
        'skip': 'Cloudflare managed challenge',
        'info_dict': {
            'id': 'CSM0Na0l0p1',
            'ext': 'mp4',
            'title': 'Extrémne rodiny 2 - POKRAČOVANIE (2012/04/09 21:30:00)',
            'duration': 3937,
            'thumbnail': r're:https?://img\.joj\.sk/.+',
        },
    }, {
        'url': 'https://media.joj.sk/embed/9i1cxv',
        'only_matching': True,
    }, {
        'url': 'https://play.joj.sk/player/jBwogmVECP3LppXbdfLE',
        'only_matching': True,
    }, {
        'url': 'joj:a388ec4c-6019-4a4a-9312-b1bee194e932',
        'only_matching': True,
    }, {
        'url': 'joj:9i1cxv',
        'only_matching': True,
    }]
    _WEBPAGE_TESTS = [{
        # FIXME: Embed detection
        'url': 'https://www.noviny.sk/slovensko/238543-slovenskom-sa-prehnala-vlna-silnych-burok',
        'skip': 'Cloudflare managed challenge',
        'info_dict': {
            'id': '238543-slovenskom-sa-prehnala-vlna-silnych-burok',
            'title': 'Slovenskom sa prehnala vlna silných búrok',
        },
        'playlist_mincount': 5,
    }]

    def _extract_play(self, video_id):
        webpage = self._download_webpage(
            f'https://play.joj.sk/videos/{video_id}', video_id, fatal=False)
        video_doc = self._download_json(
            f'https://firestore.googleapis.com/v1/projects/tivio-production/databases/(default)/documents/videos/{video_id}',
            video_id, note='Downloading video metadata', fatal=False)
        fields = traverse_obj(video_doc, ('fields', {dict})) or {}

        source = self._download_json(
            'https://europe-west3-tivio-production.cloudfunctions.net/getSourceUrl',
            video_id, note='Downloading source URL',
            data=json.dumps({
                'data': {
                    'id': video_id,
                    'documentType': 'video',
                    'capabilities': [{
                        'codec': 'h264',
                        'protocol': 'hls',
                        'encryption': 'none',
                    }],
                },
            }).encode(),
            headers={'Content-Type': 'application/json'})
        source_url = traverse_obj(source, ('result', 'url', {url_or_none}))
        if not source_url:
            raise ExtractorError(
                traverse_obj(source, ('error', 'message', {str})) or 'No playable source',
                expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            source_url, video_id, 'mp4', m3u8_id='hls')

        return {
            'id': video_id,
            'title': (
                (self._og_search_title(webpage) if webpage else None)
                or traverse_obj(fields, ('name', 'mapValue', 'fields', 'sk', 'stringValue', {str}))
                or traverse_obj(fields, ('defaultName', 'stringValue', {str}))),
            'description': (
                (self._og_search_description(webpage) if webpage else None)
                or traverse_obj(fields, ('description', 'mapValue', 'fields', 'sk', 'stringValue', {str}))),
            'thumbnail': (
                (self._og_search_thumbnail(webpage) if webpage else None)
                or traverse_obj(fields, (
                    'assets', 'mapValue', 'fields', 'cover', 'mapValue', 'fields',
                    '@1', 'mapValue', 'fields', 'background', 'stringValue', {url_or_none}))),
            'duration': int_or_none(
                traverse_obj(fields, ('duration', 'integerValue')), scale=1000),
            'formats': formats,
            'subtitles': subtitles,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if 'play.joj.sk' in url:
            return self._extract_play(video_id)

        webpage = self._download_webpage(
            f'https://media.joj.sk/embed/{video_id}', video_id)

        title = (self._search_json(r'videoTitle\s*:', webpage, 'title', video_id,
                                   contains_pattern=r'["\'].+["\']', default=None)
                 or self._html_extract_title(webpage, default=None)
                 or self._og_search_title(webpage))

        bitrates = self._parse_json(
            self._search_regex(
                r'(?s)(?:src|bitrates)\s*=\s*({.+?});', webpage, 'bitrates',
                default='{}'),
            video_id, transform_source=js_to_json, fatal=False)

        formats = []
        for format_url in try_get(bitrates, lambda x: x['mp4'], list) or []:
            if isinstance(format_url, str):
                height = self._search_regex(
                    r'(\d+)[pP]|(pal)\.', format_url, 'height', default=None)
                if height == 'pal':
                    height = 576
                formats.append({
                    'url': format_url,
                    'format_id': format_field(height, None, '%sp'),
                    'height': int_or_none(height),
                })
        if not formats:
            playlist = self._download_xml(
                f'https://media.joj.sk/services/Video.php?clip={video_id}',
                video_id)
            for file_el in playlist.findall('./files/file'):
                path = file_el.get('path')
                if not path:
                    continue
                format_id = file_el.get('id') or file_el.get('label')
                formats.append({
                    'url': 'http://n16.joj.sk/storage/{}'.format(path.replace(
                        'dat/', '', 1)),
                    'format_id': format_id,
                    'height': int_or_none(self._search_regex(
                        r'(\d+)[pP]', format_id or path, 'height',
                        default=None)),
                })

        thumbnail = self._og_search_thumbnail(webpage)

        duration = int_or_none(self._search_regex(
            r'videoDuration\s*:\s*(\d+)', webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
