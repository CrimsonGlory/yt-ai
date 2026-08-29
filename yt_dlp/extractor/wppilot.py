import json
import random
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    try_get,
)


class WPPilotBaseIE(InfoExtractor):
    _VIDEO_URL = 'https://pilot.wp.pl/api/v3/channel/%s'
    _VIDEO_GUEST_URL = 'https://pilot.wp.pl/api/v2/guest/channel/%s'
    _CHANNEL_LIST_URL = 'https://pilot.wp.pl/api/v1/guest/channels/list'
    # Guest playback is limited to the EU, Norway, and Iceland. The stream
    # API checks the real client IP; X-Forwarded-For is ignored.
    _GEO_COUNTRIES = ['PL']
    _GEO_BYPASS = False

    _HEADERS_WEB = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Referer': 'https://pilot.wp.pl/tv/',
    }

    def _get_channel_list(self, cache=True):
        if cache is True:
            cache_res = self.cache.load('wppilot', 'channel-list')
            if cache_res:
                return cache_res, True
        channel_list = try_get(self._download_json(
            self._CHANNEL_LIST_URL, None, 'Downloading channel list',
            headers=self._HEADERS_WEB), lambda x: x['data'])
        if not channel_list:
            raise ExtractorError('Unable to find the channel list')
        self.cache.store('wppilot', 'channel-list', channel_list)
        return channel_list, False

    def _parse_channel(self, chan):
        return {
            'id': str(chan['id']),
            'title': chan['name'],
            'is_live': True,
            'thumbnails': [{
                'id': key,
                'url': chan[key],
            } for key in ('thumbnail', 'thumbnail_mobile', 'icon') if chan.get(key)],
        }


class WPPilotIE(WPPilotBaseIE):
    _VALID_URL = r'(?:https?://pilot\.wp\.pl/tv/?#|wppilot:)(?P<id>[a-z\d-]+)'
    IE_NAME = 'wppilot'

    _TESTS = [{
        'url': 'https://pilot.wp.pl/tv/#telewizja-wp-hd',
        'info_dict': {
            'id': '158',
            'ext': 'mp4',
            'title': 'Telewizja WP HD',
        },
        'params': {
            'format': 'bestvideo',
        },
        'skip': 'geo-restricted to the EU (Norway/Iceland); guest stream API returns user_outside_eu (X-Forwarded-For is ignored)',
    }, {
        # audio only
        'url': 'https://pilot.wp.pl/tv/#radio-nowy-swiat',
        'info_dict': {
            'id': '238',
            'ext': 'm4a',
            'title': 'Radio Nowy Świat',
        },
        'params': {
            'format': 'bestaudio',
        },
        'skip': 'not accessible for guests (guest_channel_not_accessible); Radio Nowy Świat has guest_timeout=0',
    }, {
        'url': 'wppilot:9',
        'only_matching': True,
    }]

    def _get_channel(self, id_or_slug):
        video_list, is_cached = self._get_channel_list(cache=True)
        key = 'id' if re.match(r'^\d+$', id_or_slug) else 'slug'
        for video in video_list:
            if video.get(key) == id_or_slug:
                return self._parse_channel(video)
        # if cached channel not found, download and retry
        if is_cached:
            video_list, _ = self._get_channel_list(cache=False)
            for video in video_list:
                if video.get(key) == id_or_slug:
                    return self._parse_channel(video)
        raise ExtractorError('Channel not found')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        channel = self._get_channel(video_id)
        video_id = str(channel['id'])

        is_authorized = next((c for c in self.cookiejar if c.name == 'netviapisessid'), None)
        # cookies starting with "g:" are assigned to guests
        is_authorized = is_authorized is not None and not is_authorized.value.startswith('g:')

        video = self._download_json(
            (self._VIDEO_URL if is_authorized else self._VIDEO_GUEST_URL) % video_id,
            video_id, query={
                'device_type': 'web',
            }, headers=self._HEADERS_WEB,
            expected_status=(200, 403, 422))

        error = try_get(video, lambda x: x['_meta']['error']['name'])
        if error == 'user_outside_eu':
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        stream_token = try_get(video, lambda x: x['_meta']['error']['info']['stream_token'])
        if stream_token:
            close = self._download_json(
                'https://pilot.wp.pl/api/v1/channels/close', video_id,
                'Invalidating previous stream session', headers=self._HEADERS_WEB,
                data=json.dumps({
                    'channelId': video_id,
                    't': stream_token,
                }).encode())
            if try_get(close, lambda x: x['data']['status']) == 'ok':
                return self.url_result(url, ie=WPPilotIE.ie_key())

        streams = try_get(video, lambda x: x['data']['stream_channel']['streams'])
        if not streams:
            if error in ('guest_channel_not_accessible', 'user_channel_not_accessible', 'not_authorized'):
                self.raise_login_required()
            raise ExtractorError(error or 'Unable to extract stream', expected=True)

        formats = []

        for fmt in streams:
            # live DASH does not work for now
            # if fmt['type'] == 'dash@live:abr':
            #     formats.extend(
            #         self._extract_mpd_formats(
            #             random.choice(fmt['url']), video_id))
            if fmt['type'] == 'hls@live:abr':
                formats.extend(
                    self._extract_m3u8_formats(
                        random.choice(fmt['url']),
                        video_id, live=True))

        channel['formats'] = formats
        return channel


class WPPilotChannelsIE(WPPilotBaseIE):
    _VALID_URL = r'(?:https?://pilot\.wp\.pl/(?:tv/?)?(?:\?[^#]*)?#?|wppilot:)$'
    IE_NAME = 'wppilot:channels'

    _TESTS = [{
        'url': 'wppilot:',
        'info_dict': {
            'id': 'wppilot',
            'title': 'WP Pilot',
        },
        'playlist_mincount': 100,
    }, {
        'url': 'https://pilot.wp.pl/',
        'only_matching': True,
    }]

    def _entries(self):
        channel_list, _ = self._get_channel_list()
        for chan in channel_list:
            entry = self._parse_channel(chan)
            entry.update({
                '_type': 'url_transparent',
                'url': f'wppilot:{chan["id"]}',
                'ie_key': WPPilotIE.ie_key(),
            })
            yield entry

    def _real_extract(self, url):
        return self.playlist_result(self._entries(), 'wppilot', 'WP Pilot')
