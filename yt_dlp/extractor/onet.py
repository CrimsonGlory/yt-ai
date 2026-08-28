import re

from .common import InfoExtractor
from ..utils import (
    NO_DEFAULT,
    ExtractorError,
    determine_ext,
    float_or_none,
    get_element_by_class,
    int_or_none,
    js_to_json,
    parse_iso8601,
    remove_start,
    strip_or_none,
    url_basename,
    url_or_none,
)


class OnetBaseIE(InfoExtractor):
    _URL_BASE_RE = r'https?://(?:(?:www\.)?onet\.tv|onet100\.vod\.pl)/[a-z]/'

    def _search_mvp_id(self, webpage):
        return self._search_regex(
            r'id=(["\'])mvp:(?P<id>.+?)\1', webpage, 'mvp id', group='id')

    def _extract_from_id(self, video_id, webpage=None):
        response = self._download_json(
            'http://qi.ckm.onetapi.pl/', video_id,
            query={
                'body[id]': video_id,
                'body[jsonrpc]': '2.0',
                'body[method]': 'get_asset_detail',
                'body[params][ID_Publikacji]': video_id,
                'body[params][Service]': 'www.onet.pl',
                'content-type': 'application/jsonp',
                'x-onet-app': 'player.front.onetapi.pl',
            })

        error = response.get('error')
        if error:
            raise ExtractorError(
                '{} said: {}'.format(self.IE_NAME, error['message']), expected=True)

        video = response['result'].get('0')

        formats = []
        for format_type, formats_dict in video['formats'].items():
            if not isinstance(formats_dict, dict):
                continue
            for format_id, format_list in formats_dict.items():
                if not isinstance(format_list, list):
                    continue
                for f in format_list:
                    video_url = f.get('url')
                    if not video_url:
                        continue
                    ext = determine_ext(video_url)
                    if format_id.startswith('ism'):
                        formats.extend(self._extract_ism_formats(
                            video_url, video_id, 'mss', fatal=False))
                    elif ext == 'mpd':
                        formats.extend(self._extract_mpd_formats(
                            video_url, video_id, mpd_id='dash', fatal=False))
                    elif format_id.startswith('hls'):
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    else:
                        http_f = {
                            'url': video_url,
                            'format_id': format_id,
                            'abr': float_or_none(f.get('audio_bitrate')),
                        }
                        if format_type == 'audio':
                            http_f['vcodec'] = 'none'
                        else:
                            http_f.update({
                                'height': int_or_none(f.get('vertical_resolution')),
                                'width': int_or_none(f.get('horizontal_resolution')),
                                'vbr': float_or_none(f.get('video_bitrate')),
                            })
                        formats.append(http_f)

        meta = video.get('meta', {})

        title = (self._og_search_title(
            webpage, default=None) if webpage else None) or meta['title']
        description = (self._og_search_description(
            webpage, default=None) if webpage else None) or meta.get('description')
        duration = meta.get('length') or meta.get('lenght')
        timestamp = parse_iso8601(meta.get('addDate'), ' ')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }


class OnetMVPIE(OnetBaseIE):
    _VALID_URL = r'onetmvp:(?P<id>\d+\.\d+)'

    _TEST = {
        'url': 'onetmvp:381027.1509591944',
        'only_matching': True,
    }

    def _real_extract(self, url):
        return self._extract_from_id(self._match_id(url))


