from .common import InfoExtractor
from ..utils import unescapeHTML, url_or_none


class VODPlatformIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www\.)?vod-platform\.net|embed\.kwikmotion\.com)/[eE]mbed/(?P<id>[^/?#]+)'
    _EMBED_REGEX = [r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:(?:www\.)?vod-platform\.net|embed\.kwikmotion\.com)/[eE]mbed/.+?)\1']
    _TESTS = [{
        # from http://www.lbcgroup.tv/watch/chapter/29143/52844/%D8%A7%D9%84%D9%86%D8%B5%D8%B1%D8%A9-%D9%81%D9%8A-%D8%B6%D9%8A%D8%A7%D9%81%D8%A9-%D8%A7%D9%84%D9%80-cnn/ar
        'url': 'http://vod-platform.net/embed/RufMcytHDolTH1MuKHY9Fw',
        'skip': 'video gone',
        'md5': '1db2b7249ce383d6be96499006e951fc',
        'info_dict': {
            'id': 'RufMcytHDolTH1MuKHY9Fw',
            'ext': 'mp4',
            'title': 'LBCi News_ النصرة في ضيافة الـ "سي.أن.أن"',
        },
    }, {
        # Public KWIKmotion demo video (successor of vod-platform.net embeds)
        'url': 'https://embed.kwikmotion.com/embed/kKdJ0lAYFf6MkL1G4U2iA',
        'md5': '69e2b5fad996be0150d94c4f00196ab9',
        'info_dict': {
            'id': 'kKdJ0lAYFf6MkL1G4U2iA',
            'ext': 'mp4',
            'title': 'lS9rEcNShKWwvCW3lAxdw-20-Original-8277293',
            'thumbnail': r're:https?://embed\.kwikmotion\.com/.+',
        },
    }, {
        'url': 'http://embed.kwikmotion.com/embed/RufMcytHDolTH1MuKHY9Fw',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        hidden_inputs = self._hidden_inputs(webpage)
        title = unescapeHTML(
            self._og_search_title(webpage, default=None)
            or hidden_inputs.get('HiddenVideoTitle'))
        hls_url = url_or_none(
            hidden_inputs.get('HiddenmyhHlsLink') or hidden_inputs.get('HiddenmyDashLink'))
        if not hls_url:
            self.raise_no_formats('Unable to extract stream URL', video_id=video_id)

        formats = self._extract_wowza_formats(
            hls_url, video_id, skip_protocols=['f4m', 'smil'])

        return {
            'id': video_id,
            'title': title,
            'thumbnail': hidden_inputs.get('HiddenThumbnail') or self._og_search_thumbnail(webpage),
            'formats': formats,
        }
