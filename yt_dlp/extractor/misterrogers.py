import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    smuggle_url,
)


class MisterRogersBaseIE(InfoExtractor):
    _ACCOUNT_ID = '5771154052001'
    _PLAYER_ID = 'default'
    _EMBED = 'default'

    def _brightcove_result(self, video_id, url, account_id=None, player_id=None, embed=None):
        account_id = account_id or self._ACCOUNT_ID
        player_id = player_id or self._PLAYER_ID
        embed = embed or self._EMBED
        bc_url = f'https://players.brightcove.net/{account_id}/{player_id}_{embed}/index.html?videoId={video_id}'
        return self.url_result(
            smuggle_url(bc_url, {'referrer': url}), BrightcoveNewIE, video_id)

    def _parse_brightcove_players(self, webpage, url):
        entries = []
        seen = set()
        for video_tag in re.findall(
                r'<video(?:-js)?\b[^>]+\bdata-video-id=["\']?\d+[^>]*>', webpage):
            attrs = extract_attributes(video_tag)
            video_id = attrs.get('data-video-id')
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            entries.append(self._brightcove_result(
                video_id, url,
                account_id=attrs.get('data-account'),
                player_id=attrs.get('data-player'),
                embed=attrs.get('data-embed')))
        return entries


class MisterRogersIE(MisterRogersBaseIE):
    IE_NAME = 'misterrogers'
    IE_DESC = "Mister Rogers' Neighborhood"
    _VALID_URL = r'https?://(?:www\.)?misterrogers\.org/videos/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.misterrogers.org/videos/how-people-make-macaroni/',
        'md5': '0c7fbc5e48d21948d6c042aa8d3e24a2',
        'info_dict': {
            'id': '5815791724001',
            'ext': 'mp4',
            'title': 'Macaroni (1716)',
            'duration': 283.85,
            'timestamp': 1532980406,
            'upload_date': '20180730',
            'uploader_id': '5771154052001',
            'thumbnail': r're:https?://.+\.jpg',
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://www.misterrogers.org/videos/death-of-a-goldfish/',
        'only_matching': True,
    }, {
        'url': 'https://misterrogers.org/videos/how-the-trolley-works',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        entries = self._parse_brightcove_players(webpage, url)
        if entries:
            return entries[0]

        bc_url = BrightcoveNewIE._extract_url(self, webpage)
        if not bc_url:
            raise ExtractorError('Unable to extract Brightcove video', expected=True)
        return self.url_result(
            smuggle_url(bc_url, {'referrer': url}), BrightcoveNewIE, display_id)


class MisterRogersPlaylistIE(MisterRogersBaseIE):
    IE_NAME = 'misterrogers:playlist'
    IE_DESC = "Mister Rogers' Neighborhood playlists"
    _VALID_URL = r'https?://(?:www\.)?misterrogers\.org/video-playlist/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.misterrogers.org/video-playlist/factory-visits/',
        'info_dict': {
            'id': 'factory-visits',
            'title': "Factory Visits - Mister Rogers' Neighborhood",
        },
        'playlist_mincount': 6,
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.misterrogers.org/video-playlist/daniel/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        entries = self._parse_brightcove_players(webpage, url)
        if not entries:
            raise ExtractorError('Unable to extract Brightcove videos', expected=True)
        return self.playlist_result(
            entries, playlist_id,
            self._og_search_title(webpage, default=None) or self._html_extract_title(webpage))