class OnetIE(OnetBaseIE):
    # onet.tv now redirects to video.onet.pl; clip paths dropped the old /x/ prefix
    _VALID_URL = r'https?://(?:(?:www\.)?onet\.tv|onet100\.vod\.pl)/(?:[a-z]/)?(?P<channel>[0-9a-z-]+)/(?P<display_id>[0-9a-z-]+)/(?P<id>[0-9a-z]+)'
    IE_NAME = 'onet.tv'

    _TESTS = [{
        'url': 'https://onet.tv/zielony-onet/climate-facts-matter-unia-europejska-walczy-z-dezinformacja-klimatyczna/7nzsf9l',
        'md5': 'ca5a76525edeb2c436597dde04c0b904',
        'info_dict': {
            'id': '2449258.2021405591',
            'ext': 'mp4',
            'title': 'Climate Facts Matter. Unia Europejska walczy z dezinformacją klimatyczną.',
            'description': 'md5:107db8722dae06931e3a81af12b53c84',
            'duration': 1879,
            'timestamp': 1774940754,
            'upload_date': '20260331',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg)',
            'width': 1920,
            'height': 1080,
        },
        'add_ie': ['OnetPl'],
    }, {
        'url': 'http://onet.tv/k/openerfestival/open-er-festival-2016-najdziwniejsze-wymagania-gwiazd/qbpyqc',
        'skip': 'video gone',
        'md5': '436102770fb095c75b8bb0392d3da9ff',
        'info_dict': {
            'id': 'qbpyqc',
            'display_id': 'open-er-festival-2016-najdziwniejsze-wymagania-gwiazd',
            'ext': 'mp4',
            'title': 'Open\'er Festival 2016: najdziwniejsze wymagania gwiazd',
            'description': 'Trzy samochody, których nigdy nie użyto, prywatne spa, hotel dekorowany czarnym suknem czy nielegalne używki. Organizatorzy koncertów i festiwali muszą stawać przed nie lada wyzwaniem zapraszając gwia...',
            'upload_date': '20160705',
            'timestamp': 1467721580,
        },
    }, {
        'url': 'https://onet100.vod.pl/k/openerfestival/open-er-festival-2016-najdziwniejsze-wymagania-gwiazd/qbpyqc',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel, display_id, video_id = self._match_valid_url(url).group(
            'channel', 'display_id', 'id')
        # Clip pages now live on video.onet.pl (same Ring Publishing player as onet.pl)
        return self.url_result(
            f'https://video.onet.pl/{channel}/{display_id}/{video_id}',
            OnetPlIE.ie_key(), video_id)


class OnetChannelIE(OnetBaseIE):
    _VALID_URL = OnetBaseIE._URL_BASE_RE + r'(?P<id>[a-z]+)(?:[?#]|$)'
    IE_NAME = 'onet.tv:channel'

    _TESTS = [{
        'url': 'http://onet.tv/k/openerfestival',
        'skip': 'video gone',
        'info_dict': {
            'id': 'openerfestival',
            'title': "Open'er Festival",
            'description': "Tak było na Open'er Festival 2016! Oglądaj nasze reportaże i wywiady z artystami.",
        },
        'playlist_mincount': 35,
    }, {
        'url': 'https://onet100.vod.pl/k/openerfestival',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        webpage = self._download_webpage(url, channel_id)

        current_clip_info = self._parse_json(self._search_regex(
            r'var\s+currentClip\s*=\s*({[^}]+})', webpage, 'video info'), channel_id,
            transform_source=lambda s: js_to_json(re.sub(r'\'\s*\+\s*\'', '', s)))
        video_id = remove_start(current_clip_info['ckmId'], 'mvp:')
        video_name = url_basename(current_clip_info['url'])

        if not self._yes_playlist(channel_id, video_name, playlist_label='channel'):
            return self._extract_from_id(video_id, webpage)

        matches = re.findall(
            rf'<a[^>]+href=[\'"]({self._URL_BASE_RE}[a-z]+/[0-9a-z-]+/[0-9a-z]+)',
            webpage)
        entries = [
            self.url_result(video_link, OnetIE.ie_key())
            for video_link in matches]

        channel_title = strip_or_none(get_element_by_class('o_channelName', webpage))
        channel_description = strip_or_none(get_element_by_class('o_channelDesc', webpage))
        return self.playlist_result(entries, channel_id, channel_title, channel_description)


class OnetPlIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?(?:onet|businessinsider\.com|plejada)\.pl/(?:[^/]+/)+(?P<id>[0-9a-z]+)'
    IE_NAME = 'onet.pl'

    _TESTS = [{
        'url': 'https://video.onet.pl/zielony-onet/climate-facts-matter-unia-europejska-walczy-z-dezinformacja-klimatyczna/7nzsf9l',
        'md5': 'ca5a76525edeb2c436597dde04c0b904',
        'info_dict': {
            'id': '2449258.2021405591',
            'ext': 'mp4',
            'title': 'Climate Facts Matter. Unia Europejska walczy z dezinformacją klimatyczną.',
            'description': 'md5:107db8722dae06931e3a81af12b53c84',
            'duration': 1879,
            'timestamp': 1774940754,
            'upload_date': '20260331',
            'thumbnail': r're:https?://.*\.(?:jpg|jpeg)',
            'width': 1920,
            'height': 1080,
        },
    }, {
        'url': 'http://eurosport.onet.pl/zimowe/skoki-narciarskie/ziobro-wygral-kwalifikacje-w-pjongczangu/9ckrly',
        'skip': 'video gone',
        'md5': 'b94021eb56214c3969380388b6e73cb0',
        'info_dict': {
            'id': '1561707.1685479',
            'ext': 'mp4',
            'title': 'Ziobro wygrał kwalifikacje w Pjongczangu',
            'description': 'md5:61fb0740084d2d702ea96512a03585b4',
            'upload_date': '20170214',
            'timestamp': 1487078046,
        },
    }, {
        # embedded via pulsembed
        'url': 'http://film.onet.pl/pensjonat-nad-rozlewiskiem-relacja-z-planu-serialu/y428n0',
        'skip': 'video gone',
        'info_dict': {
            'id': '501235.965429946',
            'ext': 'mp4',
            'title': '"Pensjonat nad rozlewiskiem": relacja z planu serialu',
            'upload_date': '20170622',
            'timestamp': 1498159955,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://film.onet.pl/zwiastuny/ghost-in-the-shell-drugi-zwiastun-pl/5q6yl3',
        'only_matching': True,
    }, {
        'url': 'http://moto.onet.pl/jak-wybierane-sa-miejsca-na-fotoradary/6rs04e',
        'only_matching': True,
    }, {
        'url': 'http://businessinsider.com.pl/wideo/scenariusz-na-koniec-swiata-wedlug-nasa/dwnqptk',
        'only_matching': True,
    }, {
        'url': 'http://plejada.pl/weronika-rosati-o-swoim-domniemanym-slubie/n2bq89',
        'only_matching': True,
    }]

    def _search_mvp_id(self, webpage, default=NO_DEFAULT):
        return self._search_regex(
            r'data-(?:params-)?mvp=["\'](\d+\.\d+|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})',
            webpage, 'mvp id', default=default)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        mvp_id = self._search_mvp_id(webpage, default=None)
        media_webpage = webpage

        pulsembed_url = self._search_regex(
            r'data-src=(["\'])(?P<url>(?:https?:)?//pulsembed\.eu/.+?)\1',
            webpage, 'pulsembed url', default=None, group='url')
        if pulsembed_url:
            media_webpage = self._download_webpage(
                self._proto_relative_url(pulsembed_url), video_id,
                'Downloading pulsembed webpage')
            mvp_id = mvp_id or self._search_mvp_id(media_webpage, default=None)

        json_ld = self._search_json_ld(
            media_webpage, mvp_id or video_id, expected_type='VideoObject', default={})
        content_url = url_or_none(json_ld.pop('url', None))
        json_ld.pop('ext', None)

        embed_url = None
        for e in self._yield_json_ld(media_webpage, mvp_id or video_id, fatal=False, default=[]):
            if isinstance(e, dict) and e.get('@type') == 'VideoObject':
                embed_url = url_or_none(e.get('embedUrl'))
                if embed_url:
                    break
        if not embed_url and mvp_id:
            embed_url = f'https://grupa-onet.embed.videos.ringpublishing.com/{mvp_id}'

        formats = []
        if embed_url:
            embed_page = self._download_webpage(
                embed_url, mvp_id or video_id,
                'Downloading Ring Publishing embed', fatal=False)
            if embed_page:
                video_url = self._search_regex(
                    r'\bsrc:\s*["\']([^"\']+)["\']', embed_page, 'video url',
                    default=None)
                if video_url:
                    formats.append({'url': video_url})

        if not formats and content_url:
            if determine_ext(content_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    content_url, mvp_id or video_id, 'mp4', m3u8_id='hls'))
            else:
                formats.append({'url': content_url})

        if not formats:
            if mvp_id:
                return self.url_result(
                    f'onetmvp:{mvp_id}', OnetMVPIE.ie_key(), video_id=mvp_id)
            raise ExtractorError('No video found', expected=True)

        return {
            **json_ld,
            'id': mvp_id or video_id,
            'title': json_ld.get('title') or self._og_search_title(webpage),
            'description': json_ld.get('description') or self._og_search_description(
                webpage, default=None),
            'formats': formats,
        }
