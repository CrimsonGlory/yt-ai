import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    join_nonempty,
    smuggle_url,
    unescapeHTML,
    unsmuggle_url,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class KinescopeIE(InfoExtractor):
    IE_NAME = 'kinescope'
    IE_DESC = 'Kinescope'
    _VALID_URL = r'https?://(?:www\.)?kinescope\.io/(?:embed/)?(?P<id>(?!oembed$)[A-Za-z0-9_-]+)(?:/\d+p)?/?(?:[?#]|$)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://(?:www\.)?kinescope\.io/(?:embed/)?(?!oembed)[A-Za-z0-9_-]+[^"\']*)\1']
    _TESTS = [{
        'url': 'https://kinescope.io/200597093/',
        'md5': '7c750e03ed6e555afd7a8ac5baa9d44a',
        'info_dict': {
            'id': '200597093',
            'ext': 'mp4',
            'title': 'Вводное занятие',
            'description': 'Watch "Вводное занятие" powered by Kinescope, the ecosystem of video solutions for business of any size.',
            'thumbnail': r're:https://.+\.jpg',
            'duration': 457.8,
            'timestamp': 1625841233,
            'upload_date': '20210709',
        },
        'params': {'format': 'http-360'},
    }, {
        'url': 'https://kinescope.io/200597096/',
        'only_matching': True,
    }, {
        'url': 'https://kinescope.io/gnX8zTdpNzCMALFsExfgmq',
        'only_matching': True,
    }, {
        'url': 'https://kinescope.io/embed/7c89acb3-2d4a-4827-8579-e234c0f7229c',
        'only_matching': True,
    }, {
        'url': 'https://kinescope.io/200597093/1080p',
        'only_matching': True,
    }]

    @classmethod
    def _extract_embed_urls(cls, url, webpage):
        for embed_url in super()._extract_embed_urls(url, webpage):
            yield smuggle_url(embed_url, {'Referer': url})

    def _extract_http_formats(self, item, video_id, headers):
        media_id = traverse_obj(item, ('id', {str})) or video_id
        http_formats = []
        for height in traverse_obj(item, ('qualityLabels', ..., 'q', {int_or_none})):
            if not height:
                continue
            http_formats.append({
                'url': f'https://kinescope.io/{media_id}/{height}p',
                'ext': 'mp4',
                'format_id': join_nonempty('http', height),
                'height': height,
                'fps': int_or_none(traverse_obj(item, ('frameRate', str(height)))),
                'acodec': 'none',
                'http_headers': headers,
            })
        return http_formats

    def _extract_video(self, item, video_id, headers, extra):
        drm = traverse_obj(item, ('drm'))
        if isinstance(drm, dict):
            if any(str(k).lower() in ('widevine', 'fairplay', 'playready') for k in drm):
                self.report_drm(video_id)
        elif drm:
            self.report_drm(video_id)

        formats, subtitles = [], {}
        m3u8_url = traverse_obj(item, (
            'sources', ('hls', 'shakahls'), 'src', {url_or_none}, any))
        is_live = traverse_obj(item, ('meta', 'type', {str})) == 'live'
        if m3u8_url:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                live=is_live, headers=headers)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)

        dash_url = traverse_obj(item, ('sources', 'dash', 'src', {url_or_none}))
        if dash_url:
            dash_fmts, dash_subs = self._extract_mpd_formats_and_subtitles(
                dash_url, video_id, mpd_id='dash', fatal=False, headers=headers)
            formats.extend(dash_fmts)
            self._merge_subtitles(dash_subs, target=subtitles)

        formats.extend(self._extract_http_formats(item, video_id, headers))

        for vtt in traverse_obj(item, ('vtt', lambda _, v: url_or_none(v['src']))):
            lang = vtt.get('srcLang') or 'und'
            subtitles.setdefault(lang, []).append({
                'url': vtt['src'],
                'ext': 'vtt',
                'name': vtt.get('label'),
            })

        if not formats:
            self.raise_no_formats(
                'No video formats found', expected=True, video_id=video_id)

        info = {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live or None,
            'http_headers': headers,
            **extra,
        }
        info.update(traverse_obj(item, {
            'title': ('title', {str}),
            'duration': ('meta', 'duration', {float_or_none}),
            'thumbnail': ('poster', 'src', 'src', {url_or_none}),
        }))
        return info

    def _real_extract(self, url):
        url, smuggled = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        headers = {'Referer': smuggled.get('Referer') or url}
        webpage = self._download_webpage(
            url, video_id, headers={'Referer': headers['Referer']})

        if re.search(r'<title>\s*Access forbidden', webpage, re.I):
            raise ExtractorError('Kinescope rejected the request', expected=True)

        player = self._search_json(
            r'var\s+playerOptions\s*=', webpage, 'player options',
            video_id, fatal=False) or {}
        extra = self._search_json_ld(webpage, video_id, default={})
        content_url = extra.pop('url', None)
        extra.pop('ext', None)

        playlist = traverse_obj(player, ('playlist', ..., {dict})) or []
        if not playlist:
            m3u8_url = url_or_none(content_url) or url_or_none(unescapeHTML(
                self._search_regex(
                    r'https?://kinescope\.io/[^"\']+/master\.m3u8[^"\']*',
                    webpage, 'm3u8 url', default=None)))
            if m3u8_url:
                playlist = [{'sources': {'hls': {'src': m3u8_url}}}]

        if not playlist:
            self.raise_no_formats(
                'No video formats found', expected=True, video_id=video_id)

        entries = [
            self._extract_video(
                item, (item.get('id') if len(playlist) > 1 else None) or video_id,
                headers, extra)
            for item in playlist
        ]
        if len(entries) > 1:
            return self.playlist_result(entries, video_id, extra.get('title'))
        return entries[0]
