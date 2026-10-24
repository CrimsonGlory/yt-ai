import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    float_or_none,
    int_or_none,
    remove_end,
    unescapeHTML,
    url_or_none,
)

_VIDEO_ATTR_RE = re.compile(
    r'<[^>]+(?:\bdata-vid-id|\bdata-video-id)=["\'][^"\']+["\'][^>]*>')


def _media_url(value):
    if not value or value == 'undefined':
        return None
    return url_or_none(value)


def _attr(attrs, *keys):
    for key in keys:
        value = attrs.get(key)
        if value and value != 'undefined':
            return unescapeHTML(value)
    return None


def _wiki_ids(raw):
    if not raw:
        return []
    raw = unescapeHTML(raw)
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return [part for part in raw.split(',') if part]
    ids = []
    if not isinstance(parsed, list):
        return ids
    for item in parsed:
        if isinstance(item, str) and item:
            ids.append(item)
        elif isinstance(item, (list, tuple)) and item:
            ids.append(str(item[0]))
    return ids


class TVTropesIE(InfoExtractor):
    IE_NAME = 'tvtropes'
    IE_DESC = 'TV Tropes'
    _VALID_URL = r'https?://(?:www\.)?tvtropes\.org/pmwiki/video_example\.php\?(?:[^#]*&)?video_id=(?P<id>[0-9a-z]+)'
    _TESTS = [{
        'url': 'https://tvtropes.org/pmwiki/video_example.php?video_id=lazspg',
        'md5': '9064d6105986657da15134e1363d7928',
        'info_dict': {
            'id': 'lazspg',
            'ext': 'mp4',
            'title': 'Meet the Engineer',
            'description': "The Engineer's introduction to the players",
            'thumbnail': r're:https?://videos\.tvtropes\.org/.+/thumbnail\.jpg',
            'duration': 86,
            'average_rating': float,
            'comment_count': int,
            'categories': ['The Engineer'],
            'tags': ['Main/TheTurretMaster', 'VideoGame/TeamFortress2'],
        },
    }, {
        'url': 'https://www.tvtropes.org/pmwiki/video_example.php?video_id=lazspg',
        'only_matching': True,
    }, {
        'url': 'https://tvtropes.org/pmwiki/video_example.php?video_id=pjy265&groupname=Main&title=TheEngineer',
        'only_matching': True,
    }]
    _HEADERS = {'Referer': 'https://tvtropes.org/'}

    def _extract_video_attrs(self, webpage, video_id):
        for html in _VIDEO_ATTR_RE.findall(webpage):
            attrs = extract_attributes(html)
            if _attr(attrs, 'data-vid-id', 'data-video-id') == video_id:
                return self._normalize_video_attrs(attrs)
        raise ExtractorError('Unable to extract video data', expected=True)

    def _normalize_video_attrs(self, attrs):
        bunny = _attr(attrs, 'data-vid-bunny', 'data-bunny-video-id')
        hls = _attr(attrs, 'data-hls-url')
        mp4 = _attr(attrs, 'data-video-url', 'data-mp4-url')
        if bunny:
            if not hls:
                hls = f'https://videos.tvtropes.org/{bunny}/playlist.m3u8'
            if not mp4:
                mp4 = f'https://videos.tvtropes.org/{bunny}/play_360p.mp4'
        tags = _wiki_ids(_attr(attrs, 'data-vid-also')) + _wiki_ids(_attr(attrs, 'data-vid-sources'))
        if not tags:
            tags = [t for t in (_attr(attrs, 'data-video-media-sources') or '').split(',') if t]
        return {
            'data-bunny-video-id': bunny,
            'data-hls-url': hls,
            'data-mpd-url': _attr(attrs, 'data-mpd-url'),
            'data-video-url': mp4,
            'data-vimeo-id': _attr(attrs, 'data-vimeo-id', 'data-vid-vimeo'),
            'data-video-title': _attr(attrs, 'data-vid-title', 'data-video-title'),
            'data-video-descrip': _attr(attrs, 'data-vid-desc', 'data-video-descrip'),
            'data-video-thumbnail': _attr(attrs, 'data-vid-thumb', 'data-video-thumbnail'),
            'data-video-length': _attr(attrs, 'data-vid-len', 'data-video-length'),
            'data-video-average-rating': _attr(attrs, 'data-vid-avg', 'data-video-average-rating'),
            'data-video-comment-count': _attr(attrs, 'data-vid-count', 'data-video-comment-count'),
            'data-video-tropename': _attr(attrs, 'data-vid-tropename', 'data-video-tropename'),
            'tags': tags,
        }

    def _extract_formats(self, attrs, video_id):
        formats, subtitles = [], {}

        def add_hls(hls_url, m3u8_id='hls'):
            if not hls_url:
                return
            try:
                m3u8_doc = self._download_webpage(
                    hls_url, video_id, 'Downloading m3u8 information',
                    headers=self._HEADERS, impersonate=True)
            except ExtractorError:
                return
            hls_fmts, hls_subs = self._parse_m3u8_formats_and_subtitles(
                m3u8_doc, hls_url, 'mp4', m3u8_id=m3u8_id,
                headers=self._HEADERS, video_id=video_id)
            for fmt in hls_fmts:
                fmt.setdefault('http_headers', {}).update(self._HEADERS)
                fmt['impersonate'] = True
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)

        bunny_id = attrs.get('data-bunny-video-id')
        if bunny_id and re.fullmatch(
                r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', bunny_id, re.I):
            add_hls(f'https://videos.tvtropes.org/{bunny_id}/playlist.m3u8')

        if not formats:
            add_hls(_media_url(attrs.get('data-hls-url')))

        if not formats:
            mpd_url = _media_url(attrs.get('data-mpd-url'))
            if mpd_url:
                mpd_fmts, mpd_subs = self._extract_mpd_formats_and_subtitles(
                    mpd_url, video_id, mpd_id='dash', fatal=False, headers=self._HEADERS)
                formats.extend(mpd_fmts)
                self._merge_subtitles(mpd_subs, target=subtitles)

        if not formats:
            mp4_url = _media_url(attrs.get('data-video-url'))
            if mp4_url:
                formats.append({
                    'url': mp4_url,
                    'format_id': 'http',
                    'ext': 'mp4',
                    'http_headers': self._HEADERS,
                    'impersonate': True,
                })

        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)
        attrs = self._extract_video_attrs(webpage, video_id)

        formats, subtitles = self._extract_formats(attrs, video_id)
        vimeo_id = attrs.get('data-vimeo-id')
        if not formats and vimeo_id and vimeo_id not in ('undefined',):
            return self.url_result(vimeo_id, 'Vimeo', vimeo_id)
        if not formats:
            self.raise_no_formats('No video formats found', video_id=video_id, expected=True)

        trope = (attrs.get('data-video-tropename') or '').strip() or None
        tags = attrs.get('tags') or None

        return {
            'id': video_id,
            'title': (attrs.get('data-video-title') or '').strip() or None,
            'description': (attrs.get('data-video-descrip') or '').strip() or None,
            'thumbnail': _media_url(attrs.get('data-video-thumbnail')),
            'duration': int_or_none(attrs.get('data-video-length')),
            'average_rating': float_or_none(attrs.get('data-video-average-rating')),
            'comment_count': int_or_none(attrs.get('data-video-comment-count')),
            'categories': [trope] if trope else None,
            'tags': tags,
            'formats': formats,
            'subtitles': subtitles,
        }


