import re

from .common import InfoExtractor
from ..utils import ExtractorError


class EpiconIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?epicon\.in/(?:documentaries|movies|tv-shows/[^/?#]+/[^/?#]+)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.epicon.in/documentaries/air-battle-of-srinagar',
        'info_dict': {
            'id': 'air-battle-of-srinagar',
            'ext': 'mp4',
            'title': 'Air Battle of Srinagar',
            'description': 'md5:c4de2013af9bc05ae4392e4115d518d7',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.epicon.in/movies/krit',
        'info_dict': {
            'id': 'krit',
            'ext': 'mp4',
            'title': 'Krit',
            'description': 'md5:c12b35dad915d48ccff7f013c79bab4a',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.epicon.in/tv-shows/paapnaashini-ganga/season-1/vardaan',
        'skip': 'video gone',
        'info_dict': {
            'id': 'vardaan',
            'ext': 'mp4',
            'title': 'Paapnaashini Ganga - Season 1 - Ep 1 - VARDAAN',
            'description': 'md5:f517058c3d0402398eefa6242f4dd6ae',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.epicon.in/movies/jayadev',
        'skip': 'video gone',
        'info_dict': {
            'id': 'jayadev',
            'ext': 'mp4',
            'title': 'Jayadev',
            'description': 'md5:09e349eecd8e585a3b6466904f19df6c',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        cid = self._search_regex(
            r'class=\"mylist-icon\ iconclick\"\ id=\"(\d+)', webpage, 'cid', default=None)
        if not cid:
            cid = self._search_regex(
                r'<input[^>]+id="cont_id"[^>]+value="(\d+)"', webpage, 'cid', default=None)
        if not cid:
            cid = self._search_regex(
                r"playTrailer\('(\d+)'", webpage, 'cid', default=None)
        data_json = {}
        if cid:
            headers = {'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            data = f'cid={cid}&action=st&type=video'.encode()
            try:
                data_json = self._download_json(
                    'https://www.epicon.in/ajaxplayer/', video_id, headers=headers, data=data)
                if isinstance(data_json, str):
                    data_json = self._parse_json(data_json, video_id)
            except ExtractorError:
                data_json = {}

        if not data_json.get('success'):
            m3u8_url = self._search_regex(
                r"playTrailer\('[^']+','[^']+','(https?://[^']+\.m3u8[^']*)'",
                webpage, 'm3u8 url', default=None)
            if m3u8_url:
                m3u8_url = m3u8_url.replace('&amp;', '&')
                title = (self._search_regex(
                    r"playTrailer\('[^']+','([^']+)'", webpage, 'title', default=None)
                    or self._og_search_title(webpage)
                    or self._html_extract_title(webpage))
                return {
                    'id': video_id,
                    'title': title,
                    'description': self._og_search_description(webpage),
                    'thumbnail': self._og_search_thumbnail(webpage),
                    'formats': self._extract_m3u8_formats(m3u8_url, video_id, 'mp4'),
                }
            raise ExtractorError(data_json.get('message') or 'No playable video', expected=True)

        title = (self._search_regex(r'setplaytitle=\"([^\"]+)', webpage, 'title', default=None)
                 or self._html_extract_title(webpage))
        description = self._og_search_description(webpage) or None
        thumbnail = self._og_search_thumbnail(webpage) or None
        formats = self._extract_m3u8_formats(data_json['url']['video_url'], video_id)

        subtitles = {}
        for subtitle in data_json.get('subtitles', []):
            sub_url = subtitle.get('file')
            if not sub_url:
                continue
            subtitles.setdefault(subtitle.get('lang', 'English'), []).append({
                'url': self._proto_relative_url(sub_url),
            })

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'subtitles': subtitles,
        }


class EpiconSeriesIE(InfoExtractor):
    _VALID_URL = r'(?!.*season)https?://(?:www\.)?epicon\.in/tv-shows/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.epicon.in/tv-shows/1-of-something',
        'skip': 'video gone',
        'playlist_mincount': 5,
        'info_dict': {
            'id': '1-of-something',
        },
    }, {
        'url': 'https://www.epicon.in/tv-shows/eco-india-english',
        'skip': 'video gone',
        'playlist_mincount': 76,
        'info_dict': {
            'id': 'eco-india-english',
        },
    }, {
        'url': 'https://www.epicon.in/tv-shows/s/',
        'skip': 'video gone',
        'playlist_mincount': 25,
        'info_dict': {
            'id': 's',
        },
    }, {
        'url': 'https://www.epicon.in/tv-shows/ekaant',
        'skip': 'video gone',
        'playlist_mincount': 38,
        'info_dict': {
            'id': 'ekaant',
        },
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        episodes = re.findall(rf'ct-tray-url=\"(tv-shows/{playlist_id}/[^\"]+)', webpage)
        entries = [self.url_result(f'https://www.epicon.in/{episode}', EpiconIE) for episode in episodes]
        return self.playlist_result(entries, playlist_id=playlist_id)
