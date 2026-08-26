import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    smuggle_url,
)


class BFIPlayerIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'bfi:player'
    _VALID_URL = r'https?://player\.bfi\.org\.uk/[^/]+/film/watch-(?P<id>[\w-]+)-online'
    _TESTS = [{
        'url': 'https://player.bfi.org.uk/free/film/watch-callum-turners-3-you-must-see-on-bfi-player-2026-online',
        'md5': '8bee4f86b6ad696b389fca2106b939e5',
        'info_dict': {
            'id': '6399173210112',
            'ext': 'mp4',
            'title': "Callum Turner's 3 You Must See on BFI Player",
            'uploader_id': '6057949427001',
            'duration': 117.931,
            'timestamp': 1782224497,
            'upload_date': '20260623',
            'tags': ['free', 'archived'],
            'thumbnail': r're:https?://.+\.jpg',
        },
        'add_ie': ['BrightcoveNew'],
    }, {
        'url': 'https://player.bfi.org.uk/free/film/watch-computer-doctor-1974-online',
        'info_dict': {
            'id': 'computer-doctor-1974',
            'ext': 'mp4',
        },
        'skip': 'This film has moved to BFI Replay',
    }, {
        'url': 'https://player.bfi.org.uk/rentals/film/watch-my-fathers-island-2025-online',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        entries = []
        for player_el in re.findall(r'(?s)<video-js[^>]*>', webpage):
            attrs = extract_attributes(player_el)
            bc_id = attrs.get('data-video-id') or attrs.get('data-ref-id')
            account_id = attrs.get('data-account') or attrs.get('data-acid')
            if not bc_id or not account_id:
                continue
            player_id = attrs.get('data-player') or attrs.get('data-pid') or 'default'
            embed = attrs.get('data-embed') or 'default'
            entries.append(self.url_result(
                smuggle_url(
                    f'https://players.brightcove.net/{account_id}/{player_id}_{embed}/index.html?videoId={bc_id}',
                    {'referrer': url, 'geo_countries': ['GB']}),
                BrightcoveNewIE, bc_id, attrs.get('data-label')))
        if not entries:
            raise ExtractorError('Unable to find Brightcove player', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, video_id)
