import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AllDafIE(InfoExtractor):
    IE_DESC = 'alldaf.org'
    _VALID_URL = r'https?://(?:www\.)?alldaf\.org/p/(?P<id>\d+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://alldaf.org/p/240900',
        'md5': '2eacb6c92139d087c6505b93c5e6d276',
        'info_dict': {
            'id': '240900',
            'ext': 'mp3',
            'title': 'Zevachim 86 - Cycle 14',
            'duration': 2369.5671,
            'timestamp': 1764902052,
            'upload_date': '20251205',
            'series': 'Daf Yomi with Rabbi Elefant - Cycle 14',
            'series_id': '4049',
            'episode_number': 3449,
            'episode': 'Episode 3449',
            'creators': ['Rabbi Moshe Elefant'],
            'uploader': 'Rabbi Moshe Elefant',
            'thumbnail': r're:https?://cdn\.jwplayer\.com/v2/media/.+',
        },
        'params': {
            # Progressive MP3; HLS is the JWPlayer fallback
            'format': 'best[ext=mp3]/best',
        },
    }, {
        'url': 'https://alldaf.org/p/262335',
        'md5': 'a045a6f9e19d2226145b6e3840b2cc9b',
        'info_dict': {
            'id': '262335',
            'ext': 'mp4',
            'title': 'Inside a Glatt Kosher Beef Plant | Hastings, Nebraska',
            'duration': 764.736,
            'timestamp': 1787836851,
            'upload_date': '20260827',
            'series': 'Bringing Chulin To Life',
            'series_id': '10562',
            'episode_number': 68,
            'episode': 'Episode 68',
            'creators': ['Rabbi Moshe Schwed'],
            'uploader': 'Rabbi Moshe Schwed',
            'thumbnail': r're:https?://cdn\.jwplayer\.com/v2/media/.+',
        },
        'params': {
            'format': 'best[protocol=https][ext=mp4]/best',
        },
    }, {
        'url': 'https://alldaf.org/p/240900/',
        'only_matching': True,
    }]

    _JW_ID_RE = r'(?:content\.jwplatform|cdn\.jwplayer)\.com/(?:videos|manifests)/([a-zA-Z0-9]{8})'
    _JW_FAKE_MP3_RE = r'(?:content\.jwplatform|cdn\.jwplayer)\.com/videos/[a-zA-Z0-9]{8}\.mp3'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        post = traverse_obj(self._search_nuxt_json(webpage, video_id, fatal=False), (
            'data', lambda _, v: isinstance(v, dict) and str_or_none(v.get('id')) == video_id,
            any)) or {}

        jw_id = traverse_obj(post, ('mediaId', {str})) or self._search_regex(
            self._JW_ID_RE, webpage, 'jw media id', default=None)
        media_type = traverse_obj(post, ('mediaType', {str}))
        formats, subtitles = [], {}
        seen_urls = set()

        jw_info = {}
        if jw_id:
            jw_data = self._download_json(
                f'https://cdn.jwplayer.com/v2/media/{jw_id}', video_id,
                'Downloading JWPlayer media JSON', fatal=False)
            if jw_data:
                parsed = self._parse_jwplayer_data(
                    jw_data, video_id, require_title=False)
                if isinstance(parsed, dict) and parsed.get('_type') != 'playlist':
                    jw_info = parsed
                    formats.extend(jw_info.get('formats') or [])
                    self._merge_subtitles(jw_info.get('subtitles') or {}, target=subtitles)
                    seen_urls.update(traverse_obj(formats, (..., 'url', {url_or_none})))

        s3_url = traverse_obj(post, ('s3Url', {url_or_none}))
        if s3_url and s3_url not in seen_urls and not re.search(self._JW_FAKE_MP3_RE, s3_url):
            ext = determine_ext(s3_url)
            formats.append({
                'url': s3_url,
                'format_id': 'http',
                'ext': ext,
                'vcodec': 'none' if media_type == 'Audio' or ext in ('mp3', 'm4a', 'aac') else None,
            })
            seen_urls.add(s3_url)

        hls_url = traverse_obj(post, ('hls_url', {url_or_none}))
        if hls_url and not jw_info.get('formats'):
            hls_formats, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4' if media_type != 'Audio' else 'mp3',
                m3u8_id='hls', fatal=False)
            formats.extend(hls_formats)
            self._merge_subtitles(hls_subs, target=subtitles)

        if not formats:
            self.raise_no_formats('No media formats found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': self._og_search_thumbnail(webpage),
            **traverse_obj(jw_info, {
                'title': ('title', {str}),
                'duration': ('duration', {float_or_none}),
                'timestamp': ('timestamp', {int_or_none}),
                'thumbnail': ('thumbnail', {url_or_none}),
            }),
            **traverse_obj(post, {
                'title': ('title', {str}),
                'duration': ('duration', {float_or_none}),
                'timestamp': ('publishDate', {parse_iso8601}),
                'series': ('series', 'name', {str}),
                'series_id': ('series', 'id', {int_or_none}, {str_or_none}),
                'episode_number': ('episodeNumber', {int_or_none}),
                'creators': ('authors', ..., 'name', {str}, all),
                'uploader': ('authors', 0, 'name', {str}),
            }),
        }
