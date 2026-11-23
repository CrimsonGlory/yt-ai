import re

from .common import InfoExtractor
from ..utils import orderedSet


class NZZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nzz\.ch/(?:[^/]+/)*[^/?#]+-ld\.(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.nzz.ch/zuerich/gymizyte/gymizyte-schreiben-schueler-heute-noch-diktate-ld.9153',
        'info_dict': {
            'id': '9153',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://www.nzz.ch/video/nzz-standpunkte/cvp-auf-der-suche-nach-dem-mass-der-mitte-ld.1368112',
        'info_dict': {
            'id': '1368112',
        },
        'playlist_count': 1,
    }]

    def _jwplayer_media_id(self, url):
        return self._search_regex(
            r'cdn\.jwplayer\.com/(?:videos|manifests|v2/media)/([A-Za-z0-9]{8})',
            url or '', 'jwplayer id', default=None)

    def _entries(self, webpage, page_id):
        # JSON-LD VideoObject contentUrls are this article's clips. Related
        # teasers also embed v2/media IDs in the page payload.
        media_ids = []
        for json_ld in self._yield_json_ld(webpage, page_id, default=[]):
            ld_type = json_ld.get('@type')
            if ld_type != 'VideoObject' and 'VideoObject' not in (ld_type or []):
                continue
            media_id = self._jwplayer_media_id(json_ld.get('contentUrl'))
            if media_id:
                media_ids.append(media_id)
        media_ids = orderedSet(media_ids)
        if not media_ids:
            media_ids = orderedSet(re.findall(
                r'cdn\.jwplayer\.com/v2/media/([A-Za-z0-9]{8})', webpage))
        if not media_ids:
            media_ids = orderedSet(re.findall(
                r'cdn\.jwplayer\.com/(?:videos|manifests)/([A-Za-z0-9]{8})', webpage))
        for media_id in media_ids:
            yield self.url_result(
                f'https://cdn.jwplayer.com/v2/media/{media_id}', 'JWPlatform', media_id)
        if media_ids:
            return
        for script in re.findall(r'(?s)<script[^>]* data-hid="jw-video-jw[^>]+>(.+?)</script>', webpage):
            settings = self._search_json(r'var\s+settings\s*=[^{]*', script, 'settings', page_id, fatal=False)
            if entry := self._parse_jwplayer_data(settings, page_id):
                yield entry

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        return self.playlist_result(self._entries(webpage, page_id), page_id)
