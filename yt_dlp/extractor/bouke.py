from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    extract_attributes,
    float_or_none,
    mimetype2ext,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import find_element, traverse_obj


class BoukeIE(InfoExtractor):
    IE_NAME = 'bouke'
    IE_DESC = 'Boukè'

    _VALID_URL = [
        r'https?://(?:www\.)?bouke\.media/(?:replay/)?(?:culture|emission|info|sport)(?P<alt_id>(?:/[\w-]+)+)/(?P<id>\d+)',
        r'https?://(?:www\.)?bouke\.media/(?P<id>direct)/?(?:[?#]|$)',
    ]
    _EMBED_JSON = 'https://tvlocales-player-v12.freecaster.com/embed/{}.json'
    _MP4_QUALITIES = {
        '3': (640, 360),
        '5': (960, 540),
        '9': (1280, 720),
        '11': (1920, 1080),
    }
    _TESTS = [{
        'url': 'https://www.bouke.media/emission/xmas-melodies/19946',
        'md5': 'dfa1572370dac6a0185b5ce8496d04f3',
        'info_dict': {
            'id': '19946',
            'ext': 'mp4',
            'title': 'Xmas Mélodies',
            'creators': ['Boukè - Le média made in chez nous'],
            'description': 'Emission spéciale ou captation sur un sujet ou un événement particulier.',
            'display_id': 'xmas-melodies',
            'duration': 6589.504,
            'thumbnail': r're:https?://.+',
            'timestamp': 1766610000,
            'upload_date': '20251224',
        },
        'params': {'format': 'mp4-9'},
    }, {
        'url': 'https://www.bouke.media/replay/emission/occupe-moi-si-tu-peux/occupe-moi-si-tu-peux-profondeville/23158',
        'only_matching': True,
    }, {
        'url': 'https://www.bouke.media/sport/chinelle-2026-record-de-victoires-pour-kevin-fors-dans-une-edition-marquee-par-la-secheresse/23449',
        'only_matching': True,
    }, {
        'url': 'https://www.bouke.media/info/gaston-le-chien-qui-calme-les-emotions/23541',
        'only_matching': True,
    }, {
        'url': 'https://www.bouke.media/sport/foot/arquet-namur-b-soffre-flawinne-dans-le-derby-du-grand-namur-en-2b/23534',
        'only_matching': True,
    }, {
        'url': 'https://www.bouke.media/direct',
        'only_matching': True,
    }]

    def _extract_freecaster_formats(self, video_info, video_id, live=False):
        formats, subtitles = [], {}
        for src in traverse_obj(video_info, ('src', lambda _, v: v['src'])):
            src_url = url_or_none(src['src'])
            if not src_url:
                continue
            ext = mimetype2ext(src.get('type'))
            if ext == 'mp4':
                quality = src_url.rpartition('_')[2].removesuffix('.mp4')
                width, height = self._MP4_QUALITIES.get(quality, (None, None))
                formats.append({
                    'acodec': 'mp4a.40.2',
                    'ext': ext,
                    'format_id': f'mp4-{quality}',
                    'height': height,
                    'url': src_url,
                    'vcodec': 'avc1',
                    'width': width,
                })
            elif ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src_url, video_id, 'mp4', m3u8_id='hls', fatal=False, live=live)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    src_url, video_id, mpd_id='dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                self.report_warning(f'Unsupported stream type: {ext}')
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        is_live_url = video_id == 'direct'
        webpage = self._download_webpage(url, video_id)

        if is_live_url:
            display_id = 'direct'
            embed_id = self._search_regex(
                r'"live_token"\s*:\s*"([0-9a-f-]{36})"', webpage, 'live token')
        else:
            display_id = self._match_valid_url(url).group('alt_id').split('/')[-1]
            embed_id = traverse_obj(webpage, (
                {find_element(cls='freecaster-player', html=True)},
                {extract_attributes}, 'data-video-id', {str}))
            if not embed_id:
                raise ExtractorError('Unable to extract Freecaster video id', expected=True)

        video_info = traverse_obj(self._download_json(
            self._EMBED_JSON.format(embed_id), video_id), ('video', {dict}))
        if not video_info:
            raise ExtractorError('Failed to fetch video information')

        is_live = is_live_url or traverse_obj(video_info, ('live', {bool}))
        formats, subtitles = self._extract_freecaster_formats(
            video_info, video_id, live=is_live)
        if not formats:
            if is_live:
                self.raise_geo_restricted(countries=['BE'])
            raise ExtractorError('No video formats found', expected=True)

        json_ld = next(self._yield_json_ld(webpage, video_id), {})

        return {
            'id': video_id,
            'display_id': display_id,
            'duration': traverse_obj(video_info, ('duration', {float_or_none})),
            'formats': formats,
            'is_live': True if is_live else None,
            'location': traverse_obj(webpage, (
                {find_element(cls='content-location')}, {clean_html})),
            'subtitles': subtitles,
            'thumbnail': (
                traverse_obj(video_info, ('poster', {url_or_none}))
                or self._og_search_thumbnail(webpage, default=None)),
            'title': (
                traverse_obj(json_ld, ('headline', {clean_html}))
                or traverse_obj(video_info, ('title', {str}))
                or self._html_extract_title(webpage, default=None)),
            **traverse_obj(json_ld, {
                'creator': ('author', 'name', {clean_html}),
                'description': ('description', {clean_html}),
                'timestamp': ('datePublished', {parse_iso8601}),
            }),
        }
