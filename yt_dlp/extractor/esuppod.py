import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    get_element_by_class,
    int_or_none,
    js_to_json,
    mimetype2ext,
    parse_duration,
    parse_iso8601,
    unescapeHTML,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class EsupPodIE(InfoExtractor):
    IE_NAME = 'esuppod'
    IE_DESC = 'Esup-Pod (Université de Lille)'
    _VALID_URL = r'https?://(?:www\.)?pod\.univ-lille\.fr/video/(?P<id>\d+)(?:-[^/?#]*)?/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://pod.univ-lille.fr/video/43211-webinaire-repenser-ses-pratiques-pedagogiques-et-ses-methodes-devaluation-au-temps-de-lintelligence-artificielle/',
        'md5': '4e43a0ff25c4649ae05486ce277d54b0',
        'info_dict': {
            'id': '43211',
            'ext': 'mp4',
            'title': 'Webinaire Repenser ses pratiques pédagogiques et ses méthodes d\'évaluation au temps de l’intelligence artificielle.',
            'description': 'md5:abf1611d15e7db69cf8b9f8cf5108d4c',
            'duration': 5306,
            'timestamp': 1752071281,
            'upload_date': '20250709',
            'thumbnail': r're:https://pod\.univ-lille\.fr/media/cache/.+',
            'uploader': 'Emmanuel Pasian',
            'view_count': int,
            'chapters': 'count:12',
        },
    }, {
        'url': 'https://pod.univ-lille.fr/video/43211-webinaire-repenser-ses-pratiques-pedagogiques-et-ses-methodes-devaluation-au-temps-de-lintelligence-artificielle/?is_iframe=true',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        formats = []
        for source in self._search_json(
            r'const mp4_sources\s*=', webpage, 'mp4 sources', video_id,
            contains_pattern=r'\[(?s:.+?)\]', end_pattern=r';',
            default=[], transform_source=js_to_json,
        ):
            src_path = traverse_obj(source, ('src', {str}))
            src = url_or_none(urljoin(url, src_path)) if src_path else None
            if not src:
                continue
            height = int_or_none(traverse_obj(source, 'height'))
            ext = (traverse_obj(source, ('extension', {str})) or '').lstrip('.') or mimetype2ext(
                traverse_obj(source, 'type')) or 'mp4'
            formats.append({
                'url': src,
                'ext': ext,
                'format_id': traverse_obj(source, ('label', {str})) or (f'{height}p' if height else None),
                'height': height,
                'vcodec': 'none' if ext in ('mp3', 'm4a', 'ogg') else None,
            })

        subtitles = {}
        if not formats:
            hls_path = self._search_regex(
                r'const srcOptions\s*=\s*\{[^}]*?\bsrc:\s*[\'"]([^\'"]+)',
                webpage, 'hls url', default=None)
            hls_src = url_or_none(urljoin(url, hls_path)) if hls_path else None
            if hls_src:
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    hls_src, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)

        if not formats:
            raise ExtractorError('No video sources found', expected=True)

        duration = parse_duration(self._html_search_meta(
            'duration', webpage, default=None)) or parse_duration(self._html_search_regex(
            r'class="video-info__duration"[^>]*>.*?</span>\s*([0-9:]+)',
            webpage, 'duration', default=None, flags=re.DOTALL))
        poster = self._search_regex(
            r'<video[^>]+id="podvideoplayer"[^>]+poster=(["\'])(?P<poster>(?:(?!\1).)+)\1',
            webpage, 'poster', default=None, group='poster')

        return {
            'id': video_id,
            'title': (self._og_search_title(webpage, default=None)
                      or self._html_search_regex(
                          r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                      or self._html_extract_title(webpage)),
            'description': (clean_html(get_element_by_class('pod-video-description', webpage))
                            or self._og_search_description(webpage)),
            'thumbnail': url_or_none(urljoin(url, unescapeHTML(poster))) if poster else None,
            'duration': duration,
            'timestamp': parse_iso8601(self._html_search_meta('uploadDate', webpage, default=None)),
            'uploader': self._html_search_regex(
                r'class="pod-meta-title">[^<]+</span>\s*([^<(]+)',
                webpage, 'uploader', default=None),
            'view_count': int_or_none(self._search_regex(
                r'class="pod-info-video__view"[^>]*>.*?<a[^>]*>\s*(\d+)',
                webpage, 'view count', default=None, flags=re.DOTALL)),
            'chapters': [{
                'start_time': int(start),
                'title': unescapeHTML(title),
            } for start, title in re.findall(
                r'data-start="(\d+)"[^>]*data-title="([^"]*)"', webpage)] or None,
            'formats': formats,
            'subtitles': subtitles,
        }
