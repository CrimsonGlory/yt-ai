from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    get_elements_text_and_html_by_attribute,
    scale_thumbnails_to_max_format_width,
    unified_timestamp,
    url_or_none,
)


class TVOpenGrBaseIE(InfoExtractor):
    _PLAYER_APIS = (
        'https://cdn.ethnos.gr/templates/data/player',
        'https://www.tvopen.gr/templates/data/player',
    )

    def _download_player(self, video_id):
        for endpoint in self._PLAYER_APIS:
            player = self._download_json(
                endpoint, video_id, query={'cid': video_id},
                fatal=False, errnote=False, impersonate=True)
            if isinstance(player, dict) and (
                    url_or_none(player.get('stream')) or url_or_none(player.get('httpstream'))):
                return player
        raise ExtractorError('Unable to download player JSON', expected=True)

    def _download_open_webpage(self, url, video_id, note='Downloading webpage'):
        return self._download_webpage(
            url, video_id, note, fatal=False, errnote=False, impersonate=True) or ''

    def _extract_formats_and_subs(self, response, video_id):
        formats, subs = [], {}
        for format_id, format_url in response.items():
            if format_id not in ('stream', 'httpstream', 'mpegdash'):
                continue
            format_url = url_or_none(format_url)
            if not format_url:
                continue
            ext = determine_ext(format_url)
            if ext == 'm3u8':
                formats_, subs_ = self._extract_m3u8_formats_and_subtitles(
                    format_url, video_id, 'mp4', m3u8_id=format_id,
                    fatal=False)
            elif ext == 'mpd':
                formats_, subs_ = self._extract_mpd_formats_and_subtitles(
                    format_url, video_id, mpd_id=format_id, fatal=False)
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                })
                continue
            formats.extend(formats_)
            self._merge_subtitles(subs_, target=subs)
        return formats, subs

    def _webpage_video_info(self, webpage, video_id):
        return self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={}) or {}

    def _extract_open_video(self, video_id, display_id, webpage):
        webpage = webpage or ''
        info = self._webpage_video_info(webpage, video_id)
        if not info.get('title'):
            canonical_url = self._og_search_url(webpage, default=None)
            if canonical_url:
                canon_page = self._download_open_webpage(
                    canonical_url, video_id, 'Downloading canonical watch page')
                if canon_page:
                    webpage = canon_page
                    info = self._webpage_video_info(webpage, video_id)
                    if not display_id:
                        display_id = self._search_regex(
                            r'/watch/\d+/([^/?#]+)', canonical_url,
                            'display id', default=video_id)
        if not webpage:
            webpage = self._download_open_webpage(
                f'https://cdn.ethnos.gr/embed/{video_id}', video_id, 'Downloading embed page')
            if webpage and not info.get('title'):
                info = self._webpage_video_info(webpage, video_id) or info

        player = self._download_player(video_id)
        info['formats'], info['subtitles'] = self._extract_formats_and_subs(player, video_id)

        thumb = player.get('thumb')
        if thumb:
            info['thumbnails'] = [{
                'url': f'https://opentv-static.siliconweb.com/imgHandler/1280/{thumb}',
            }]
            info.pop('thumbnail', None)
        if info.get('formats') and info.get('thumbnails'):
            info['thumbnails'] = scale_thumbnails_to_max_format_width(
                info['formats'], info['thumbnails'], r'(?<=/imgHandler/)\d+')

        description, desc_html = next(
            get_elements_text_and_html_by_attribute('class', 'description', webpage),
            (None, None))
        if description and desc_html and desc_html.startswith('<span '):
            info['description'] = description

        info['id'] = video_id
        info['display_id'] = display_id or video_id
        info['title'] = (
            info.get('title')
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage, default=None)
            or display_id or video_id)
        info.setdefault(
            'description',
            self._og_search_description(webpage, default=None)
            or self._html_search_meta('description', webpage, default=None))
        if not info.get('timestamp'):
            info['timestamp'] = unified_timestamp(
                self._html_search_meta('publish-date', webpage, default=None))
        if not info.get('thumbnails') and not info.get('thumbnail'):
            info['thumbnail'] = self._og_search_thumbnail(webpage, default=None)
        return info


