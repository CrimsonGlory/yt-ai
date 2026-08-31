import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    urljoin,
)
from ..utils.traversal import traverse_obj


def _parse_ark_timestamp(ark_start):
    if not ark_start:
        return None
    return parse_iso8601(
        f'{ark_start[:4]}-{ark_start[4:6]}-{ark_start[6:8]}T'
        f'{ark_start[9:11]}:{ark_start[11:13]}:{ark_start[13:15]}Z')


class SpinitronIE(InfoExtractor):
    IE_NAME = 'spinitron'
    IE_DESC = 'Spinitron'
    _VALID_URL = r'https?://(?:www\.)?spinitron\.com/(?P<station>[^/?#]+)/pl/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://spinitron.com/KPOV/pl/22946778/Calling-All-Cowboys',
        'md5': '2732de5b7b2db252e780eaefbbd4c2d2',
        'info_dict': {
            'id': '22946778',
            'ext': 'mp4',
            'title': 'Calling All Cowboys Sun Aug 30 with Chuckaroo The Buckaroo on 88.9FM KPOV Bend',
            'description': 'md5:e41316b6bf2a1e2c7f81fc94c137429e',
            'thumbnail': 'https://spinitron.com/images/Show/01/18/11860-img_show.225x225.jpg?v=1675713243',
            'timestamp': 1788123600,
            'upload_date': '20260830',
            'series': 'Calling All Cowboys',
            'series_id': '11860',
            'uploader': '88.9FM KPOV Bend',
            'uploader_id': 'KPOV',
            'channel': '88.9FM KPOV Bend',
            'channel_id': 'KPOV',
            'channel_url': 'https://spinitron.com/KPOV/',
            'creators': ['Chuckaroo The Buckaroo'],
            'genres': ['Music'],
        },
    }, {
        'url': 'https://spinitron.com/KPOV/pl/19695954/Calling-All-Cowboys',
        'only_matching': True,
    }, {
        'url': 'https://spinitron.com/KPOV/pl/22946778',
        'only_matching': True,
    }, {
        'url': 'https://www.spinitron.com/KPOV/pl/22946778/Calling-All-Cowboys',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        station, playlist_id = self._match_valid_url(url).group('station', 'id')
        webpage = self._download_webpage(url, playlist_id)

        ark_start = self._search_regex(
            r'data-ark-start="(\d{8}T\d{6}Z)"', webpage, 'archive start', default=None)
        if not ark_start:
            raise ExtractorError(
                'Spinitron Ark audio is only kept for about the last two weeks',
                expected=True)

        player = self._search_json(
            r'ark2Player\([^,]+,', webpage, 'ark player config', playlist_id, default={})
        station_name = traverse_obj(player, ('stationName', {str})) or station
        hls_base = traverse_obj(player, ('hlsBaseUrl', {str})) or 'https://ark3.spinitron.com/ark2'
        m3u8_url = f'{hls_base.rstrip("/")}/{station_name}-{ark_start}/index.m3u8'

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, playlist_id, 'mp4', m3u8_id='hls')
        for f in formats:
            f.setdefault('vcodec', 'none')

        series = self._html_search_regex(
            r'<h3[^>]+class="show-title"[^>]*>\s*<a[^>]*>([^<]+)',
            webpage, 'show title', default=None)
        dj = self._html_search_regex(
            r'<p class="dj-name">\s*(?:With\s+)?<a[^>]*>([^<]+)',
            webpage, 'dj', default=None)
        genre = self._html_search_regex(
            r'<p class="show-categoty">([^<]+)', webpage, 'genre', default=None)
        uploader = self._html_search_regex(
            r'<h1[^>]+class="station-title"[^>]*>\s*<a[^>]*>([^<]+)',
            webpage, 'station', default=None)
        series_id = self._search_regex(
            rf'/{re.escape(station)}/show/(\d+)', webpage, 'show id', default=None)

        return {
            'id': playlist_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'timestamp': _parse_ark_timestamp(ark_start),
            'formats': formats,
            'subtitles': subtitles,
            'series': series,
            'series_id': series_id,
            'uploader': uploader,
            'uploader_id': station_name,
            'channel': uploader,
            'channel_id': station_name,
            'channel_url': f'https://spinitron.com/{station_name}/',
            'creators': [dj] if dj else None,
            'genres': [genre] if genre else None,
        }


class SpinitronShowIE(InfoExtractor):
    IE_NAME = 'spinitron:show'
    IE_DESC = 'Spinitron shows'
    _VALID_URL = r'https?://(?:www\.)?spinitron\.com/(?P<station>[^/?#]+)/show/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://spinitron.com/KPOV/show/11860/Calling-All-Cowboys',
        'info_dict': {
            'id': '11860',
            'title': 'Calling All Cowboys with Chuckaroo The Buckaroo on 88.9FM KPOV Bend',
            'description': 'md5:e41316b6bf2a1e2c7f81fc94c137429e',
        },
        'playlist_mincount': 1,
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.spinitron.com/KPOV/show/11860/Calling-All-Cowboys',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        entries = []
        for item in re.split(r'(?=<div class="list-item")', webpage):
            if not re.search(r'data-ark-start="\d{8}T\d{6}Z"', item):
                continue
            mobj = re.search(r'href="(/[^"]+/pl/(\d+)[^"]*)"', item)
            if not mobj:
                continue
            entries.append(self.url_result(
                urljoin('https://spinitron.com', mobj.group(1)),
                ie=SpinitronIE, video_id=mobj.group(2)))

        if not entries:
            raise ExtractorError(
                'No Spinitron Ark audio is currently available for this show '
                '(archives are only kept for about the last two weeks)',
                expected=True)

        return self.playlist_result(
            entries, show_id,
            self._og_search_title(webpage),
            self._og_search_description(webpage))
