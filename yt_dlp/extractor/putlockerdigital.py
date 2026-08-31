import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    parse_duration,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class PutlockerDigitalIE(InfoExtractor):
    IE_NAME = 'putlocker:digital'
    IE_DESC = 'Putlocker.digital'
    _VALID_URL = (
        r'https?://(?:www\d*\.)?putlocker\.digital/'
        r'(?P<kind>movie|tv-series)/(?P<slug>[^/?#]+)/(?P<id>[A-Za-z0-9]+)'
        r'(?:-watch-online-free(?:\.html)?)?'
        r'(?:/(?P<episode>[A-Za-z0-9]+)(?:-watch-online-free(?:\.html)?)?)?'
        r'/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://www2.putlocker.digital/movie/classified-2024/l7m49b2y/2vqCRvSH-watch-online-free.html',
        'md5': '6f02a48169af85060d785dc4ec09409a',
        'info_dict': {
            'id': 'l7m49b2y',
            'ext': 'mp4',
            'title': 'Classified (2024)',
            'display_id': 'classified-2024',
            'description': 'md5:175405b362cb455aa1b7dd5f55f40d3d',
            'thumbnail': r're:https?://static\.putlocker\.digital/.+',
            'duration': 6300,
            'release_year': 2024,
            'average_rating': 3.7,
            'genres': ['Action', 'Thriller'],
            'cast': 'count:11',
            'creators': ['Roel Reiné'],
        },
    }, {
        'url': 'https://www2.putlocker.digital/movie/classified-2024/l7m49b2y-watch-online-free.html',
        'only_matching': True,
    }, {
        'url': 'https://www2.putlocker.digital/tv-series/classified-season-1/ErDzfRY5/1waz8ol1-watch-online-free.html',
        'only_matching': True,
    }, {
        'url': 'https://www2.putlocker.digital/tv-series/classified-season-1/ErDzfRY5',
        'only_matching': True,
    }, {
        'url': 'https://putlocker.digital/movie/classified-2024/l7m49b2y',
        'only_matching': True,
    }]

    def _info_field(self, webpage, name):
        return self._html_search_regex(
            rf'<div class="t">\s*{re.escape(name)}:\s*</div>\s*<div class="v">(.*?)</div>',
            webpage, name, default=None, flags=re.DOTALL)

    def _split_names(self, value):
        if not value:
            return None
        names = [part.strip() for part in re.split(r'\s*,\s*', value)
                 if part.strip() and '»' not in part]
        return names or None

    def _extract_season_playlist(self, url, webpage, playlist_id):
        entries, seen = [], set()
        for ep_id, path in re.findall(
            r'<a\b(?=[^>]*\bdata-ep-id="([^"]+)")(?=[^>]*\bhref="([^"]+)")[^>]*>',
                webpage):
            if ep_id in seen:
                continue
            seen.add(ep_id)
            entries.append(self.url_result(
                urljoin(url, path), ie=self.ie_key(), video_id=ep_id))
        if not entries:
            raise ExtractorError('No episodes found', expected=True)
        return self.playlist_result(
            entries, playlist_id, self._html_search_regex(
                r'<h1[^>]*>(.+?)</h1>', webpage, 'title', default=None))

    def _extract_subtitles(self, webpage, video_id):
        subtitles = {}
        for track in self._search_json(
            r'window\.subtitles\s*=', webpage, 'subtitles', video_id,
            contains_pattern=r'\[(?s:.+)\]', default=[],
        ) or []:
            sub_url = traverse_obj(track, (('src', 'file'), {url_or_none}, any))
            lang = traverse_obj(track, (('srclang', 'label'), {str}, any)) or 'und'
            if sub_url:
                subtitles.setdefault(lang, []).append({
                    'url': sub_url,
                    'name': traverse_obj(track, ('label', {str})),
                    'ext': determine_ext(sub_url, 'srt'),
                })
        return subtitles

    def _extract_formats(self, sources, video_id):
        formats, subtitles = [], {}
        for source in sources:
            media_url = traverse_obj(source, (('src', 'file'), {url_or_none}, any))
            if not media_url:
                continue
            media_type = traverse_obj(source, ('type', {str}))
            label = traverse_obj(source, ('label', {lambda v: str(v) if v is not None else None}))
            height = int_or_none(self._search_regex(
                r'(\d+)', label or '', 'height', default=None))
            if media_type == 'm3u8' or determine_ext(media_url) == 'm3u8':
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
                continue
            formats.append({
                'url': media_url,
                'format_id': label,
                'ext': 'mp4' if media_type in (None, 'mp4') else media_type,
                'height': height,
                'filesize': traverse_obj(source, ('size', {int_or_none})),
            })
        return formats, subtitles

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        kind, slug, catalog_id, episode_id = mobj.group('kind', 'slug', 'id', 'episode')
        video_id = episode_id if kind == 'tv-series' and episode_id else catalog_id

        webpage = self._download_webpage(url, video_id)
        is_watching = self._search_regex(
            r'PlayerPage\(\s*(true|false)', webpage, 'watch page', default=None)
        if is_watching == 'false':
            return self._extract_season_playlist(url, webpage, catalog_id)

        sources = self._download_json(
            url, video_id, 'Downloading video JSON', query={'number': '1'},
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': url,
            },
            transform_source=lambda s: '[]' if s.strip() in ('none', '') else s)

        if isinstance(sources, dict):
            if traverse_obj(sources, 'capcha'):
                raise ExtractorError(
                    'Putlocker.digital requires a captcha to play this video', expected=True)
            iframe_url = traverse_obj(sources, ('link', {url_or_none}))
            if traverse_obj(sources, 'type') == 'iframe' and iframe_url:
                return self.url_result(iframe_url)
            sources = [sources]

        if not isinstance(sources, list) or not sources:
            raise ExtractorError('No video sources found', expected=True)

        formats, subtitles = self._extract_formats(sources, video_id)
        self._merge_subtitles(self._extract_subtitles(webpage, video_id), target=subtitles)
        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        title = (
            self._html_search_regex(r'<h1[^>]*>(.+?)</h1>', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage))
        description = self._html_search_regex(
            r'<div[^>]+id="info"[^>]*>\s*<div[^>]*>\s*<div class="text">(.+?)</div>',
            webpage, 'description', default=None, flags=re.DOTALL)

        return {
            'id': video_id,
            'display_id': slug,
            'title': title,
            'description': description or self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': parse_duration(self._info_field(webpage, 'Duration')),
            'release_year': int_or_none(self._info_field(webpage, 'Release')),
            'average_rating': float_or_none(self._info_field(webpage, 'IMDb')),
            'genres': self._split_names(self._info_field(webpage, 'Genre')),
            'cast': self._split_names(self._info_field(webpage, 'Actors')),
            'creators': self._split_names(self._info_field(webpage, 'Director')),
            'formats': formats,
            'subtitles': subtitles,
        }
