import base64
import json
import random
import re
import string
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_qs,
    update_url_query,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CommercialRadioIE(InfoExtractor):
    IE_NAME = '881903'
    IE_DESC = 'Commercial Radio Hong Kong'
    _VALID_URL = r'https?://(?:www\.)?881903\.com/live/(?P<id>881|903|864)(?:/video)?'
    _TESTS = [{
        'url': 'https://www.881903.com/live/903',
        'info_dict': {
            'id': '903',
            'ext': 'aac',
            'title': r're:叱咤903直播｜商業電台 881903',
            'description': 'md5:cb13c87cbeec24c19e6050b309ffc39c',
            'thumbnail': 'https://www.881903.com/share.png',
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://www.881903.com/live/881',
        'only_matching': True,
    }, {
        'url': 'https://www.881903.com/live/864',
        'only_matching': True,
    }, {
        'url': 'https://www.881903.com/live/903/video',
        'only_matching': True,
    }]
    _STREAMS = {
        '881': ('1', '881hd'),
        '903': ('2', '903hd'),
        '864': ('4', '864sd'),
    }
    _ORIGIN = 'https://www.881903.com'

    def _extract_playback_js_url(self, webpage):
        mobj = re.search(r'atob\(d\.(\w+) \+ d\.(\w+)\)', webpage)
        if not mobj:
            return None
        part1 = self._search_regex(
            rf'"{re.escape(mobj.group(1))}"\s*:\s*"([^"]+)"',
            webpage, 'playback URL part 1', default=None)
        part2 = self._search_regex(
            rf'"{re.escape(mobj.group(2))}"\s*:\s*"([^"]+)"',
            webpage, 'playback URL part 2', default=None)
        if not part1 or not part2:
            return None
        try:
            return base64.b64decode(part1 + part2 + '===').decode()
        except (ValueError, UnicodeDecodeError):
            return None

    def _m3u8_from_cloudfront_policy(self, media_url):
        policy = getattr(self._get_cookies(media_url).get('CloudFront-Policy'), 'value', None)
        if not policy:
            return None
        try:
            data = json.loads(base64.urlsafe_b64decode(policy + '==='))
        except (ValueError, json.JSONDecodeError):
            return None
        resource = traverse_obj(data, ('Statement', 0, 'Resource', {str}))
        if resource and resource.endswith('/*'):
            return resource[:-1] + 'playlist.m3u8'
        return None

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        api_id, stream_id = self._STREAMS[channel_id]
        webpage = self._download_webpage(url, channel_id)
        headers = {
            'Referer': url,
            'Origin': self._ORIGIN,
        }

        src = self._download_json(
            f'https://www.881903.com/api/live/src/{api_id}', channel_id,
            'Downloading live source', fatal=False, headers={
                'Referer': url,
                'Accept': 'application/json',
            })
        playlist_js_url = traverse_obj(src, ('response', 'livePlaylistUrl', {url_or_none}))
        if not playlist_js_url:
            playlist_js_url = url_or_none(self._extract_playback_js_url(webpage))
        if not playlist_js_url:
            raise ExtractorError('Unable to extract live playlist URL', expected=True)

        z = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        playlist_js_url = update_url_query(playlist_js_url, {'z': z})
        playlist_js, urlh = self._download_webpage_handle(
            playlist_js_url, channel_id, 'Downloading playlist script', headers=headers)
        script_url = urlh.url

        parsed = urllib.parse.urlparse(script_url)
        media_base = f'{parsed.scheme}://{parsed.netloc}'
        aac_m3u8 = f'{media_base}/edge-aac/{stream_id}/playlist.m3u8'
        qs = parse_qs(script_url)
        ts_query = {k: qs[k][0] for k in ('r', 'ri') if traverse_obj(qs, (k, 0))}
        ts_m3u8 = f'{media_base}/edge-ts/{stream_id}/playlist.m3u8'
        if ts_query:
            ts_m3u8 = update_url_query(ts_m3u8, ts_query)

        m3u8_url = (
            self._m3u8_from_cloudfront_policy(aac_m3u8)
            or self._search_regex(
                r'(https?://[^\s\'"\\]+\.m3u8[^\s\'"\\]*)',
                playlist_js, 'm3u8 URL', default=None)
            or aac_m3u8)

        formats = subtitles = None
        for candidate in dict.fromkeys(filter(None, (m3u8_url, aac_m3u8, ts_m3u8))):
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                candidate, channel_id, 'aac', m3u8_id='hls', live=True,
                headers=headers, fatal=False)
            if formats:
                break
        if not formats:
            raise ExtractorError('Unable to extract live stream', expected=True)

        return {
            'id': channel_id,
            'title': self._og_search_title(webpage, default=None),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }
