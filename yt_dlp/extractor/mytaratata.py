import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    extract_attributes,
    int_or_none,
    merge_dicts,
    parse_resolution,
    url_or_none,
    urljoin,
)


class MyTaratataIE(InfoExtractor):
    IE_NAME = 'mytaratata'
    IE_DESC = 'mytaratata.com'
    _VALID_URL = r'https?://(?:www\.)?mytaratata\.com/taratata/(?P<episode>\d+)/(?P<id>[^/?#]+)(?:/embed)?'
    _TESTS = [{
        'url': 'https://mytaratata.com/taratata/253/kevin-michael-yael-naim-lean-on-me-2008',
        'md5': '195c40c74a8c7e358988b7fa052c54ca',
        'info_dict': {
            'id': '239',
            'ext': 'mp4',
            'display_id': 'kevin-michael-yael-naim-lean-on-me-2008',
            'title': 'Kevin Michael / Yael Naim "Lean On Me" (2008)',
            'description': 'Kevin Michael / Yael Naim "Lean On Me" (2008)',
            'thumbnail': r're:https?://mytaratata\.com/.+\.(?:jpe?g|png)',
            'timestamp': 1202428800,
            'upload_date': '20080208',
            'series': 'Taratata',
            'episode': 'Episode 253',
            'episode_number': 253,
        },
    }, {
        'url': 'https://mytaratata.com/taratata/584/jean-louis-aubert-merveille-2024',
        'only_matching': True,
    }, {
        'url': 'https://mytaratata.com/taratata/253/kevin-michael-yael-naim-lean-on-me-2008/embed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, episode = self._match_valid_url(url).group('id', 'episode')
        webpage = self._download_webpage(url, display_id)

        player = {}
        for el in re.findall(r'<div[^>]+class="[^"]*\bjwplayer\b[^"]*"[^>]*>', webpage):
            attrs = extract_attributes(el)
            if url_or_none(attrs.get('data-source')) or url_or_none(attrs.get('data-url')):
                player = attrs
                break
        if not player:
            raise ExtractorError('Unable to extract JWPlayer source', expected=True)

        media_url = url_or_none(player.get('data-source'))
        hls_url = url_or_none(player.get('data-url'))
        video_id = self._search_regex(
            r'/videos/(\d+)', hls_url or media_url or '', 'video id',
            default=display_id)

        formats, subtitles = [], {}
        if media_url:
            formats.append({
                'url': media_url,
                'format_id': 'http',
                'ext': determine_ext(media_url, 'mp4'),
                'quality': 1,
                **parse_resolution(media_url),
            })
        if hls_url:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)
        json_ld.pop('title', None)

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'title': self._html_search_regex(
                r'<h1[^>]*>([^<]+)', webpage, 'title', default=None),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': url_or_none(player.get('data-image')),
            'formats': formats,
            'subtitles': subtitles,
            'series': 'Taratata',
            'episode_number': int_or_none(episode),
        }, json_ld)


class MyTaratataEpisodeIE(InfoExtractor):
    IE_NAME = 'mytaratata:episode'
    IE_DESC = 'mytaratata.com episodes'
    _VALID_URL = r'https?://(?:www\.)?mytaratata\.com/taratata/(?P<id>\d+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://mytaratata.com/taratata/253',
        'info_dict': {
            'id': '253',
            'title': 'TARATATA N°253',
        },
        'playlist_mincount': 10,
        'params': {'skip_download': True},
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        title = (
            self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._html_extract_title(webpage, default=None))
        return self.playlist_from_matches(
            re.findall(
                rf'(?:https?:)?(?://(?:www\.)?mytaratata\.com)?(/taratata/{re.escape(playlist_id)}/[^/?#"]+)',
                webpage),
            playlist_id, title, getter=lambda path: urljoin(url, path),
            ie=MyTaratataIE)