class TVTropesPlaylistIE(InfoExtractor):
    IE_NAME = 'tvtropes:playlist'
    _VALID_URL = (
        r'https?://(?:www\.)?tvtropes\.org/pmwiki/'
        r'(?:pmwiki\.php/(?P<id>[^?#]+)|(?P<recent>recent_videos)\.php)')
    _TESTS = [{
        'url': 'https://tvtropes.org/pmwiki/pmwiki.php/Main/NetworkFinale',
        'info_dict': {
            'id': 'Main/NetworkFinale',
            'title': 'Network Finale',
        },
        'playlist_mincount': 4,
    }, {
        'url': 'https://tvtropes.org/pmwiki/pmwiki.php/VideoExamples/TheEngineer',
        'only_matching': True,
    }, {
        'url': 'https://tvtropes.org/pmwiki/recent_videos.php',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id, recent = self._match_valid_url(url).group('id', 'recent')
        playlist_id = (playlist_id or recent).rstrip('/')
        webpage = self._download_webpage(url, playlist_id, impersonate=True)

        entries, seen = [], set()
        for html in _VIDEO_ATTR_RE.findall(webpage):
            attrs = extract_attributes(html)
            video_id = _attr(attrs, 'data-vid-id', 'data-video-id')
            if not video_id or video_id in seen or video_id.startswith('tvtropes-videos-'):
                continue
            seen.add(video_id)
            entries.append(self.url_result(
                f'https://tvtropes.org/pmwiki/video_example.php?video_id={video_id}',
                TVTropesIE, video_id, _attr(attrs, 'data-vid-title', 'data-video-title')))

        if not entries:
            raise ExtractorError('No video examples found on this page', expected=True)

        title = remove_end(
            self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage, default=''),
            ' - TV Tropes') or None

        return self.playlist_result(entries, playlist_id, title)
