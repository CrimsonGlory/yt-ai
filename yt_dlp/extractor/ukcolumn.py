from .common import InfoExtractor
from .vimeo import VimeoIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    unescapeHTML,
    urljoin,
)


class UkColumnIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'ukcolumn'
    _VALID_URL = r'(?i)https?://(?:www\.)?ukcolumn\.org(/index\.php)?/(?:video|ukcolumn-news)/(?P<id>[-a-z0-9]+)'

    _TESTS = [{
        'url': 'https://www.ukcolumn.org/ukcolumn-news/uk-column-news-28th-april-2021',
        'skip': 'Rate limited',
        'info_dict': {
            'id': '541632443',
            'ext': 'mp4',
            'title': 'UK Column News - 28th April 2021',
            'uploader_id': 'ukcolumn',
            'uploader': 'UK Column',
        },
        'add_ie': [VimeoIE.ie_key()],
        'expected_warnings': ['Unable to download JSON metadata'],
        'params': {
            'skip_download': 'Handled by Vimeo',
        },
    }, {
        'url': 'https://www.ukcolumn.org/video/insight-eu-military-unification',
        'skip': 'Rate limited',
        'info_dict': {
            'id': 'Fzbnb9t7XAw',
            'ext': 'mp4',
            'title': 'Insight: EU Military Unification',
            'uploader_id': 'ukcolumn',
            'description': 'md5:29a207965271af89baa0bc191f5de576',
            'uploader': 'UK Column',
            'upload_date': '20170514',
        },
        'add_ie': [YoutubeIE.ie_key()],
        'params': {
            'skip_download': 'Handled by Youtube',
        },
    }, {
        'url': 'https://www.ukcolumn.org/index.php/ukcolumn-news/uk-column-news-30th-april-2021',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        odysee_url = self._search_regex(
            r'(https?://odysee\.com/[^"\'&]+)', unescapeHTML(webpage),
            'Odysee URL', default=None)
        if odysee_url:
            return {
                '_type': 'url_transparent',
                'title': self._og_search_title(webpage),
                'url': odysee_url.replace('%3A', ':'),
                'ie_key': 'LBRY',
            }

        oembed_url = urljoin(url, unescapeHTML(self._search_regex(
            r'<iframe[^>]+src=(["\'])(?P<url>/media/oembed\?url=.+?)\1',
            webpage, 'OEmbed URL', group='url')))
        oembed_webpage = self._download_webpage(
            oembed_url, display_id, note='Downloading OEmbed page')

        ie, video_url = YoutubeIE, YoutubeIE._extract_url(oembed_webpage)
        if not video_url:
            ie, video_url = VimeoIE, VimeoIE._extract_url(url, oembed_webpage)
        if not video_url:
            odysee_url = self._search_regex(
                r'(https?://odysee\.com/[^"\'&]+)', unescapeHTML(oembed_webpage),
                'Odysee URL', default=None)
            if odysee_url:
                return {
                    '_type': 'url_transparent',
                    'title': self._og_search_title(webpage),
                    'url': unescapeHTML(odysee_url),
                    'ie_key': 'LBRY',
                }
            raise ExtractorError('No embedded video found')

        return {
            '_type': 'url_transparent',
            'title': self._og_search_title(webpage),
            'url': video_url,
            'ie_key': ie.ie_key(),
        }
