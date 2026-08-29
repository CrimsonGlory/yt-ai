import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    extract_attributes,
    get_element_by_class,
    get_element_html_by_class,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TV5MondePlusIE(InfoExtractor):
    IE_NAME = 'TV5MONDE'
    _VALID_URL = r'https?://(?:www\.|information\.)?tv5monde\.com/(?:tv/video|(?:[^/?#]+)/video|les-jt)/(?P<id>[^/?#]+)'
    _TESTS = [{
        # information.tv5monde.com news clip (direct mp4)
        'url': 'https://information.tv5monde.com/international/video/canada-donald-trump-le-rebaptiseur-de-lac-2835290',
        'md5': 'ca8a199a4dcf84159d7043fc6e3743ab',
        'info_dict': {
            'id': '6661938',
            'display_id': 'canada-donald-trump-le-rebaptiseur-de-lac-2835290',
            'ext': 'mp4',
            'title': 'Canada: Donald Trump, le rebaptiseur de lac',
            'description': 'md5:820f7faab5da46480a0c2f72f602921c',
            'thumbnail': r're:https?://information\.tv5monde\.com/.+',
            'duration': 175,
            'upload_date': '20260828',
            'timestamp': 1787875200,
            'series': 'article',
            'episode': 'canada_donald_trump_le_rebaptiseur_de_lac|jtchapter_canada_donald_trump_le_rebaptiseur_',
        },
    }, {
        # documentary
        'url': 'https://www.tv5monde.com/tv/video/65931-baudouin-l-heritage-d-un-roi-baudouin-l-heritage-d-un-roi',
        'md5': 'd2a708902d3df230a357c99701aece05',
        'info_dict': {
            'id': '3FPa7JMu21_6D4BA7b',
            'display_id': '65931-baudouin-l-heritage-d-un-roi-baudouin-l-heritage-d-un-roi',
            'ext': 'mp4',
            'title': "Baudouin, l'héritage d'un roi",
            'thumbnail': 'https://psi.tv5monde.com/upsilon-images/960x540/6f/baudouin-f49c6b0e.jpg',
            'duration': 4842,
            'upload_date': '20240130',
            'timestamp': 1706641242,
            'episode': "BAUDOUIN, L'HERITAGE D'UN ROI",
            'description': 'md5:78125c74a5cac06d7743a2d09126edad',
            'series': "Baudouin, l'héritage d'un roi",
        },
        'skip': 'Old /tv/video pages redirect to DRM-protected TV5MONDE+',
    }, {
        # series episode
        'url': 'https://www.tv5monde.com/tv/video/52952-toute-la-vie-mardi-23-mars-2021',
        'md5': 'f5e09637cadd55639c05874e22eb56bf',
        'info_dict': {
            'id': 'obRRZ8m6g9_6D4BA7b',
            'display_id': '52952-toute-la-vie-mardi-23-mars-2021',
            'ext': 'mp4',
            'title': 'Toute la vie',
            'description': 'md5:a824a2e1dfd94cf45fa379a1fb43ce65',
            'thumbnail': 'https://psi.tv5monde.com/media/image/960px/5880553.jpg',
            'duration': 2526,
            'upload_date': '20230721',
            'timestamp': 1689971646,
            'series': 'Toute la vie',
            'episode': 'Mardi 23 mars 2021',
        },
        'skip': 'Old /tv/video pages redirect to DRM-protected TV5MONDE+',
    }, {
        # movie
        'url': 'https://www.tv5monde.com/tv/video/8771-ce-fleuve-qui-nous-charrie-ce-fleuve-qui-nous-charrie-p001-ce-fleuve-qui-nous-charrie',
        'md5': '87cefc34e10a6bf4f7823cccd7b36eb2',
        'info_dict': {
            'id': 'DOcfvdLKXL_6D4BA7b',
            'display_id': '8771-ce-fleuve-qui-nous-charrie-ce-fleuve-qui-nous-charrie-p001-ce-fleuve-qui-nous-charrie',
            'ext': 'mp4',
            'title': 'Ce fleuve qui nous charrie',
            'description': 'md5:62ba3f875343c7fc4082bdfbbc1be992',
            'thumbnail': 'https://psi.tv5monde.com/media/image/960px/5476617.jpg',
            'duration': 5300,
            'upload_date': '20210822',
            'timestamp': 1629594105,
            'episode': 'CE FLEUVE QUI NOUS CHARRIE-P001-CE FLEUVE QUI NOUS CHARRIE',
            'series': 'Ce fleuve qui nous charrie',
        },
        'skip': 'Old /tv/video pages redirect to DRM-protected TV5MONDE+',
    }, {
        # news
        'url': 'https://www.tv5monde.com/tv/video/70402-tv5monde-le-journal-edition-du-08-05-24-11h',
        'md5': 'c62977d6d10754a2ecebba70ad370479',
        'info_dict': {
            'id': 'LgQFrOCNsc_6D4BA7b',
            'display_id': '70402-tv5monde-le-journal-edition-du-08-05-24-11h',
            'ext': 'mp4',
            'title': 'TV5MONDE, le journal',
            'description': 'md5:777dc209eaa4423b678477c36b0b04a8',
            'thumbnail': 'https://psi.tv5monde.com/media/image/960px/6184105.jpg',
            'duration': 854,
            'upload_date': '20240508',
            'timestamp': 1715159640,
            'series': 'TV5MONDE, le journal',
            'episode': 'EDITION DU 08/05/24 - 11H',
        },
        'skip': 'Old /tv/video pages redirect to DRM-protected TV5MONDE+',
    }, {
        'url': 'https://information.tv5monde.com/les-jt/64-minutes',
        'only_matching': True,
    }]
    _GEO_BYPASS = False

    @staticmethod
    def _extract_subtitles(data_captions):
        subtitles = {}
        for f in traverse_obj(data_captions, ('files', lambda _, v: url_or_none(v['file']))):
            subtitles.setdefault(f.get('label') or 'fra', []).append({'url': f['file']})
        return subtitles

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, display_id, impersonate=True)
        if 'tv5mondeplus.com' in urllib.parse.urlparse(urlh.url).netloc:
            raise ExtractorError(
                'This video has moved to TV5MONDE+, which uses DRM', expected=True)

        if ">Ce programme n'est malheureusement pas disponible pour votre zone géographique.<" in webpage:
            self.raise_geo_restricted(countries=['FR'])

        vpl_data = extract_attributes(self._search_regex(
            r'(<[^>]+class="video_player_loader"[^>]+>)',
            webpage, 'video player loader'))

        video_files = self._parse_json(
            vpl_data['data-broadcast'], display_id)
        formats = []
        video_id = None

        def process_video_files(v):
            nonlocal video_id
            for video_file in v:
                v_url = video_file.get('url')
                if not v_url:
                    continue
                if video_file.get('type') == 'application/deferred':
                    d_param = urllib.parse.quote(v_url)
                    token = video_file.get('token')
                    if not token:
                        continue
                    deferred_json = self._download_json(
                        f'https://api.tv5monde.com/player/asset/{d_param}/resolve?condenseKS=true',
                        display_id, 'Downloading deferred info', fatal=False, impersonate=True,
                        headers={'Authorization': f'Bearer {token}'})
                    v_url = traverse_obj(deferred_json, (0, 'url', {url_or_none}))
                    if not v_url:
                        continue
                    process_video_files(deferred_json)

                # data-guid from the webpage isn't stable; prefer ids from media URLs
                video_id = video_id or self._search_regex(
                    (r'materials/([\da-zA-Z]{10}_[\da-fA-F]{7})/',
                     r'/videos/[\da-f]+/(\d+)\.mp4'),
                    v_url, 'video id', default=None)

                video_format = video_file.get('format') or determine_ext(v_url)
                if video_format == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        v_url, display_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls', fatal=False))
                elif video_format == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        v_url, display_id, fatal=False))
                else:
                    formats.append({
                        'url': v_url,
                        'format_id': video_format,
                    })

        process_video_files(video_files)

        metadata = self._parse_json(
            vpl_data.get('data-metadata') or '{}', display_id, fatal=False)

        if not video_id:
            video_id = self._search_regex(
                (r'data-guid=["\']([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})',
                 r'id_contenu["\']\s:\s*(\d+)'), webpage, 'video id',
                default=display_id)

        return {
            **traverse_obj(metadata, ('content', {
                'id': ('id', {str}),
                'title': ('title', {str}),
                'episode': ('title', {str}),
                'series': ('series', {str}),
                'timestamp': ('publishDate_ts', {int_or_none}),
                'duration': ('duration', {int_or_none}),
            })),
            'id': video_id,
            'display_id': display_id,
            'title': (clean_html(get_element_by_class('main-title', webpage))
                      or self._og_search_title(webpage)),
            'description': (
                clean_html(get_element_by_class(
                    'text', get_element_html_by_class('ep-summary', webpage) or ''))
                or self._og_search_description(webpage)),
            'thumbnail': url_or_none(vpl_data.get('data-image')),
            'formats': formats,
            'subtitles': self._extract_subtitles(self._parse_json(
                traverse_obj(vpl_data, ('data-captions', {str}), default='{}'), display_id, fatal=False)),
        }
