from .common import InfoExtractor
from .jwplatform import JWPlatformIE


class MetacriticIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?metacritic\.com/(?:movie|game|tv)/(?P<id>[^/?#]+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?metacritic\.com/.+?/trailers/(?P<id>\d+)',
    )
    _TESTS = [{
        'url': 'https://www.metacritic.com/movie/the-godfather/',
        'md5': 'e3f89a3ae06f8c723873355fa2dffb17',
        'info_dict': {
            'id': 'zIUMZ9F8',
            'ext': 'mp4',
            'title': 'The Godfather (Accolades Trailer)',
            'display_id': 'the-godfather',
            'description': '',
            'duration': 58.0,
            'thumbnail': r're:https?://cdn\.jwplayer\.com/v2/media/.+',
            'timestamp': 1751260213,
            'upload_date': '20250630',
        },
        'params': {
            # Prefer progressive MP4 so the live test is not HLS-only
            'format': 'best[protocol=https][ext=mp4]/best',
        },
    }, {
        'url': 'http://www.metacritic.com/game/playstation-4/infamous-second-son/trailers/3698222',
        'info_dict': {
            'id': '3698222',
            'ext': 'mp4',
            'title': 'inFamous: Second Son - inSide Sucker Punch: Smoke & Mirrors',
            'description': 'Take a peak behind-the-scenes to see how Sucker Punch brings smoke into the universe of inFAMOUS Second Son on the PS4.',
            'duration': 221,
        },
        'skip': 'Old trailer URLs no longer serve the original clips',
    }, {
        'url': 'http://www.metacritic.com/game/playstation-4/tales-from-the-borderlands-a-telltale-game-series/trailers/5740315',
        'skip': 'video gone',
        'info_dict': {
            'id': '5740315',
            'ext': 'mp4',
            'title': 'Tales from the Borderlands - Finale: The Vault of the Traveler',
            'description': 'In the final episode of the season, all hell breaks loose. Jack is now in control of Helios\' systems, and he\'s ready to reclaim his rightful place as king of Hyperion (with or without you).',
            'duration': 114,
        },
    }, {
        'url': 'https://www.metacritic.com/game/elden-ring/',
        'only_matching': True,
    }, {
        'url': 'https://www.metacritic.com/tv/the-pitt/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        jw_id = self._search_regex(
            r'https?://cdn\.jwplayer\.com/manifests/([a-zA-Z0-9]{8})\.m3u8',
            webpage, 'jwplayer id')
        return self.url_result(
            f'jwplatform:{jw_id}', JWPlatformIE, jw_id,
            url_transparent=True, display_id=display_id)
