import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    float_or_none,
    int_or_none,
    parse_duration,
    unescapeHTML,
    url_or_none,
)


class BigMarkerIE(InfoExtractor):
    IE_NAME = 'BigMarker'
    IE_DESC = 'BigMarker webinars'
    _VALID_URL = [
        r'https?://(?:www\.)?bigmarker\.com/(?:conferences|recordings)/(?P<id>[0-9a-f]+)',
        r'https?://(?:www\.)?bigmarker\.com/(?!(?:communities|conferences|recordings|series|webinars|users|accounts|api|demos|home|about|product_updates)(?:/|$))(?P<channel>[\w-]+)/(?P<id>[\w-]+)',
        r'https?://click\d+\.bigmarker\.com/links/(?P<id>[^?#]+)',
    ]
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://(?:www\.)?bigmarker\.com/recordings/[0-9a-f]+[^"\']*)\1']
    _TESTS = [{
        'url': 'https://www.bigmarker.com/eetech-media/microgrids-the-journey-to-sustainable-ai-data-centers-in-europe',
        'md5': 'e765a6aa1245885ba5ee9c3541f8d55d',
        'info_dict': {
            'id': 'eb85d39e0062',
            'ext': 'mp4',
            'display_id': 'microgrids-the-journey-to-sustainable-ai-data-centers-in-europe',
            'title': 'Microgrids: The Journey to Sustainable AI Data Centers in Europe',
            'description': 'md5:e440b9559caa281d59c4842ead077704',
            'thumbnail': r're:https://.+\.(?:png|jpe?g)',
            'duration': 3600,
            'timestamp': 1752159600,
            'upload_date': '20250710',
            'uploader': 'EETech Media',
            'uploader_id': 'eetech-media',
            'channel': 'EETech Media',
            'channel_id': 'eetech-media',
            'channel_url': 'https://www.bigmarker.com/eetech-media',
            'creators': ['Bob Downing'],
        },
    }, {
        'url': 'https://www.bigmarker.com/conferences/eb85d39e0062',
        'only_matching': True,
    }, {
        'url': 'https://www.bigmarker.com/recordings/6210f003190f',
        'only_matching': True,
    }, {
        'url': 'https://click30.bigmarker.com/links/IdIg4-FAge3/bDQqexv8r/-9FRLlyhg3M/viTYzj5zvEq',
        'only_matching': True,
    }]

    def _search_player_value(self, webpage, key, name):
        return self._search_regex(
            rf'(?:["\']{re.escape(key)}["\']|{re.escape(key)})\s*:\s*["\']([^"\']+)',
            webpage, name, default=None)

    def _search_player_url(self, webpage, key, name):
        return url_or_none(self._search_player_value(webpage, key, name))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(
            r'<input[^>]+id="conference-obfuscated-id"[^>]+value="([^"]+)"',
            webpage, 'conference id', default=None) or self._search_regex(
            r'/conferences/([0-9a-f]+)/recording_watched',
            webpage, 'conference id', default=display_id)

        formats, subtitles = [], {}
        mp4_url = self._search_player_url(webpage, 'mp4Url', 'mp4 url')
        if mp4_url:
            formats.append({
                'url': mp4_url,
                'ext': 'mp4',
                'format_id': 'http-mp4',
            })

        hls_url = self._search_player_url(webpage, 'hls_manifest_url', 'hls url')
        if hls_url:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)

        dash_url = self._search_player_url(webpage, 'dash_manifest_url', 'dash url')
        dash_key = self._search_player_value(webpage, 'dash_encryption_key', 'dash key')
        if dash_url and not dash_key:
            dash_fmts, dash_subs = self._extract_mpd_formats_and_subtitles(
                dash_url, video_id, mpd_id='dash', fatal=False)
            formats.extend(dash_fmts)
            self._merge_subtitles(dash_subs, target=subtitles)

        if not formats:
            if dash_url and dash_key:
                self.report_drm(video_id)
            if re.search(r'id=["\']register-to-view-recording-box["\']', webpage):
                self.raise_login_required(
                    'This recording requires registration', method=None)
            self.raise_no_formats('No recording is available', expected=True, video_id=video_id)

        channel_id = self._match_valid_url(url).groupdict().get('channel') or self._search_regex(
            r'id="channle-host-contact-box".*?href="/([\w-]+)"',
            webpage, 'channel id', default=None, flags=re.DOTALL)
        uploader = clean_html(self._search_regex(
            r'id="channle-host-contact-box".*?<h2><a[^>]*>([^<]+)',
            webpage, 'uploader', default=None, flags=re.DOTALL)) or channel_id
        duration = parse_duration(clean_html(self._search_regex(
            r'>Duration</div>\s*<div[^>]*>\s*<div[^>]*>\s*([^<]+)',
            webpage, 'duration', default=None)))
        timestamp = int_or_none(float_or_none(self._search_regex(
            r'webinar-start-time=["\']([0-9.]+)', webpage, 'timestamp', default=None)), scale=1000)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
            'description': clean_html(self._og_search_description(webpage, default=None)),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': channel_id,
            'channel': uploader,
            'channel_id': channel_id,
            'channel_url': f'https://www.bigmarker.com/{channel_id}' if channel_id else None,
            'creators': [unescapeHTML(name) for name in re.findall(
                r'class="presenter_name">\s*<a[^>]*>([^<]+)', webpage)] or None,
            'formats': formats,
            'subtitles': subtitles,
        }
