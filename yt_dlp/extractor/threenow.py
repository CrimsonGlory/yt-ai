import re
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    join_nonempty,
    parse_age_limit,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ThreeNowIE(InfoExtractor):
    IE_NAME = 'ThreeNow'
    IE_DESC = 'ThreeNow live TV'
    _VALID_URL = r'https?://(?:www\.)?threenow\.co\.nz/(?i:live-tv-guide)/(?P<id>[^/?#]+)'
    _API_BASE = 'https://now-api.fullscreen.nz/v5/'
    _TESTS = [{
        'url': 'https://www.threenow.co.nz/live-tv-guide/three',
        'info_dict': {
            'id': 'three',
            'ext': 'mp4',
            'display_id': 'three',
            'title': r're:Three',
            'description': str,
            'thumbnail': r're:https?://.+',
            'channel': 'Three',
            'channel_id': 'three',
            'age_limit': int,
            'genres': list,
            'season': str,
            'season_number': int,
            'episode': str,
            'episode_number': int,
            'is_live': True,
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://www.threenow.co.nz/live-tv-guide/three-now-sport-1',
        'only_matching': True,
    }, {
        'url': 'https://www.threenow.co.nz/Live-TV-Guide/cnn-headlines-international',
        'only_matching': True,
    }]

    def _channel_slug(self, display_name):
        # Ember.String.dasherize used by ThreeNow as urlSlug
        slug = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', display_name or '')
        slug = re.sub(r'[?!]', '', slug).lower()
        return re.sub(r'[ _]', '-', slug)

    def _rewrite_image(self, url):
        if not url:
            return None
        return url_or_none(url.replace('[width]', '1920').replace('[height]', '1080'))

    def _current_broadcast(self, broadcasts):
        now = int(time.time())
        fallback = None
        for broadcast in broadcasts or []:
            if not isinstance(broadcast, dict):
                continue
            if fallback is None:
                fallback = broadcast
            start = parse_iso8601(broadcast.get('startDate'))
            end = parse_iso8601(broadcast.get('endDate'))
            if start is not None and end is not None and start <= now <= end:
                return broadcast
        return fallback

    def _real_extract(self, url):
        slug = urllib.parse.unquote(self._match_id(url)).lower()
        epg = self._download_json(
            f'{self._API_BASE}live-epg', slug, 'Downloading live EPG JSON', headers={
                'Accept': 'application/json',
                'devicetype': 'browser',
                'version': '4.1',
                'Origin': 'https://www.threenow.co.nz',
                'Referer': 'https://www.threenow.co.nz/',
            })

        channel = None
        for candidate in traverse_obj(epg, ('channels', ..., {dict})):
            names = {
                (candidate.get('channelId') or '').lower(),
                self._channel_slug(candidate.get('displayName')),
            }
            if slug in names:
                channel = candidate
                break
        if not channel:
            raise ExtractorError(f'Unable to find live channel {slug}', expected=True)

        channel_id = channel.get('channelId') or slug
        channel_name = channel.get('displayName') or channel_id
        hls_url = traverse_obj(channel, ('videoRenditions', 'hlsUrl', {url_or_none}))
        if not hls_url:
            raise ExtractorError(f'No HLS URL for channel {channel_id}', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, channel_id, 'mp4', m3u8_id='hls', live=True)

        broadcast = self._current_broadcast(channel.get('broadcasts')) or {}
        program_title = (
            traverse_obj(broadcast, ('title', {str}))
            or traverse_obj(broadcast, ('episodeName', {str})))
        genre = traverse_obj(broadcast, ('genre', {str}))

        return {
            'id': channel_id,
            'display_id': slug,
            'title': join_nonempty(channel_name, program_title, delim=': ') or channel_name,
            'description': (
                traverse_obj(broadcast, ('episodeSynopsis', {str}))
                or traverse_obj(broadcast, ('showSynopsis', {str}))),
            'thumbnail': self._rewrite_image(
                traverse_obj(broadcast, ('episodeImage', {str}))
                or traverse_obj(broadcast, ('seriesImage', {str}))),
            'channel': channel_name,
            'channel_id': channel_id,
            'genres': [genre] if genre else None,
            'episode': traverse_obj(broadcast, ('episodeName', {str})),
            'episode_number': traverse_obj(broadcast, ('episodeNumber', {int_or_none})),
            'season_number': traverse_obj(broadcast, ('seriesNumber', {int_or_none})),
            'age_limit': parse_age_limit(traverse_obj(broadcast, ('classification', {str}))),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }
