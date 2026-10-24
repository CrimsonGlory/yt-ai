import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    merge_dicts,
    mimetype2ext,
    orderedSet,
    unescapeHTML,
    url_or_none,
    urlencode_postdata,
    urljoin,
)
from ..utils.traversal import traverse_obj


class JavtifulIE(InfoExtractor):
    IE_NAME = 'javtiful'
    IE_DESC = 'javtiful.com'
    _VALID_URL = (
        r'https?://(?:www\.)?javtiful\.com/(?:[a-z]{2}/)?'
        r'(?:video|embed)/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?')
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?javtiful\.com/(?:[a-z]{2}/)?embed/\d+)']
    _TESTS = [{
        'url': 'https://javtiful.com/video/77717/fsdss-979',
        'md5': 'b74c1407ab8e75ac2a0dadc482604ee4',
        'info_dict': {
            'id': '77717',
            'ext': 'mp4',
            'display_id': 'fsdss-979',
            'title': 'FSDSS-979 A completely positive mistress, a life of affairs where she pampers you to the fullest, Goddess Jun',
            'description': 'md5:d298df0d964b7f7b1035f54b224e9173',
            'thumbnail': r're:https?://javtiful\.com/uploads/.+\.jpg',
            'duration': 7336,
            'timestamp': 1738675212,
            'upload_date': '20250204',
            'view_count': int,
            'like_count': int,
            'channel': 'FALENO',
            'channel_id': 'faleno',
            'channel_url': 'https://javtiful.com/channel/faleno',
            'cast': ['Megami Jun'],
            'categories': ['Affair', 'Big Tits'],
            'tags': ['solowork', 'blowjob', 'cowgirl', 'tittyfuck', 'Megami Jun', 'FALENO', 'Censored'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://javtiful.com/embed/77717',
        'only_matching': True,
    }, {
        'url': 'https://javtiful.com/ja/video/77717/fsdss-979',
        'only_matching': True,
    }, {
        'url': 'https://javtiful.com/video/113006/san-486',
        'only_matching': True,
    }]

    def _extract_player_sources(self, sources, url, video_id):
        formats, subtitles = [], {}
        for source in traverse_obj(sources, (..., {dict})):
            src = url_or_none(urljoin(url, source.get('src')))
            if not src:
                continue
            media_type = source.get('type') if isinstance(source.get('type'), str) else ''
            height = int_or_none(source.get('size'))
            if 'mpegurl' in media_type.lower() or determine_ext(src) == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                continue
            formats.append({
                'url': src,
                'ext': mimetype2ext(media_type) or determine_ext(src, 'mp4'),
                'height': height,
                'format_id': str(height) if height else 'http',
            })
        return formats, subtitles

    def _extract_playback_sources(self, webpage, url, video_id):
        config = self._search_json(
            r'<script[^>]+id="watch-config"[^>]*>', webpage, 'watch config',
            video_id, end_pattern=r'</script>', default={})
        playback = traverse_obj(config, ('playback', {dict})) or {}
        endpoint = urljoin(url, playback['endpoint']) if playback.get('endpoint') else None
        ticket = traverse_obj(playback, ('ticket', {str}))
        if not endpoint or not ticket:
            return [], {}

        csrf = traverse_obj(self._download_json(
            urljoin(url, config.get('csrfUrl') or '/csrf-token'), video_id,
            'Downloading CSRF token', fatal=False, headers={
                'Accept': 'application/json',
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest',
            }), ('token', {str}))
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': 'https://javtiful.com',
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
        }
        postdata = {'ticket': ticket}
        if csrf:
            headers['X-CSRF-TOKEN'] = csrf
            postdata['_token'] = csrf
        playback_json = self._download_json(
            endpoint, video_id, 'Downloading playback sources',
            data=urlencode_postdata(postdata), headers=headers, fatal=False) or {}
        return self._extract_player_sources(playback_json.get('sources'), url, video_id)

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        formats, subtitles = self._extract_playback_sources(webpage, url, video_id)
        if not formats:
            formats, subtitles = self._extract_player_sources(self._search_json(
                r'"playerSources"\s*:\s*', webpage, 'player sources', video_id,
                contains_pattern=r'\[(?s:.+?)\]', default=[],
            ), url, video_id)

        if not formats:
            for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
                formats.extend(entry.get('formats') or [])
                self._merge_subtitles(entry.get('subtitles') or {}, target=subtitles)

        if not formats:
            raise ExtractorError('No video source found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)

        channel_id = self._search_regex(
            r'href="/channel/([^"/?#]+)"', webpage, 'channel id', default=None)
        poster = unescapeHTML(self._search_regex(
            r'(?:poster|"videoPoster")\s*[:=]\s*"([^"]+)"',
            webpage, 'thumbnail', default=None))

        return merge_dicts(json_ld, {
            'id': video_id,
            'display_id': display_id,
            'title': (
                self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
                or self._og_search_title(webpage, default=None)),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': urljoin(url, poster) or self._og_search_thumbnail(webpage, default=None),
            'like_count': int_or_none(self._search_regex(
                r'data-front-likes-count[^>]*>\s*(\d+)', webpage, 'like count', default=None)),
            'channel': self._html_search_regex(
                r'href="/channel/[^"]+"[^>]*>([^<]+)', webpage, 'channel', default=None),
            'channel_id': channel_id,
            'channel_url': urljoin('https://javtiful.com/', f'channel/{channel_id}') if channel_id else None,
            'cast': orderedSet(
                unescapeHTML(name.strip())
                for name in re.findall(
                    r'href="/actress/[^"]+"[^>]*>\s*(?:<img[^>]*>\s*)?<span>([^<]+)',
                    webpage)
                if name.strip()) or None,
            'categories': orderedSet(
                unescapeHTML(c.strip())
                for c in re.findall(r'<a[^>]+href="/category/[^"]+"[^>]*>([^<]+)', webpage)
                if c.strip()) or None,
            'tags': orderedSet(
                t.strip() for t in (self._html_search_meta('keywords', webpage) or '').split(',')
                if t.strip()) or None,
            'age_limit': 18,
            'formats': formats,
            'subtitles': subtitles,
        })
