from .common import InfoExtractor
from .vimeo import VimeoIE
from ..utils import ExtractorError, filter_dict


class LeCinemaClubIE(InfoExtractor):
    IE_DESC = 'Le Cinéma Club'
    _VALID_URL = (
        r'https?://(?:www\.)?lecinemaclub\.com'
        r'(?:/now-showing(?:/(?P<id>[\w-]+))?/?|/?)'
        r'(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://www.lecinemaclub.com/now-showing/vengeance-is-mine/',
        'md5': 'f23dcd7662378c0cf567fd01bef82516',
        'info_dict': {
            'id': '1215903307',
            'ext': 'mp4',
            'display_id': 'vengeance-is-mine',
            'title': 'VENGEANCE IS MINE',
            'description': 'md5:f6cd1b1de4e9c4f8d1bf5aa27fa9e217',
            'duration': 7140,
            'thumbnail': 'https://www.lecinemaclub.com/wp-content/uploads/2026/08/LCC_VMIA-1200x676.png',
            'uploader': 'LCC',
            'uploader_id': 'user33221439',
            'uploader_url': 'https://vimeo.com/user33221439',
        },
        'params': {
            'format': 'bv*[height<=360][protocol^=m3u8]/bv*',
            'external_downloader': 'ffmpeg',
        },
        'expected_warnings': ['Failed to parse XML: not well-formed'],
        'add_ie': ['Vimeo'],
    }, {
        'url': 'https://www.lecinemaclub.com/',
        'only_matching': True,
    }, {
        'url': 'https://www.lecinemaclub.com/now-showing/',
        'only_matching': True,
    }, {
        'url': 'https://lecinemaclub.com/now-showing/vengeance-is-mine',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_valid_url(url).group('id') or 'now-showing'
        webpage = self._download_webpage(url, display_id)

        # The hero <video> is a short looping preview. The actual film is the
        # Plyr Vimeo iframe / Watch-button `player.vimeo.com/external/{id}.mpd`.
        vimeo_id = self._search_regex(
            (r'<iframe[^>]+src=["\']https?://(?:player\.)?vimeo\.com/video/(\d+)',
             r'class="watch"[^>]+data-url=["\']https?://player\.vimeo\.com/external/(\d+)',
             r'player\.vimeo\.com/external/(\d+)\.mpd'),
            webpage, 'vimeo id', default=None)
        if not vimeo_id:
            raise ExtractorError(
                'No film is currently streaming on Le Cinéma Club', expected=True)

        if display_id == 'now-showing':
            display_id = self._search_regex(
                r'data-url=["\']https?://(?:www\.)?lecinemaclub\.com/now-showing/([^/"\']+)',
                webpage, 'display id', default=display_id)

        return self.url_result(
            VimeoIE._smuggle_referrer(
                f'https://player.vimeo.com/video/{vimeo_id}', url),
            VimeoIE, vimeo_id, url_transparent=True, **filter_dict({
                'display_id': display_id,
                'title': self._search_regex(
                    r'\bdata-title=["\']([^"\']+)', webpage, 'title', default=None),
                'description': self._html_search_regex(
                    r'(?s)<div class="meta">\s*<p>(.+?)</p>',
                    webpage, 'description', default=None),
                'thumbnail': self._og_search_thumbnail(webpage),
            }))
