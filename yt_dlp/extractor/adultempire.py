import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    merge_dicts,
    orderedSet,
    parse_duration,
    strip_or_none,
    unified_strdate,
    url_or_none,
    urljoin,
)


class AdultEmpireIE(InfoExtractor):
    IE_NAME = 'adultempire'
    IE_DESC = 'Adult Empire'
    _VALID_URL = [
        r'https?://(?:www\.)?adultempire\.com/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?(?:[?#]|$)',
        r'https?://(?:www\.)?adultempire\.com/gw/player/\?(?:[^#]*?&)?item_id=(?P<id>\d+)',
    ]
    _TESTS = [{
        'url': 'https://www.adultempire.com/4738510/tiffany-watsons-1st-dp-porn-videos.html',
        'md5': 'b83ae382a6f2b1e6ba953e9b6ded22c9',
        'info_dict': {
            'id': '4738510',
            'ext': 'mp4',
            'display_id': 'tiffany-watsons-1st-dp-porn-videos',
            'title': "Tiffany Watson's 1st DP",
            'description': 'md5:d03e5d2f66f52575120ab124bb0a72d1',
            'thumbnail': r're:https://caps1cdn\.adultempire\.com/.+\.jpg',
            'duration': 2820,
            'timestamp': 1711929600,
            'upload_date': '20240401',
            'release_date': '20240330',
            'uploader': 'Elegant Angel Select',
            'uploader_url': 'https://www.adultempire.com/96576/studio/elegant-angel-select-studios.html',
            'cast': ['Tiffany Watson', 'John Strong', 'Zac Wild'],
            'tags': 'count:19',
            'age_limit': 18,
            'width': 720,
            'height': 405,
        },
    }, {
        'url': 'https://www.adultempire.com/4738510',
        'only_matching': True,
    }, {
        'url': 'https://www.adultempire.com/gw/player/?item_id=4738510&type=trailer&site=95ae5f6e21754ad4b0f877d0b7c403ab',
        'only_matching': True,
    }, {
        'url': 'https://adultempire.com/4823920/all-or-nothing-a-hailey-rose-showcase-porn-videos.html',
        'only_matching': True,
    }]

    @staticmethod
    def _clean_title(title):
        title = strip_or_none(title)
        if not title:
            return None
        title = re.sub(r'\s*\|\s*(?:Watch Video - )?AdultEmpire\.com\s*$', '', title, flags=re.I)
        title = re.sub(r'^(?:Trailer from|Free Preview of)\s+', '', title, flags=re.I)
        return strip_or_none(title)

    def _confirm_age(self, video_id):
        cookies = self._get_cookies('https://www.adultempire.com/')
        if getattr(cookies.get('ageConfirmed'), 'value', None) == 'true':
            return
        self.report_age_confirmation()
        self._set_cookie('www.adultempire.com', 'ageConfirmed', 'true')
        self._download_webpage(
            'https://www.adultempire.com/Account/AgeConfirmation',
            video_id, 'Submitting age confirmation', fatal=False,
            query={'ageConfirmationClicked': 'true'})

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.groupdict().get('display_id')
        if display_id:
            display_id = display_id.removesuffix('.html')

        self._confirm_age(video_id)

        webpage = None
        if '/gw/player/' not in urllib.parse.urlparse(url).path:
            webpage = self._download_webpage(url, video_id)
        else:
            webpage = self._download_webpage(
                f'https://www.adultempire.com/{video_id}', video_id,
                'Downloading product page', fatal=False)

        player = self._download_webpage(
            'https://www.adultempire.com/gw/player/', video_id,
            'Downloading trailer player', query={
                'item_id': video_id,
                'type': 'trailer',
            })

        player_ld = self._search_json_ld(
            player, video_id, expected_type='VideoObject', default={})
        page_ld = self._search_json_ld(webpage, video_id, default={}) if webpage else {}
        info = merge_dicts(page_ld, player_ld)

        video_url = url_or_none(info.pop('url', None)) or self._og_search_video_url(
            player, default=None)
        if not video_url:
            raise ExtractorError('No public trailer found', expected=True)
        info.pop('ext', None)
        info.pop('thumbnails', None)

        title = (
            strip_or_none(self._html_search_regex(
                r'<h1[^>]+class="[^"]*movie-page__heading__title[^"]*"[^>]*>([^<]+)',
                webpage or '', 'title', default=None))
            or self._clean_title(info.get('title'))
            or self._clean_title(self._og_search_title(webpage or player, default=None)))

        studio_path, studio = self._search_regex(
            r'Studio:\s*</small>\s*<a[^>]+href="([^"]+)"[^>]*>([^<]+)',
            webpage or '', 'studio', default=(None, None), group=(1, 2))

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': (
                self._og_search_description(player, default=None)
                or info.get('description')
                or self._og_search_description(webpage or '', default=None)),
            'thumbnail': (
                self._og_search_thumbnail(player, default=None)
                or self._og_search_thumbnail(webpage or '', default=None)),
            'duration': parse_duration(self._search_regex(
                r'Length:\s*</small>\s*([^<]+)', webpage or '', 'duration', default=None)),
            'release_date': unified_strdate(strip_or_none(self._search_regex(
                r'Released:</small>\s*([^<]+)', webpage or '', 'release date', default=None))),
            'uploader': strip_or_none(studio),
            'uploader_url': urljoin('https://www.adultempire.com', studio_path) if studio_path else None,
            'cast': orderedSet(re.findall(
                r'<meta[^>]+(?:name|property)=["\']og[.:]video[.:]actor["\'][^>]+content=["\']([^"\']+)',
                player)),
            'tags': orderedSet(re.findall(
                r'<meta[^>]+(?:name|property)=["\']og[.:]video[.:]tag["\'][^>]+content=["\']([^"\']+)',
                player)),
            'width': int_or_none(self._og_search_property('video:width', player, default=None)),
            'height': int_or_none(self._og_search_property('video:height', player, default=None)),
            'age_limit': self._rta_search(player) or self._rta_search(webpage or '') or 18,
        }, info)
