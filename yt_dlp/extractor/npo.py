import json
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    merge_dicts,
    orderedSet,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class NPOIE(InfoExtractor):
    IE_NAME = 'npo'
    IE_DESC = 'npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl'
    _VALID_URL = r'''(?x)
                    (?:
                        npo:|
                        https?://
                            (?:www\.)?
                            (?:
                                npo\.nl/(?:[^/]+/)*|
                                (?:ntr|npostart)\.nl/(?:[^/]+/){2,}|
                                omroepwnl\.nl/video/fragment/[^/]+__|
                                (?:zapp|npo3)\.nl/(?:[^/]+/){2,}
                            )
                        )
                        (?P<id>[^/?#]+)
                '''

    _TESTS = [{
        'url': 'http://www.npo.nl/nieuwsuur/22-06-2014/VPWON_1220719',
        'md5': '4b3f9c429157ec4775f2c9cb7b911016',
        'info_dict': {
            'id': 'VPWON_1220719',
            'ext': 'm4v',
            'title': 'Nieuwsuur',
            'description': 'Dagelijks tussen tien en elf: nieuws, sport en achtergronden.',
            'upload_date': '20140622',
        },
        'skip': 'Video was removed',
    }, {
        'url': 'http://www.npo.nl/de-mega-mike-mega-thomas-show/27-02-2009/VARA_101191800',
        'md5': 'da50a5787dbfc1603c4ad80f31c5120b',
        'info_dict': {
            'id': 'VARA_101191800',
            'ext': 'm4v',
            'title': 'De Mega Mike & Mega Thomas show: The best of.',
            'description': 'md5:3b74c97fc9d6901d5a665aac0e5400f4',
            'upload_date': '20090227',
            'duration': 2400,
        },
        'skip': 'Video was removed',
    }, {
        'url': 'https://npo.nl/start/afspelen/zwart-geld-de-toekomst-komt-uit-afrika',
        'md5': '8c30593a81ac80d65b531eaf2a92ac02',
        'info_dict': {
            'id': 'VPWON_1169289',
            'ext': 'mp4',
            'title': 'Zwart geld: de toekomst komt uit Afrika',
            'description': 'md5:52cf4eefbc96fffcbdc06d024147abea',
            'upload_date': '20130225',
            'duration': 3000,
            'creators': ['NED2'],
            'series': 'VPRO Tegenlicht',
            'timestamp': 1361822340,
            'thumbnail': r're:https://assets-start\.npo\.nl/resources/.+',
            'episode': 'Zwart geld: de toekomst komt uit Afrika',
            'episode_number': 18,
        },
    }, {
        'url': 'http://www.npo.nl/tegenlicht/25-02-2013/VPWON_1169289',
        'only_matching': True,
    }, {
        'url': 'http://www.npo.nl/de-nieuwe-mens-deel-1/21-07-2010/WO_VPRO_043706',
        'info_dict': {
            'id': 'WO_VPRO_043706',
            'ext': 'mp4',
            'title': 'De nieuwe mens - Deel 1',
            'description': 'md5:518ae51ba1293ffb80d8d8ce90b74e4b',
            'duration': 4680.0,
            'episode': 'De nieuwe mens - Deel 1',
            'thumbnail': 'https://images.poms.omroep.nl/image/s1080/6289',
            'series': 'De nieuwe mens - Deel 1',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # non asf in streams
        'url': 'http://www.npo.nl/hoe-gaat-europa-verder-na-parijs/10-01-2015/WO_NOS_762771',
        'info_dict': {
            'id': 'WO_NOS_762771',
            'ext': 'mp4',
            'title': 'Hoe gaat Europa verder na Parijs?',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Video was removed',
    }, {
        'url': 'http://www.ntr.nl/Aap-Poot-Pies/27/detail/Aap-poot-pies/VPWON_1233944#content',
        'info_dict': {
            'id': 'VPWON_1233944',
            'ext': 'mp4',
            'title': 'Aap, poot, pies',
            'description': 'md5:4b46b1b9553b4c036a04d2a532a137e6',
            'duration': 599.98,
            'episode': 'Aap, poot, pies',
            'thumbnail': 'https://images.poms.omroep.nl/image/s1080/608116',
            'series': 'Aap, poot, pies',
            'creators': ['NED3'],
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.omroepwnl.nl/video/fragment/vandaag-de-dag-verkiezingen__POMS_WNL_853698',
        'info_dict': {
            'id': 'POW_00996502',
            'ext': 'm4v',
            'title': '''"Dit is wel een 'landslide'..."''',
            'description': 'md5:f8d66d537dfb641380226e31ca57b8e8',
            'upload_date': '20150508',
            'duration': 462,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Video was removed',
    }, {
        # audio
        'url': 'http://www.npo.nl/jouw-stad-rotterdam/29-01-2017/RBX_FUNX_6683215/RBX_FUNX_7601437',
        'info_dict': {
            'id': 'RBX_FUNX_6683215',
            'ext': 'mp3',
            'title': 'Jouw Stad Rotterdam',
            'description': 'md5:db251505244f097717ec59fabc372d9f',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Video was removed',
    }, {
        'url': 'http://www.zapp.nl/de-bzt-show/gemist/KN_1687547',
        'only_matching': True,
    }, {
        'url': 'http://www.zapp.nl/de-bzt-show/filmpjes/POMS_KN_7315118',
        'only_matching': True,
    }, {
        'url': 'http://www.zapp.nl/beste-vrienden-quiz/extra-video-s/WO_NTR_1067990',
        'only_matching': True,
    }, {
        'url': 'https://www.npo3.nl/3onderzoekt/16-09-2015/VPWON_1239870',
        'only_matching': True,
    }, {
        # live stream
        'url': 'npo:LI_NL1_4188102',
        'only_matching': True,
    }, {
        'url': 'http://www.npo.nl/radio-gaga/13-06-2017/BNN_101383373',
        'only_matching': True,
    }, {
        'url': 'https://www.zapp.nl/1803-skelterlab/instructie-video-s/740-instructievideo-s/POMS_AT_11736927',
        'only_matching': True,
    }, {
        'url': 'https://www.npostart.nl/broodje-gezond-ei/28-05-2018/KN_1698996',
        'only_matching': True,
    }, {
        'url': 'https://npo.nl/KN_1698996',
        'only_matching': True,
    }, {
        'url': 'https://npo.nl/start/afspelen/nos-journaal_106198',
        'only_matching': True,
    }, {
        'url': 'https://www.npo3.nl/the-genius/21-11-2022/VPWON_1341105',
        'info_dict': {
            'id': 'VPWON_1341105',
            'ext': 'mp4',
            'duration': 2658,
            'series': 'The Genius',
            'description': 'md5:b5b23d0c9bc0092055146fa5e2a81629',
            'title': 'The Genius',
            'timestamp': 1669062000,
            'creators': ['NED3'],
            'episode': 'The Genius',
            'thumbnail': 'https://assets-start.npo.nl/resources/2023/07/01/2e062997-ad28-4788-970c-bf60d7c8ebf4.jpg',
            'episode_number': 8,
            'upload_date': '20221121',
        },
        'params': {
            'skip_download': True,
        },
    }]

    @classmethod
    def suitable(cls, url):
        return (False if any(ie.suitable(url)
                for ie in (NPOLiveIE, NPORadioIE, NPORadioFragmentIE))
                else super().suitable(url))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        program = {}
        if re.fullmatch(r'[A-Z]{2,}_\w+', display_id):
            video_id = display_id
            search = self._download_json(
                'https://npo.nl/start/api/domain/search-collection-items',
                video_id, 'Downloading program search JSON', fatal=False, query={
                    'searchQuery': video_id,
                    'searchType': 'broadcasts',
                    'subscriptionType': 'anonymous',
                })
            program = traverse_obj(search, (
                'items', lambda _, v: v.get('productId') == video_id),
                get_all=False) or {}
        else:
            program = self._download_json(
                f'https://npo.nl/start/api/domain/program-detail?slug={display_id}',
                display_id, 'Downloading program details JSON')
            video_id = program['productId']

        token = self._download_json(
            f'https://npo.nl/start/api/domain/player-token?productId={video_id}',
            video_id, 'Downloading token')['jwt']

        drm = False
        geo = False
        is_live = False
        format_urls = set()
        formats = []
        stream_meta = {}
        subtitles = {}
        for profile_name in ('hls', 'dash', 'smooth'):
            profile = self._download_json(
                'https://prod.npoplayer.nl/stream-link', video_id,
                f'Downloading {profile_name} profile JSON', fatal=False,
                data=json.dumps({
                    'profileName': profile_name,
                    'referrerUrl': url,
                }).encode(), headers={
                    'Authorization': token,
                    'Content-Type': 'application/json',
                    'Origin': 'https://npo.nl',
                    'Referer': 'https://npo.nl/',
                }, expected_status=(400, 401, 403, 404, 451, 500))
            if not isinstance(profile, dict):
                continue
            if profile.get('status') == 451:
                geo = True
                continue
            if not stream_meta and isinstance(profile.get('metadata'), dict):
                stream_meta = profile['metadata']
            for cc in traverse_obj(profile, ('assets', 'subtitles', ...)):
                cc_url = url_or_none(cc.get('location'))
                if not cc_url:
                    continue
                lang = str_or_none(cc.get('iso')) or 'nl'
                subtitles.setdefault(lang, []).append({
                    'url': cc_url,
                    'name': cc.get('name'),
                })
            stream = profile.get('stream')
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('streamURL') or stream.get('src'))
            if not stream_url or stream_url in format_urls:
                continue
            format_urls.add(stream_url)
            if stream.get('isLiveStream'):
                is_live = True
            if stream.get('drmType') or stream.get('drmToken') or stream.get('drm') or stream.get('protection') or stream.get('keySystemOptions'):
                drm = True
                continue
            stream_ext = determine_ext(stream_url)
            if stream_ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))
            elif stream_ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            elif re.search(r'\.isml?/Manifest', stream_url):
                formats.extend(self._extract_ism_formats(
                    stream_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'url': stream_url,
                })

        if not formats:
            if geo:
                self.raise_geo_restricted(countries=['NL'])
            if not self.get_param('allow_unplayable_formats') and drm:
                self.report_drm(video_id)

        duration = int_or_none(stream_meta.get('duration'))
        if duration and duration > 10000:
            duration /= 1000

        return merge_dicts(traverse_obj(program, {
            'title': ('title', {str}),
            'episode': ('title', {str}),
            'episode_number': ('programKey', {int_or_none}),
            'duration': ('durationInSeconds', {int_or_none}),
            'description': ('synopsis', ('long', 'short', 'brief'), {str}, any),
            'series': ('series', 'title', {str}),
            'timestamp': (('firstBroadcastDate', 'publishedDateTime'), {int_or_none}, any),
            'thumbnail': ('images', 0, 'url', {url_or_none}),
        }), {
            'title': stream_meta.get('subTitle') or stream_meta.get('title'),
            'episode': stream_meta.get('subTitle'),
            'description': stream_meta.get('description'),
            'duration': duration,
            'creator': stream_meta.get('channel'),
            'series': stream_meta.get('title'),
            'thumbnail': url_or_none(stream_meta.get('poster')),
            'is_live': is_live or None,
        }, {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        })


class NPOLiveIE(InfoExtractor):
    IE_NAME = 'npo.nl:live'
    _VALID_URL = r'https?://(?:www\.)?npo(?:start)?\.nl/(?:start/)?live(?:/(?P<id>[^/?#&]+))?'

    _TESTS = [{
        'url': 'http://www.npo.nl/live/npo-1',
        'info_dict': {
            'id': 'LI_NL1_4188102',
            'display_id': 'npo1',
            'ext': 'mp4',
            'title': 're:^NPO 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'geo restricted',
    }, {
        'url': 'http://www.npo.nl/live',
        'only_matching': True,
    }, {
        'url': 'https://www.npostart.nl/live/npo-1',
        'only_matching': True,
    }, {
        'url': 'https://npo.nl/start/live?channel=NPO1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        if not display_id:
            display_id = urllib.parse.parse_qs(
                urllib.parse.urlparse(url).query).get('channel', [None])[0]
        display_id = re.sub(r'^npo-', 'npo', (display_id or 'npo1').lower())

        channels = self._download_json(
            'https://npo.nl/start/api/domain/guide-channels', display_id,
            'Downloading live channels JSON')
        live_id = None
        for channel in channels or []:
            livestream = channel.get('livestream') or {}
            if livestream.get('slug') == display_id or (channel.get('title') or '').lower() == display_id:
                live_id = livestream.get('productId') or channel.get('externalId')
                break
        if not live_id:
            live_id = traverse_obj(channels, (0, 'livestream', 'productId', {str}))
        if not live_id:
            self.raise_no_formats('Unable to extract live id', expected=True)

        return {
            '_type': 'url_transparent',
            'url': f'npo:{live_id}',
            'ie_key': NPOIE.ie_key(),
            'id': live_id,
            'display_id': display_id,
        }


class NPORadioIE(InfoExtractor):
    IE_NAME = 'npo.nl:radio'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/radio/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.npo.nl/radio/radio-1',
        'skip': 'video gone',
        'info_dict': {
            'id': 'radio-1',
            'ext': 'mp3',
            'title': 're:^NPO Radio 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }

    @classmethod
    def suitable(cls, url):
        return False if NPORadioFragmentIE.suitable(url) else super().suitable(url)

    @staticmethod
    def _html_get_attribute_regex(attribute):
        return rf'{attribute}\s*=\s*\'([^\']+)\''

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            self._html_get_attribute_regex('data-channel'), webpage, 'title')

        stream = self._parse_json(
            self._html_search_regex(self._html_get_attribute_regex('data-streams'), webpage, 'data-streams'),
            video_id)

        codec = stream.get('codec')

        return {
            'id': video_id,
            'url': stream['url'],
            'title': title,
            'acodec': codec,
            'ext': codec,
            'is_live': True,
        }


class NPORadioFragmentIE(InfoExtractor):
    IE_NAME = 'npo.nl:radio:fragment'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/radio/[^/]+/fragment/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.npo.nl/radio/radio-5/fragment/174356',
        'skip': 'video gone',
        'md5': 'dd8cc470dad764d0fdc70a9a1e2d18c2',
        'info_dict': {
            'id': '174356',
            'ext': 'mp3',
            'title': 'Jubileumconcert Willeke Alberti',
        },
    }

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(url, audio_id)

        title = self._html_search_regex(
            rf'href="/radio/[^/]+/fragment/{audio_id}" title="([^"]+)"',
            webpage, 'title')

        audio_url = self._search_regex(
            r"data-streams='([^']+)'", webpage, 'audio url')

        return {
            'id': audio_id,
            'url': audio_url,
            'title': title,
        }


class NPODataMidEmbedIE(InfoExtractor):  # XXX: Conventionally, base classes should end with BaseIE/InfoExtractor
    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            r'data-mid=(["\'])(?P<id>(?:(?!\1).)+)\1', webpage, 'video_id', group='id')
        return {
            '_type': 'url_transparent',
            'ie_key': 'NPO',
            'url': f'npo:{video_id}',
            'display_id': display_id,
        }


class SchoolTVIE(NPODataMidEmbedIE):
    IE_NAME = 'schooltv'
    _VALID_URL = r'https?://(?:www\.)?schooltv\.nl/video/(?P<id>[^/?#&]+)'

    _TEST = {
        'url': 'http://www.schooltv.nl/video/ademhaling-de-hele-dag-haal-je-adem-maar-wat-gebeurt-er-dan-eigenlijk-in-je-lichaam/',
        'info_dict': {
            'id': 'WO_NTR_429477',
            'display_id': 'ademhaling-de-hele-dag-haal-je-adem-maar-wat-gebeurt-er-dan-eigenlijk-in-je-lichaam',
            'title': 'Ademhaling: De hele dag haal je adem. Maar wat gebeurt er dan eigenlijk in je lichaam?',
            'ext': 'mp4',
            'description': 'md5:abfa0ff690adb73fd0297fd033aaa631',
        },
        'params': {
            # Skip because of m3u8 download
            'skip_download': True,
        },
    }


class HetKlokhuisIE(NPODataMidEmbedIE):
    IE_NAME = 'hetklokhuis'
    _VALID_URL = r'https?://(?:www\.)?hetklokhuis\.nl/[^/]+/\d+/(?P<id>[^/?#&]+)'

    _TEST = {
        'url': 'http://hetklokhuis.nl/tv-uitzending/3471/Zwaartekrachtsgolven',
        'skip': 'video gone',
        'info_dict': {
            'id': 'VPWON_1260528',
            'display_id': 'Zwaartekrachtsgolven',
            'ext': 'm4v',
            'title': 'Het Klokhuis: Zwaartekrachtsgolven',
            'description': 'md5:c94f31fb930d76c2efa4a4a71651dd48',
            'upload_date': '20170223',
        },
        'params': {
            'skip_download': True,
        },
    }


class NPOPlaylistBaseIE(NPOIE):  # XXX: Do not subclass from concrete IE
    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [
            self.url_result(f'npo:{video_id}' if not video_id.startswith('http') else video_id)
            for video_id in orderedSet(re.findall(self._PLAYLIST_ENTRY_RE, webpage))
        ]

        playlist_title = self._html_search_regex(
            self._PLAYLIST_TITLE_RE, webpage, 'playlist title',
            default=None) or self._og_search_title(webpage)

        return self.playlist_result(entries, playlist_id, playlist_title)


class VPROIE(NPOPlaylistBaseIE):
    IE_NAME = 'vpro'
    _VALID_URL = r'https?://(?:www\.)?(?:(?:tegenlicht\.)?vpro|2doc)\.nl/(?:[^/]+/)*(?P<id>[^/]+)\.html'
    _PLAYLIST_TITLE_RE = (r'<h1[^>]+class=["\'].*?\bmedia-platform-title\b.*?["\'][^>]*>([^<]+)',
                          r'<h5[^>]+class=["\'].*?\bmedia-platform-subtitle\b.*?["\'][^>]*>([^<]+)')
    _PLAYLIST_ENTRY_RE = r'data-media-id="([^"]+)"'

    _TESTS = [
        {
            'url': 'http://tegenlicht.vpro.nl/afleveringen/2012-2013/de-toekomst-komt-uit-afrika.html',
            'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
            'info_dict': {
                'id': 'VPWON_1169289',
                'ext': 'm4v',
                'title': 'De toekomst komt uit Afrika',
                'description': 'md5:52cf4eefbc96fffcbdc06d024147abea',
                'upload_date': '20130225',
            },
            'skip': 'Video gone',
        },
        {
            'url': 'http://www.vpro.nl/programmas/2doc/2015/sergio-herman.html',
            'skip': 'video gone',
            'info_dict': {
                'id': 'sergio-herman',
                'title': 'sergio herman: fucking perfect',
            },
            'playlist_count': 2,
        },
        {
            # playlist with youtube embed
            'url': 'http://www.vpro.nl/programmas/2doc/2015/education-education.html',
            'skip': 'video gone',
            'info_dict': {
                'id': 'education-education',
                'title': 'education education',
            },
            'playlist_count': 2,
        },
        {
            'url': 'http://www.2doc.nl/documentaires/series/2doc/2015/oktober/de-tegenprestatie.html',
            'skip': 'video gone',
            'info_dict': {
                'id': 'de-tegenprestatie',
                'title': 'De Tegenprestatie',
            },
            'playlist_count': 2,
        }, {
            'url': 'http://www.2doc.nl/speel~VARA_101375237~mh17-het-verdriet-van-nederland~.html',
            'skip': 'video gone',
            'info_dict': {
                'id': 'VARA_101375237',
                'ext': 'm4v',
                'title': 'MH17: Het verdriet van Nederland',
                'description': 'md5:09e1a37c1fdb144621e22479691a9f18',
                'upload_date': '20150716',
            },
            'params': {
                # Skip because of m3u8 download
                'skip_download': True,
            },
        },
    ]


class WNLIE(NPOPlaylistBaseIE):
    IE_NAME = 'wnl'
    _VALID_URL = r'https?://(?:www\.)?omroepwnl\.nl/video/detail/(?P<id>[^/]+)__\d+'
    _PLAYLIST_TITLE_RE = r'(?s)<h1[^>]+class="subject"[^>]*>(.+?)</h1>'
    _PLAYLIST_ENTRY_RE = r'<a[^>]+href="([^"]+)"[^>]+class="js-mid"[^>]*>Deel \d+'

    _TESTS = [{
        'url': 'http://www.omroepwnl.nl/video/detail/vandaag-de-dag-6-mei__060515',
        'info_dict': {
            'id': 'vandaag-de-dag-6-mei',
            'title': 'Vandaag de Dag 6 mei',
        },
        'playlist_count': 4,
    }]


class AndereTijdenIE(NPOPlaylistBaseIE):
    IE_NAME = 'anderetijden'
    _VALID_URL = r'https?://(?:www\.)?anderetijden\.nl/programma/(?:[^/]+/)+(?P<id>[^/?#&]+)'
    _PLAYLIST_TITLE_RE = r'(?s)<h1[^>]+class=["\'].*?\bpage-title\b.*?["\'][^>]*>(.+?)</h1>'
    _PLAYLIST_ENTRY_RE = r'<figure[^>]+class=["\']episode-container episode-page["\'][^>]+data-prid=["\'](.+?)["\']'

    _TESTS = [{
        'url': 'http://anderetijden.nl/programma/1/Andere-Tijden/aflevering/676/Duitse-soldaten-over-de-Slag-bij-Arnhem',
        'skip': 'video gone',
        'info_dict': {
            'id': 'Duitse-soldaten-over-de-Slag-bij-Arnhem',
            'title': 'Duitse soldaten over de Slag bij Arnhem',
        },
        'playlist_count': 3,
    }]
