import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    extract_attributes,
    int_or_none,
    url_or_none,
    urljoin,
)


class AnimationFilmArchivesIE(InfoExtractor):
    IE_NAME = 'animationfilmarchives'
    IE_DESC = 'Japanese Animated Film Classics'
    _VALID_URL = r'https?://(?:www\.)?animation\.filmarchives\.jp/(?:en/)?works/(?P<kind>playen|play|view)/(?P<id>\d+)'
    _PLAYER_IFRAME_RE = r'<iframe[^>]+src=["\']((?:https?:)?//h10\.cs\.nii\.ac\.jp/view\d*/video_view\.php\?[^"\']+)'
    _TESTS = [{
        'url': 'https://animation.filmarchives.jp/en/works/playen/41061',
        'md5': '19d28e6d103fb19221774f17905de41c',
        'info_dict': {
            'id': '41061_en',
            'ext': 'mp4',
            'title': 'The Story of the Monkey King',
            'description': 'The Story of the Monkey King (The Story of the Monkey King) Prod. Year : 1926  Dir. : Noburo Ofuji。The monk Xuanzang embarks on a journey in search of sacred scriptures. Sun Wukong, the mischievous Monkey King, becomes his disciple and joins him on his journey to the faraway land of India.',
            'thumbnail': r're:https?://h10\.cs\.nii\.ac\.jp/.+/poster\.png',
            'release_year': 1926,
            'uploader': 'The National Museum of Modern Art, Tokyo.',
            'creators': ['Noburo Ofuji'],
        },
        'params': {'format': 'best[protocol=m3u8_native]'},
    }, {
        'url': 'https://animation.filmarchives.jp/works/play/41061',
        'only_matching': True,
    }, {
        'url': 'https://animation.filmarchives.jp/en/works/play/5141',
        'only_matching': True,
    }, {
        'url': 'https://animation.filmarchives.jp/en/works/view/41061',
        'only_matching': True,
    }]

    @staticmethod
    def _sibling_manifest(src):
        if '/dash/' in src and src.endswith('.mpd'):
            return src.replace('/dash/', '/hls/').replace('.mpd', '.m3u8')
        if '/hls/' in src and src.endswith('.m3u8'):
            return src.replace('/hls/', '/dash/').replace('.m3u8', '.mpd')
        return None

    def _extract_nii_formats(self, player_url, video_id):
        player = self._download_webpage(
            player_url, video_id, note='Downloading NII player')
        source_urls = []
        for tag in re.findall(r'<source[^>]+>', player, flags=re.DOTALL):
            src = extract_attributes(tag).get('src')
            if not src:
                continue
            src = url_or_none(re.sub(r'\s+', '', src))
            if src:
                source_urls.append(src)
        preferred = [src for src in source_urls if '/auto/' in src] or source_urls
        manifest_urls, seen_src = [], set()
        for src in preferred:
            for url in (src, self._sibling_manifest(src)):
                if url and url not in seen_src:
                    seen_src.add(url)
                    manifest_urls.append(url)

        formats, subtitles = [], {}
        for src in manifest_urls:
            ext = determine_ext(src)
            if ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    src, video_id, mpd_id='dash', fatal=False)
            elif ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', m3u8_id='hls', fatal=False)
            else:
                fmts, subs = [{'url': src}], {}
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        thumbnail = url_or_none(self._search_regex(
            r'\bposter=(["\'])(?P<url>https?://[^"\']+)\1',
            player, 'thumbnail', default=None, group='url'))
        return formats, subtitles, thumbnail

    def _real_extract(self, url):
        kind, video_id = self._match_valid_url(url).group('kind', 'id')
        webpage = self._download_webpage(url, video_id)

        if kind == 'view':
            play_path = self._search_regex(
                r'(/(?:en/)?works/play(?:en)?/\d+)', webpage, 'play page')
            return self.url_result(urljoin(url, play_path), ie=self.ie_key())

        player_src = self._search_regex(
            self._PLAYER_IFRAME_RE, webpage, 'NII player iframe', default=None)
        player_url = urljoin(url, player_src) if player_src else None
        if not player_url:
            raise ExtractorError('No NII video player found', expected=True)

        formats, subtitles, thumbnail = self._extract_nii_formats(player_url, video_id)
        if not formats:
            raise ExtractorError('No video source found', expected=True)

        track = 'en' if kind == 'playen' else 'jp'
        credit = self._html_search_regex(
            r'<p[^>]+class="video-heading-en"[^>]*>([^<]+)',
            webpage, 'credit', default='') or ''
        creator = self._search_regex(
            r'^\s*(.+?)\s+\d{4}', credit, 'creator', default=None)

        return {
            'id': f'{video_id}_{track}',
            'title': (
                self._html_search_regex(
                    r'<h1[^>]+class="[^"]*video-heading[^"]*"[^>]*>([^<]+)',
                    webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)
                or self._html_extract_title(webpage)),
            'description': (
                self._og_search_description(webpage, default=None)
                or self._html_search_meta('description', webpage, default=None)),
            'thumbnail': thumbnail or self._og_search_thumbnail(webpage, default=None),
            'release_year': int_or_none(self._search_regex(
                r'(\d{4})', credit, 'release year', default=None)),
            'uploader': self._html_search_meta('copyright', webpage, default=None),
            'creators': [creator] if creator else None,
            'formats': formats,
            'subtitles': subtitles,
        }
