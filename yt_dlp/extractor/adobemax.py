from .adobetv import AdobeTVVideoIE
from .common import InfoExtractor
from ..utils import urljoin


class AdobeMaxIE(InfoExtractor):
    IE_NAME = 'adobemax'
    IE_DESC = 'Adobe MAX'
    _VALID_URL = (
        r'https?://(?:www\.)?adobe\.com/(?:[a-z]{2}(?:_[a-z]{2})?/)?'
        r'(?:max/\d{4}/sessions/(?P<id>[^/?#]+?)(?:\.html)?/?|'
        r'www-fragments/max/\d{4}/marquees/(?P<fragment_id>[^/?#]+)/ondemand\.live\.html)/?(?:$|[?#])')
    _TESTS = [{
        'url': 'https://www.adobe.com/max/2025/sessions/opening-keynote-gs1.html',
        'md5': '25f9ebbc241531aca296f99bf7de9851',
        'info_dict': {
            'id': '3458790',
            'ext': 'mp4',
            'title': 'GS1 - Opening Keynote',
            'description': 'Opening Keynote',
            'duration': 10996.078,
            'thumbnail': r're:https?://images-tv\.adobe\.com/.+\.jpg',
        },
        'params': {
            'format': 'mpeg4-Low',
        },
        'add_ie': [AdobeTVVideoIE.ie_key()],
    }, {
        'url': 'https://www.adobe.com/www-fragments/max/2025/marquees/GS1/ondemand.live.html',
        'only_matching': True,
    }, {
        'url': 'https://www.adobe.com/max/2025/sessions/video-super-session-artistry-in-motion-ss2.html',
        'only_matching': True,
    }, {
        'url': 'https://www.adobe.com/max/2020/sessions/creative-luminary-marc-levoy-od5203.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id') or mobj.group('fragment_id')
        webpage = self._download_webpage(url, display_id, impersonate=True)

        adobe_tv_url = self._search_regex(
            r'((?:https?:)?//video\.tv\.adobe\.com/v/\d+)',
            webpage, 'adobe tv url', default=None)
        if not adobe_tv_url:
            fragment_path = self._search_regex(
                r'(/www-fragments/max/\d{4}/marquees/[^/?#]+/ondemand\.live\.html)',
                webpage, 'on-demand fragment')
            fragment = self._download_webpage(
                urljoin(url, fragment_path), display_id,
                'Downloading on-demand fragment', impersonate=True)
            adobe_tv_url = self._search_regex(
                r'((?:https?:)?//video\.tv\.adobe\.com/v/\d+)',
                fragment, 'adobe tv url')

        return self.url_result(
            self._proto_relative_url(adobe_tv_url), AdobeTVVideoIE)
