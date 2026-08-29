from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    mimetype2ext,
    parse_age_limit,
    parse_duration,
    parse_iso8601,
    parse_resolution,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class KaruselTVIE(InfoExtractor):
    IE_NAME = 'karusel-tv'
    IE_DESC = 'Карусель'
    _VALID_URL = r'https?://(?:www\.)?karusel-tv\.ru/(?:video/(?P<id>\d+)(?:-[^/?#]+|/frame)?/?|announce/(?P<announce_id>\d+)(?:-[^/?#]+)?/?)(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.karusel-tv.ru/video/23111-navigator_novosti_vypusk_1406',
        'md5': '293ddc03835e4e0232ca6ee184ebfa4a',
        'info_dict': {
            'id': '23111',
            'ext': 'mp4',
            'title': 'Навигатор. Новости. Выпуск 1406',
            'description': 'md5:f8dc0438e8adcdfb204b47426c8608fe',
            'thumbnail': r're:https?://.+\.(?:png|jpe?g)',
            'duration': 484,
            'timestamp': 1782135000,
            'upload_date': '20260622',
            'view_count': int,
            'age_limit': 0,
        },
    }, {
        'url': 'https://www.karusel-tv.ru/video/23161-soyuz_zverej_spasenie_dvunogih',
        'only_matching': True,
    }, {
        'url': 'https://www.karusel-tv.ru/video/23111/frame',
        'only_matching': True,
    }, {
        'url': 'https://www.karusel-tv.ru/announce/11647-v_mire_dikoy_prirody',
        'only_matching': True,
    }, {
        'url': 'https://www.karusel-tv.ru/announce/15822-carevna_i_drakon_magicheskaya_kniga',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        url_m = self._match_valid_url(url)
        video_id, announce_id = url_m.group('id', 'announce_id')
        webpage = None
        if not video_id:
            webpage = self._download_webpage(url, announce_id)
            video_id = self._search_regex(
                r'data-videoID=["\'](\d+)', webpage, 'video id')

        data = self._download_json(
            f'https://www.karusel-tv.ru/video/api/get/{video_id}', video_id)

        formats, subtitles = [], {}
        for source in traverse_obj(data, ('sources', lambda _, v: url_or_none(v['src']))):
            src = source['src']
            label = traverse_obj(source, ('label', {str}))
            ext = mimetype2ext(source.get('type'), default=determine_ext(src))
            if ext == 'm3u8' or label == 'hls':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                continue
            formats.append({
                'url': src,
                'ext': ext,
                'format_id': label,
                **parse_resolution(label),
            })

        if not formats:
            raise ExtractorError('No video sources returned', expected=True)

        if webpage is None:
            webpage = self._download_webpage(url, video_id, fatal=False)

        return {
            'id': str(traverse_obj(data, 'id') or video_id),
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(data, {
                'title': ('title', {str}),
                'thumbnail': ('poster', {url_or_none}),
                'age_limit': ('agerating', {parse_age_limit}),
            }),
            'description': unescapeHTML(
                self._html_search_meta('description', webpage, default=None) if webpage else None),
            'duration': parse_duration(
                self._html_search_meta('duration', webpage, default=None) if webpage else None),
            'timestamp': parse_iso8601(
                self._html_search_meta('uploadDate', webpage, default=None) if webpage else None),
            'view_count': int_or_none(self._search_regex(
                r'UserViews:(\d+)', webpage or '', 'view count', default=None)),
        }
