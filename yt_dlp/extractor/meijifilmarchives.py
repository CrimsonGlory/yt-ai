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


class MeijiFilmArchivesIE(InfoExtractor):
    IE_NAME = 'meijifilmarchives'
    IE_DESC = 'The Meiji Period on Film'
    _VALID_URL = r'https?://(?:www\.)?meiji\.filmarchives\.jp/(?:works|lumiere-works)/(?P<id>[\w.-]+)\.html'
    _PLAYER_IFRAME_RE = r'<iframe[^>]+src=["\']((?:https?:)?//h10\.cs\.nii\.ac\.jp/view\d*/video_view\.php\?[^"\']+)'
    _TESTS = [{
        'url': 'https://meiji.filmarchives.jp/works/01_play.html',
        'md5': 'bb59207a56ff4e4035080b98e6081227',
        'info_dict': {
            'id': '01_play',
            'ext': 'mp4',
            'title': '紅葉狩',
            'description': '歌舞伎の名優、九代目市川団十郎と五代目尾上菊五郎の至芸を記録した、現存最古の日本映画。映画フィルム初の重要文化財。',
            'thumbnail': r're:https?://h10\.cs\.nii\.ac\.jp/.+/poster\.png',
            'release_year': 1899,
            'uploader': 'National Film Archive of Japan.',
        },
        'params': {'format': 'best[protocol=m3u8_native]'},
    }, {
        'url': 'https://meiji.filmarchives.jp/lumiere-works/ML01-733.html',
        'info_dict': {
            'id': 'ML01-733',
            'ext': 'mp4',
            'title': '日本の宴会 / Dîner japonais',
            'description': '1960年にフランス政府から寄贈された、日本を撮影した最初期の映画であるフランスのリュミエール社作品29本を公開',
            'thumbnail': r're:https?://h10\.cs\.nii\.ac\.jp/.+/poster\.png',
            'release_year': 1897,
            'uploader': 'National Film Archive of Japan.',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://meiji.filmarchives.jp/works/01.html',
        'only_matching': True,
    }]

    def _player_iframe_url(self, webpage, page_url, video_id):
        iframe = self._search_regex(
            self._PLAYER_IFRAME_RE, webpage, 'NII player iframe', default=None)
        if iframe:
            return urljoin(page_url, iframe)
        play_path = self._search_regex(
            r'<a[^>]+href=["\']((?:https?://meiji\.filmarchives\.jp)?/works/[\w.-]+_play\.html)',
            webpage, 'play page', default=None)
        if not play_path:
            return None
        play_url = urljoin(page_url, play_path)
        play_page = self._download_webpage(
            play_url, video_id, note='Downloading play page')
        iframe = self._search_regex(
            self._PLAYER_IFRAME_RE, play_page, 'NII player iframe', default=None)
        return urljoin(play_url, iframe) if iframe else None

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
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_url = self._player_iframe_url(webpage, url, video_id)
        if not player_url:
            raise ExtractorError('No NII video player found', expected=True)

        formats, subtitles, thumbnail = self._extract_nii_formats(player_url, video_id)
        if not formats:
            raise ExtractorError('No video source found', expected=True)

        title = (
            self._html_search_regex(
                r'<h[12][^>]+class="[^"]*(?:video-heading|work-title)[^"]*"[^>]*>([^<]+)',
                webpage, 'title', default=None)
            or self._html_extract_title(webpage))

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, default=None),
            'thumbnail': thumbnail,
            'release_year': int_or_none(self._search_regex(
                r'(\d{4})\s*（明治', webpage, 'release year', default=None)),
            'uploader': self._html_search_meta('copyright', webpage, default=None),
            'formats': formats,
            'subtitles': subtitles,
        }


class MeijiFilmArchivesPlaylistIE(InfoExtractor):
    IE_NAME = 'meijifilmarchives:playlist'
    IE_DESC = 'The Meiji Period on Film listings'
    _VALID_URL = r'https?://(?:www\.)?meiji\.filmarchives\.jp/(?P<id>works|lumiere-works)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://meiji.filmarchives.jp/works/',
        'info_dict': {
            'id': 'works',
            'title': '動画一覧｜映像でみる明治の日本 / The Meiji Period on Film',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://meiji.filmarchives.jp/lumiere-works/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        return self.playlist_from_matches(
            re.findall(
                r'href="(/(?:works|lumiere-works)/[\w.-]+\.html)"', webpage),
            playlist_id, self._html_extract_title(webpage),
            getter=lambda path: urljoin(url, path),
            ie=MeijiFilmArchivesIE)
