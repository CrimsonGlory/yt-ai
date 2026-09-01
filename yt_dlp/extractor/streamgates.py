import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    js_to_json,
    traverse_obj,
    url_or_none,
    variadic,
)


class StreamgatesIE(InfoExtractor):
    _VALID_URL = r'https?://cplayer\.streamgates\.net/dvr/?\?(?:[^#]*&)?Xs=(?P<id>[^&#]+)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://cplayer\.streamgates\.net/dvr/\?[^"\']+)\1']
    _TESTS = [
        {
            'url': 'https://cplayer.streamgates.net/dvr/?Sv=clive_vod&Xs=siyum_belzashdod_rec&Pp=clive_rec&Tt=c-live.co.il',
            'md5': '039c0fdf899edf3dbb76dd1ec297a291',
            'info_dict': {
                'id': 'siyum_belzashdod_rec',
                'ext': 'mp4',
                'title': 'Clive.CO.IL',
                'channel': 'c-live.co.il',
                'width': 1280,
                'height': 720,
            },
        },
        {
            'url': 'https://cplayer.streamgates.net/dvr/?Xs=siyum_belzashdod_rec',
            'only_matching': True,
        },
    ]

    def _add_src_formats(self, src, video_id, headers):
        formats, subtitles = [], {}
        if isinstance(src, str):
            src = {'hls': src} if determine_ext(src) == 'm3u8' else {'mp4': src}

        hls_url = traverse_obj(src, ('hls', {url_or_none}))
        if hls_url:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', headers=headers,
            )
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)

        dash_url = traverse_obj(src, ('dash', {url_or_none}))
        if dash_url:
            dash_fmts, dash_subs = self._extract_mpd_formats_and_subtitles(
                dash_url, video_id, mpd_id='dash', fatal=False, headers=headers,
            )
            formats.extend(dash_fmts)
            self._merge_subtitles(dash_subs, target=subtitles)

        for mp4 in variadic(traverse_obj(src, 'mp4') or []):
            mp4_url = mp4 if isinstance(mp4, str) else traverse_obj(mp4, ('src', {url_or_none}), ('url', {url_or_none}))
            mp4_url = url_or_none(mp4_url)
            if mp4_url:
                formats.append(
                    {
                        'url': mp4_url,
                        'ext': determine_ext(mp4_url, 'mp4'),
                        'format_id': 'mp4',
                    },
                )
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        src = self._search_json(
            r'(?:var|const|let)\s+src\s*=', webpage, 'player src', video_id, transform_source=js_to_json, default=None,
        )
        if src is None:
            settings = self._search_json(
                r'(?:var|const|let)\s+settings\s*=', webpage, 'player settings', video_id, transform_source=js_to_json,
            )
            src = traverse_obj(settings, 'src')
        if not src:
            raise ExtractorError('Unable to extract Radiant Media Player source', expected=True)

        headers = {'Referer': 'https://cplayer.streamgates.net/'}
        formats, subtitles = self._add_src_formats(src, video_id, headers)
        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        title = (
            traverse_obj(src, ('contentTitle', {str})) or self._html_extract_title(webpage, default=None) or video_id
        )
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'channel': traverse_obj(query, ('Tt', 0, {str})),
            'http_headers': headers,
        }