class TVOpenGrWatchIE(TVOpenGrBaseIE):
    IE_NAME = 'tvopengr:watch'
    IE_DESC = 'tvopen.gr (and ethnos.gr) videos'
    _VALID_URL = r'https?://(?P<netloc>(?:www\.)?(?:tvopen|ethnos)\.gr)/watch/(?P<id>\d+)/(?P<slug>[^/]+)'

    _TESTS = [{
        'url': 'https://www.tvopen.gr/watch/100979/se28099agapaomenalla7cepeisodio267cmhthrargiapashskakias',
        'md5': '2a03f96dc482828f9bd4eb0c986baeb8',
        'params': {'format': 'httpstream'},
        'info_dict': {
            'id': '100979',
            'title': 'md5:e021f3001e16088ee40fa79b20df305b',
            'display_id': 'se28099agapaomenalla7cepeisodio267cmhthrargiapashskakias',
            'description': 'md5:ba17db53954134eb8d625d199e2919fb',
            'thumbnail': r're:https?://opentv-static\.siliconweb\.com/imgHandler/.+\.jpg',
            'ext': 'mp4',
            'duration': 2420.0,
            'upload_date': '20220108',
            'timestamp': 1641600000,
        },
    }, {
        'url': 'https://www.ethnos.gr/watch/101009/nikoskaprabelosdenexoymekanenanasthenhsemethmethmetallaxhomikron',
        'info_dict': {
            'id': '101009',
            'title': 'md5:51f68773dcb6c70498cd326f45fefdf0',
            'display_id': 'nikoskaprabelosdenexoymekanenanasthenhsemethmethmetallaxhomikron',
            'description': 'md5:78fff49f18fb3effe41b070e5c7685d6',
            'thumbnail': r're:https?://opentv-static\.siliconweb\.com/imgHandler/.+\.jpg',
            'ext': 'mp4',
            'duration': 246.0,
            'upload_date': '20220109',
            'timestamp': 1641686400,
        },
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'slug')
        webpage = self._download_open_webpage(url, video_id)
        return self._extract_open_video(video_id, display_id, webpage)


class TVOpenGrEmbedIE(TVOpenGrBaseIE):
    IE_NAME = 'tvopengr:embed'
    IE_DESC = 'tvopen.gr embedded videos'
    _VALID_URL = r'(?:https?:)?//(?:www\.|cdn\.|)(?:tvopen|ethnos).gr/embed/(?P<id>\d+)'
    _EMBED_REGEX = [rf'''<iframe[^>]+?src=(?P<_q1>["'])(?P<url>{_VALID_URL})(?P=_q1)''']

    _TESTS = [{
        'url': 'https://cdn.ethnos.gr/embed/100963',
        'info_dict': {
            'id': '100963',
            'display_id': 'koronoiosapotoysdieythyntestonsxoleionselftestgiaosoysdenbrhkan',
            'title': 'md5:2c71876fadf0cda6043da0da5fca2936',
            'description': 'md5:17482b4432e5ed30eccd93b05d6ea509',
            'thumbnail': r're:https?://opentv-static\.siliconweb\.com/imgHandler/.+\.jpg',
            'ext': 'mp4',
            'duration': 118.0,
            'upload_date': '20220108',
            'timestamp': 1641600000,
        },
    }]
    _WEBPAGE_TESTS = [{
        'url': 'https://www.ethnos.gr/World/article/190604/hparosiaxekinoynoisynomiliessthgeneyhmethskiatoypolemoypanoapothnoykrania',
        'info_dict': {
            'id': '101119',
            'ext': 'mp4',
            'title': 'Οι καρποί των διαπραγματεύσεων ΗΠΑ-Ρωσίας | Ώρα Ελλάδος 7:00 > Ρεπορτάζ',
            'description': 'Ξεκινούν οι διαπραγματεύσεις ανάμεσα σε Ηνωμένες Πολιτείες και Ρωσία για την Ουκρανία.',
            'display_id': 'oikarpoitondiapragmateyseonhparosias',
            'duration': 421.0,
            'thumbnail': r're:https?://opentv-static\.siliconweb\.com/imgHandler/.+\.jpg',
            'timestamp': 1641772800,
            'upload_date': '20220110',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_open_webpage(url, video_id)
        display_id = self._search_regex(
            r'/watch/\d+/([^/?#]+)',
            self._og_search_url(webpage, default=''),
            'display id', default=video_id)
        return self._extract_open_video(video_id, display_id, webpage)
