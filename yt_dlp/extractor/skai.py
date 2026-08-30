from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class SkaiIE(InfoExtractor):
    IE_NAME = 'skai'
    IE_DESC = 'SKAI'
    _VALID_URL = (
        r'https?://(?:www\.)?skai\.gr/tv/episode/'
        r'[^/?#]+/[^/?#]+/(?P<airdate>\d{4}-\d{2}-\d{2}-\d{2})'
        r'(?:/(?P<id>[^/?#]+))?/?'
    )
    _HLS_BASE = 'https://videostream.skai.gr/skaivod/_definst_/mp4:skai'
    _DOWNLOAD_BASE = 'https://download.skai.gr'
    _TESTS = [
        {
            'url': 'https://www.skai.gr/tv/episode/enimerosi/opou-yparchei-ellada/2025-06-11-14/opou-yparchei-ellada-ikaria-11062025',
            'md5': '169f825c9275791786a41c86c2a90970',
            'info_dict': {
                'id': '464070',
                'ext': 'mp4',
                'title': 'Όπου Υπάρχει Ελλάδα | Ικαρία | 11/06/2025',
                'description': 'md5:0da4b83e7e84984a44d8234e20db51a1',
                'thumbnail': r're:https://media\.skaitv\.gr/images/.+',
                'timestamp': 1749653100,
                'upload_date': '20250611',
                'series': 'Όπου Υπάρχει Ελλάδα',
                'episode': 'Ικαρία',
                'episode_number': 107,
            },
        },
        {
            'url': 'https://www.skai.gr/tv/episode/enimerosi/opou-yparchei-ellada/2025-06-11-14',
            'only_matching': True,
        },
        {
            'url': 'https://www.skai.gr/tv/episode/enimerosi/opou-yparchei-ellada/2025-06-11-14/to-isonopou-yparchei-elladasin-einai-stin-ikaria-poio-einai-to-mustiko-tis-makrozoias-ton-katoikon',
            'only_matching': True,
        },
        {
            'url': 'https://www.skai.gr/tv/episode/ntokimanter/skoteini-dekaetia-1964-1974/2024-10-28-21/skoteini-dekaetia-1964-1974-21i-apriliou-28102024',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        url_m = self._match_valid_url(url)
        display_id = url_m.group('id') or url_m.group('airdate')
        webpage = self._download_webpage(url, display_id)
        data = self._search_json(
            r'var type\s*=\s*[\'"]player-main[\'"]\s*;\s*var data\s*=', webpage, 'player data', display_id,
        )
        episode = traverse_obj(data, 'episodemain', {dict})
        if not episode:
            raise ExtractorError('No episode data found', expected=True)

        video_id = str_or_none(episode.get('media_item_id') or episode.get('id')) or display_id
        if str_or_none(episode.get('drmflag')) == '1' or episode.get('drm'):
            self.report_drm(video_id)

        media_file = traverse_obj(episode, 'media_item_file', {str})
        if not media_file:
            raise ExtractorError('No media file available', expected=True)

        if str_or_none(episode.get('media_type_id')) == '4':
            if not YoutubeIE.suitable(media_file):
                media_file = f'https://www.youtube.com/watch?v={media_file}'
            return self.url_result(media_file, YoutubeIE, video_id)

        formats, subtitles = [], {}
        if media_file.startswith('http'):
            video_url = media_file
        else:
            path = media_file if media_file.startswith('/') else f'/{media_file}'
            if determine_ext(media_file) == 'mp4':
                video_url = f'{self._HLS_BASE}{path}/playlist.m3u8'
            else:
                video_url = f'{self._DOWNLOAD_BASE}{path}'

        ext = determine_ext(video_url, 'mp4')
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(video_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats = [{'url': video_url, 'ext': ext}]

        sub_url = url_or_none(episode.get('subs'))
        if sub_url:
            self._merge_subtitles({'el': [{'url': sub_url}]}, target=subtitles)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (
                traverse_obj(episode, (('media_item_title', 'title'), {str}, any))
                or self._og_search_title(webpage, default=None)
                or self._html_extract_title(webpage)),
            **traverse_obj(
                episode,
                {
                    'description': (('short_descr', 'descr', 'meta_description'), {clean_html}, filter, any),
                    'thumbnail': (('img', 'meta_image', 'thumb', 'mi_img'), {url_or_none}, any),
                    'timestamp': ('start', {unified_timestamp}),
                    'series': ('title1', {str}),
                    'episode': ('title2', {str}),
                    'episode_number': ('episode_number', {int_or_none}),
                },
            ),
        }
