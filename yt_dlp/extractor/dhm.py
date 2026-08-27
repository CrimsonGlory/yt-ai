import re

from .common import InfoExtractor
from ..utils import parse_duration, url_basename, urljoin


class DHMIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'Deutsches Historisches Museum'
    _VALID_URL = r'https?://(?:www\.)?dhm\.de/(?:filmarchiv/(?:[^/?#]+/)+|journal/beitrag/)(?P<id>[^/?#]+)/?'

    _TESTS = [{
        'url': 'https://www.dhm.de/journal/beitrag/man-konnte-ploetzlich-nur-noch-unter-lebensgefahr-dieses-land-verlassen-renate-werwigk-schneider-erinnert-sich-an-den-bau-der-berliner-mauer',
        'md5': '59df5e5aff667d3840e29732a2054844',
        'info_dict': {
            'id': 'C20260211_1062',
            'ext': 'mp4',
            'display_id': 'man-konnte-ploetzlich-nur-noch-unter-lebensgefahr-dieses-land-verlassen-renate-werwigk-schneider-erinnert-sich-an-den-bau-der-berliner-mauer',
            'title': '„Man konnte plötzlich nur noch unter Lebensgefahr dieses Land verlassen“ – Renate Werwigk-Schneider erinnert sich an den Bau der Berliner Mauer',
            'thumbnail': r're:https?://www\.dhm\.de/journal/.+\.(?:webp|jpg|jpeg|png)',
        },
    }, {
        'url': 'http://www.dhm.de/filmarchiv/die-filme/the-marshallplan-at-work-in-west-germany/',
        'skip': 'video gone',
        'md5': '11c475f670209bf6acca0b2b7ef51827',
        'info_dict': {
            'id': 'the-marshallplan-at-work-in-west-germany',
            'ext': 'flv',
            'title': 'MARSHALL PLAN AT WORK IN WESTERN GERMANY, THE',
            'description': 'md5:1fabd480c153f97b07add61c44407c82',
            'duration': 660,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://www.dhm.de/filmarchiv/02-mapping-the-wall/peter-g/rolle-1/',
        'skip': 'video gone',
        'md5': '09890226332476a3e3f6f2cb74734aa5',
        'info_dict': {
            'id': 'rolle-1',
            'ext': 'flv',
            'title': 'ROLLE 1',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.dhm.de/journal/beitrag/vergleichsgeschichte-zweier-gewaltregime-kurator-stephan-malinowski-ueber-die-kommende-ausstellung-umstrittene-verwandtschaft-koloniale-und-nationalsozialistische-gewalt',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        playlist_url = self._search_regex(
            r"file\s*:\s*'([^']+)'", webpage, 'playlist url', default=None)
        if playlist_url:
            entries = self._extract_xspf_playlist(playlist_url, display_id)

            title = self._search_regex(
                [r'dc:title="([^"]+)"', r'<title> &raquo;([^<]+)</title>'],
                webpage, 'title').strip()
            description = self._html_search_regex(
                r'<p><strong>Description:</strong>(.+?)</p>',
                webpage, 'description', default=None)
            duration = parse_duration(self._search_regex(
                r'<em>Length\s*</em>\s*:\s*</strong>([^<]+)',
                webpage, 'duration', default=None))

            entries[0].update({
                'title': title,
                'description': description,
                'duration': duration,
            })

            return self.playlist_result(entries, display_id)

        media_url = urljoin(url, self._search_regex(
            r'data-src=(["\'])(?P<url>(?:(?!\1).)+\.(?:mp4|m4a|webm|mp3)(?:\?(?:(?!\1).)*)?)\1',
            webpage, 'media url', group='url'))

        return {
            'id': url_basename(media_url).rsplit('.', 1)[0],
            'display_id': display_id,
            'url': media_url,
            'title': self._og_search_title(webpage) or self._html_extract_title(webpage),
            'thumbnail': urljoin(url, self._search_regex(
                r'data-src=["\'][^"\']+\.(?:mp4|m4a|webm|mp3)(?:\?[^"\']*)?["\'][^>]*>\s*<img[^>]+src=(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage, 'thumbnail', default=None, group='url', flags=re.DOTALL)),
        }
