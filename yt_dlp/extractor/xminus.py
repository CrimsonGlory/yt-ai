import math
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    float_or_none,
    get_element_html_by_id,
    int_or_none,
    parse_duration,
    unified_strdate,
)


class XMinusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?x-minus\.(?:org|pro|me)/track/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://x-minus.pro/track/147/theres-a-fire-starting-in-my',
        'md5': 'fe9eb5122264bb1626a92f13dcb770ad',
        'info_dict': {
            'id': '147',
            'ext': 'mp3',
            'title': 'Adele-Rolling in the Deep',
            'duration': 230,
            'tbr': 242,
            'filesize_approx': 6600000.0,
            'upload_date': '20120810',
            'description': 'md5:87e9a54523e237a5df2201cfa71b0d7d',
        },
    }, {
        'url': 'http://x-minus.org/track/4542/%D0%BF%D0%B5%D1%81%D0%B5%D0%BD%D0%BA%D0%B0-%D1%88%D0%BE%D1%84%D0%B5%D1%80%D0%B0.html',
        'skip': 'x-minus.org domain has expired',
    }]

    def _media_host(self, webpage, video_id):
        host_fn = self._search_regex(
            r'function getMediaHost\(id,p,t,d\)\{([^}]+)\}',
            webpage, 'media host', default='')
        prefixes = re.findall(r"'([^']+)'", self._search_regex(
            r'\bh=\[([^\]]+)\]', host_fn, 'media prefixes', default=''))
        default_prefix = self._search_regex(
            r"\bs='([^']+)'", host_fn, 'default media prefix', default='m5.')
        threshold = int_or_none(self._search_regex(
            r'id<(\d+)', host_fn, 'media host threshold', default=None))
        vid = int(video_id)
        if prefixes and (threshold is None or vid < threshold):
            prefix = prefixes[vid % len(prefixes)]
        else:
            prefix = default_prefix
        return f'https://{prefix}xmst.cc'

    def _extract_media_url(self, webpage, video_id, track_name):
        player_k = extract_attributes(
            get_element_html_by_id('player-data', webpage) or '').get('data-k')
        track_k = extract_attributes(
            get_element_html_by_id(f'm{video_id}', webpage) or '').get('data-k')
        if not player_k or not track_k:
            self.raise_no_formats('Unable to extract download token', expected=False)

        vid = int(video_id)
        # Token from player JS getUrl() at pitch=0 / tempo=0
        checksum = sum(map(ord, player_k)) + round(3.3 * math.pi) / 2 + vid + 111 * 9
        salt = int((vid - 150000 + 24235) / 333)
        token = f'{int(checksum):x}zyxwz{vid + 0.9}z{track_k}z{salt}'
        media_url = f'{self._media_host(webpage, video_id)}/dl/minus/{video_id}?t668={token}'
        if track_name:
            media_url += f'&trackname={urllib.parse.quote(track_name)}'
        return media_url

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        artist = self._html_search_regex(
            r'<h1[^>]*>\s*<a[^>]+href="/artist/[^"]+"[^>]*>([^<]+)</a>',
            webpage, 'artist', default=None)
        song = self._html_search_regex(
            r'<span[^>]+class="minustrack-full-title[^"]*"[^>]*>([^<]+)',
            webpage, 'title', default=None)
        track_name = self._html_search_regex(
            r'\bdata-fn="([^"]+)"', webpage, 'track filename', default=None)
        if artist and song:
            title = f'{artist}-{song.strip()}'
        else:
            title = track_name or video_id

        duration = parse_duration(extract_attributes(
            get_element_html_by_id(f'm{video_id}', webpage) or '').get('data-source-dur'))
        media_info = re.search(
            r'(?P<filesize>[\d.]+)\s*MB\s+(?P<tbr>\d+)\s*kbps', webpage)
        description = self._html_search_regex(
            r'(?s)<pre[^>]+id="lyrics-original"[^>]*>(.*?)</pre>',
            webpage, 'song lyrics', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            r'(?s)<th>\s*Uploaded:\s*</th>\s*<td>\s*<span>([^<]+)</span>',
            webpage, 'upload date', default=None))

        return {
            'id': video_id,
            'title': title,
            'url': self._extract_media_url(webpage, video_id, track_name),
            'ext': 'mp3',
            'duration': duration,
            'filesize_approx': float_or_none(
                media_info.group('filesize') if media_info else None, invscale=1000000),
            'tbr': int_or_none(media_info.group('tbr') if media_info else None),
            'upload_date': upload_date,
            'description': description,
            'vcodec': 'none',
        }
