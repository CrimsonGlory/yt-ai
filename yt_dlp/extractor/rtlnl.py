from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class RtlNlIE(InfoExtractor):
    IE_NAME = 'rtl.nl'
    IE_DESC = 'rtl.nl and rtlxl.nl'
    _EMBED_REGEX = [
        r'<iframe[^>]+?\bsrc=(?P<q1>[\'"])(?P<url>(?:https?:)?//(?:(?:www|static)\.)?rtl\.nl/(?:system/videoplayer/[^"]+(?:video_)?)?embed[^"]+)(?P=q1)',
        r'<iframe[^>]+?\bsrc=(?P<q1>[\'"])(?P<url>(?:https?:)?//embed\.rtl\.nl/[^"]+)(?P=q1)',
    ]
    _VALID_URL = r'''(?x)
        https?://(?:(?:www|static)\.)?
        (?:
            rtlxl\.nl/(?:[^\#]*\#!|programma)/[^/]+/|
            rtl\.nl/(?:
                (?:system/videoplayer/(?:[^/]+/)+(?:video_)?embed\.html|embed)\b.+?\buuid=|
                (?:[^/?#]+/)*video/
            )|
            embed\.rtl\.nl/?\S*?[\#?&]uuid=
        )
        (?P<id>[0-9a-f-]+)'''

    _TESTS = [{
        # Current RTL XL / rtl.nl VOD (FairPlay HLS + Widevine DASH)
        'url': 'https://www.rtlxl.nl/programma/rtl-nieuws/9ce11b6e-3aaa-4d29-b16b-f5a7dd544282',
        'info_dict': {
            'id': '9ce11b6e-3aaa-4d29-b16b-f5a7dd544282',
            'ext': 'mp4',
            'title': 'RTL Nieuws - Fleur Agema maakte statement voor enquetecommissie: \'Ik zoek een baan, wil burgemeester worden\'',
            'description': 'md5:b4a2e01756f963b7d2e443e7c10664ef',
            'timestamp': 1787744812,
            'upload_date': '20260826',
            'duration': 61,
            'series': 'RTL Nieuws',
            'thumbnail': r're:https://(?:covers|screenshots)\.rtl\.nl/.+',
        },
        'skip': 'DRM protected (FairPlay SAMPLE-AES HLS / Widevine DASH)',
    }, {
        # new URL schema
        'url': 'https://www.rtlxl.nl/programma/rtl-nieuws/0bd1384d-d970-3086-98bb-5c104e10c26f',
        'skip': 'video gone',
        'md5': '490428f1187b60d714f34e1f2e3af0b6',
        'info_dict': {
            'id': '0bd1384d-d970-3086-98bb-5c104e10c26f',
            'ext': 'mp4',
            'title': 'RTL Nieuws',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'timestamp': 1593293400,
            'upload_date': '20200627',
            'duration': 661.08,
        },
    }, {
        # old URL schema
        'url': 'http://www.rtlxl.nl/#!/rtl-nieuws-132237/82b1aad1-4a14-3d7b-b554-b0aed1b2c416',
        'md5': '473d1946c1fdd050b2c0161a4b13c373',
        'info_dict': {
            'id': '82b1aad1-4a14-3d7b-b554-b0aed1b2c416',
            'ext': 'mp4',
            'title': 'RTL Nieuws',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'timestamp': 1461951000,
            'upload_date': '20160429',
            'duration': 1167.96,
        },
        'skip': '404',
    }, {
        # best format available a3t
        'url': 'http://www.rtl.nl/system/videoplayer/derden/rtlnieuws/video_embed.html#uuid=84ae5571-ac25-4225-ae0c-ef8d9efb2aed/autoplay=false',
        'skip': 'video gone',
        'md5': 'dea7474214af1271d91ef332fb8be7ea',
        'info_dict': {
            'id': '84ae5571-ac25-4225-ae0c-ef8d9efb2aed',
            'ext': 'mp4',
            'timestamp': 1424039400,
            'title': 'RTL Nieuws - Nieuwe beelden Kopenhagen: chaos direct na aanslag',
            'thumbnail': r're:^https?://screenshots\.rtl\.nl/(?:[^/]+/)*sz=[0-9]+x[0-9]+/uuid=84ae5571-ac25-4225-ae0c-ef8d9efb2aed$',
            'upload_date': '20150215',
            'description': 'Er zijn nieuwe beelden vrijgegeven die vlak na de aanslag in Kopenhagen zijn gemaakt. Op de video is goed te zien hoe omstanders zich bekommeren om één van de slachtoffers, terwijl de eerste agenten ter plaatse komen.',
        },
    }, {
        # empty synopsis and missing episodes (see https://github.com/ytdl-org/youtube-dl/issues/6275)
        # best format available nettv
        'url': 'http://www.rtl.nl/system/videoplayer/derden/rtlnieuws/video_embed.html#uuid=f536aac0-1dc3-4314-920e-3bd1c5b3811a/autoplay=false',
        'skip': 'video gone',
        'info_dict': {
            'id': 'f536aac0-1dc3-4314-920e-3bd1c5b3811a',
            'ext': 'mp4',
            'title': 'RTL Nieuws - Meer beelden van overval juwelier',
            'thumbnail': r're:^https?://screenshots\.rtl\.nl/(?:[^/]+/)*sz=[0-9]+x[0-9]+/uuid=f536aac0-1dc3-4314-920e-3bd1c5b3811a$',
            'timestamp': 1437233400,
            'upload_date': '20150718',
            'duration': 30.474,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # encrypted m3u8 streams, georestricted
        'url': 'http://www.rtlxl.nl/#!/afl-2-257632/52a74543-c504-4cde-8aa8-ec66fe8d68a7',
        'only_matching': True,
    }, {
        'url': 'http://www.rtl.nl/system/videoplayer/derden/embed.html#!/uuid=bb0353b0-d6a4-1dad-90e9-18fe75b8d1f0',
        'only_matching': True,
    }, {
        'url': 'http://rtlxl.nl/?_ga=1.204735956.572365465.1466978370#!/rtl-nieuws-132237/3c487912-023b-49ac-903e-2c5d79f8410f',
        'only_matching': True,
    }, {
        'url': 'https://www.rtl.nl/video/c603c9c2-601d-4b5e-8175-64f1e942dc7d/',
        'only_matching': True,
    }, {
        'url': 'https://static.rtl.nl/embed/?uuid=1a2970fc-5c0b-43ff-9fdc-927e39e6d1bc&autoplay=false&publicatiepunt=rtlnieuwsnl',
        'only_matching': True,
    }, {
        # new embed URL schema
        'url': 'https://embed.rtl.nl/#uuid=84ae5571-ac25-4225-ae0c-ef8d9efb2aed/autoplay=false',
        'only_matching': True,
    }, {
        'url': 'https://www.rtl.nl/nieuws/politiek/video/9ce11b6e-3aaa-4d29-b16b-f5a7dd544282/fleur-agema-maakte-statement-voor',
        'only_matching': True,
    }, {
        'url': 'https://embed.rtl.nl?uuid=9ce11b6e-3aaa-4d29-b16b-f5a7dd544282&publicatiepunt=rtlnieuwsshare&autoplay=false',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        uuid = self._match_id(url)

        metadata = self._download_json(
            f'https://api.rtl.nl/rtlxl/metadata/api/metadata/{uuid}',
            uuid, fatal=False)

        token = self._download_json(
            'https://api.rtl.nl/rtlxl/token/api/token', uuid,
            note='Downloading access token')['accessToken']
        play = self._download_json(
            f'https://api.rtl.nl/watch/play/api/v2/play/xl/{uuid}',
            uuid, query={'device': 'web'}, headers={
                'Authorization': f'Bearer {token}',
                'rtl-platform': 'web',
            })

        formats = []
        hls_url = traverse_obj(play, ('manifests', 'hls', {url_or_none}))
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, uuid, 'mp4', m3u8_id='hls', fatal=False))
        mpd_url = traverse_obj(play, ('manifests', 'dash', {url_or_none}))
        if mpd_url:
            formats.extend(self._extract_mpd_formats(
                mpd_url, uuid, mpd_id='dash', fatal=False))

        # Play API always attaches FairPlay/Widevine/PlayReady; HLS keys live on
        # media playlists so the master m3u8 is not enough to set has_drm.
        if traverse_obj(play, 'drm'):
            for f in formats:
                f['has_drm'] = True

        if not formats:
            error = traverse_obj(play, ('error', ('description', 'code'), {str}), get_all=False)
            error_l = (error or '').lower()
            if 'ipblocked' in error_l:
                self.raise_geo_restricted(countries=['NL'])
            if 'subscription' in error_l:
                self.raise_login_required(error)
            if not play.get('canPlay'):
                raise ExtractorError(error or 'Video unavailable', expected=True)
            self.report_drm(uuid)

        series = traverse_obj(metadata, ('series', 'title', {str}))
        title = traverse_obj(metadata, ('title', {str}))
        if series and title:
            full_title = f'{series} - {title}'
        else:
            full_title = title or series or uuid

        thumbnails = []
        for asset in traverse_obj(metadata, ('assets', ..., {dict})) or []:
            asset_url, asset_type = url_or_none(asset.get('url')), asset.get('type')
            if asset_url and asset_type in ('Cover', 'Poster', 'Still'):
                thumbnails.append({'id': asset_type.lower(), 'url': asset_url})

        return {
            'id': uuid,
            'title': full_title,
            'description': traverse_obj(metadata, ('synopsis', {str})),
            'duration': int_or_none(traverse_obj(metadata, 'duration')),
            'timestamp': parse_iso8601(traverse_obj(metadata, ('broadcastDateTime', {str}))),
            'series': series,
            'formats': formats,
            'thumbnails': thumbnails,
        }


class RTLLuBaseIE(InfoExtractor):
    _MEDIA_REGEX = {
        # Legacy custom elements, plus Brightspot/Next.js ReplayVideo + ReplayAudio payloads
        'video': [
            r'<rtl-player\s[^>]*\bhls\s*=\s*"([^"]+)',
            r'(https?://stream\.rtl\.lu/data/ondemand/video/e/hls/amlst:\d+/playlist\.m3u8)',
            r'\\?"hls\\?"\s*:\s*\\?"(https?://stream\.rtl\.lu/[^"\\]+\.m3u8)',
        ],
        'audio': [
            r'<rtl-audioplayer\s[^>]*\bsrc\s*=\s*"([^"]+)',
            r'(https?://replayaudio\.rtl\.lu/[^"\\]+\.mp3)',
        ],
        'thumbnail': [
            r'<rtl-player\s[^>]*\bposter\s*=\s*"([^"]+)',
            r'"poster"\s*:\s*\{[^}]*?"url"\s*:\s*"([^"]+)',
        ],
    }

    def get_media_url(self, webpage, video_id, media_type):
        return self._search_regex(self._MEDIA_REGEX[media_type], webpage, f'{media_type} url', default=None)

    def get_formats_and_subtitles(self, webpage, video_id):
        video_url, audio_url = self.get_media_url(webpage, video_id, 'video'), self.get_media_url(webpage, video_id, 'audio')

        formats, subtitles = [], {}
        if video_url is not None:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(video_url, video_id)
        if audio_url is not None:
            formats.append({'url': audio_url, 'ext': 'mp3', 'vcodec': 'none'})

        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        is_live = video_id in ('live', 'live-2', 'lauschteren')

        # TODO: extract comment from https://www.rtl.lu/comments?status=1&order=desc&context=news|article|<video_id>
        # we can context from <rtl-comments context=<context> in webpage
        webpage = self._download_webpage(url, video_id)

        formats, subtitles = self.get_formats_and_subtitles(webpage, video_id)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage, default=None),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': self.get_media_url(webpage, video_id, 'thumbnail') or self._og_search_thumbnail(webpage, default=None),
            'is_live': is_live,
        }


class RTLLuTeleVODIE(RTLLuBaseIE):
    IE_NAME = 'rtl.lu:tele-vod'
    _VALID_URL = r'https?://(?:www\.)?rtl\.lu/(tele/(?P<slug>[\w-]+)/v/|video/)(?P<id>\d+)(\.html)?'
    _TESTS = [{
        'url': 'https://www.rtl.lu/tele/de-journal-vun-der-tele/v/3266757.html',
        'skip': 'video gone',
        'info_dict': {
            'id': '3266757',
            'title': 'Informatiounsversammlung Héichwaasser',
            'ext': 'mp4',
            'thumbnail': 'https://replay-assets.rtl.lu/2021/11/16/d3647fc4-470d-11ec-adc2-3a00abd6e90f_00008.jpg',
            'description': 'md5:b1db974408cc858c9fd241812e4a2a14',
        },
    }, {
        'url': 'https://www.rtl.lu/video/3295215',
        'skip': 'video gone',
        'info_dict': {
            'id': '3295215',
            'title': 'Kulturassisen iwwer d\'Bestandsopnam vum Lëtzebuerger Konscht',
            'ext': 'mp4',
            'thumbnail': 'https://replay-assets.rtl.lu/2022/06/28/0000_3295215_0000.jpg',
            'description': 'md5:85bcd4e0490aa6ec969d9bf16927437b',
        },
    }]


class RTLLuArticleIE(RTLLuBaseIE):
    IE_NAME = 'rtl.lu:article'
    _VALID_URL = r'https?://(?:(?:www|5minutes|today|infos)\.)rtl\.lu/(?:[\w-]+/)+(?:a/|(?:[\w-]+-))(?P<id>\d+)(?:\.html)?'
    _TESTS = [{
        'url': 'https://www.rtl.lu/news/national/kann-een-als-premier-eigentlech-richteg-ofschalten-1774577552',
        'md5': '7400d306a1c660458f1dc09590bebe51',
        'info_dict': {
            'id': '1774577552',
            'ext': 'mp4',
            'title': 'Summerinterview - Luc Frieden: Kann een als Premier eigentlech richteg ofschalten?',
            'description': 'md5:9d7fc27d2ebec6420b02cd2106e40867',
            'thumbnail': r're:https://static-prod\.rtl\.lu/.+',
        },
    }, {
        # Audio-only (legacy /a/ID.html URL)
        'url': 'https://www.rtl.lu/sport/news/a/1934360.html',
        'only_matching': True,
    }, {
        # 5minutes
        'url': 'https://5minutes.rtl.lu/espace-frontaliers/frontaliers-en-questions/a/1853173.html',
        'skip': 'redirects to infos.rtl.lu homepage',
        'info_dict': {
            'id': '1853173',
            'ext': 'mp4',
            'description': 'md5:ac031da0740e997a5cf4633173634fee',
            'title': 'md5:87e17722ed21af0f24be3243f4ec0c46',
            'thumbnail': 'https://replay-assets.rtl.lu/2022/01/26/screenshot_20220126104933_3274749_12b249833469b0d6e4440a1dec83cdfa.jpg',
        },
    }, {
        # today.lu
        'url': 'https://today.rtl.lu/entertainment/news/a/1936203.html',
        'skip': 'video gone',
        'info_dict': {
            'id': '1936203',
            'ext': 'mp4',
            'title': 'Once Upon A Time...zu Lëtzebuerg: The Three Witches\' Tower',
            'description': 'The witchy theme continues in the latest episode of Once Upon A Time...',
            'thumbnail': 'https://replay-assets.rtl.lu/2022/07/02/screenshot_20220702122859_3290019_412dc5185951b7f6545a4039c8be9235.jpg',
        },
    }]


class RTLLuLiveIE(RTLLuBaseIE):
    _VALID_URL = r'https?://www\.rtl\.lu/(?:tele|radio)/(?P<id>live(?:-\d+)?|lauschteren)'
    _TESTS = [{
        # Tele:live
        'url': 'https://www.rtl.lu/tele/live',
        'skip': 'video gone',
        'info_dict': {
            'id': 'live',
            'ext': 'mp4',
            'live_status': 'is_live',
            'title': r're:RTL - Télé LIVE \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
            'thumbnail': 'https://static.rtl.lu/livestream/channel1.jpg',
        },
    }, {
        # Tele:live-2
        'url': 'https://www.rtl.lu/tele/live-2',
        'skip': 'video gone',
        'info_dict': {
            'id': 'live-2',
            'ext': 'mp4',
            'live_status': 'is_live',
            'title': r're:RTL - Télé LIVE \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
            'thumbnail': 'https://static.rtl.lu/livestream/channel2.jpg',
        },
    }, {
        # Radio:lauschteren
        'url': 'https://www.rtl.lu/radio/lauschteren',
        'skip': 'video gone',
        'info_dict': {
            'id': 'lauschteren',
            'ext': 'mp4',
            'live_status': 'is_live',
            'title': r're:RTL - Radio LIVE \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
            'thumbnail': 'https://static.rtl.lu/livestream/rtlradiowebtv.jpg',
        },
    }]


class RTLLuRadioIE(RTLLuBaseIE):
    _VALID_URL = r'https?://www\.rtl\.lu/radio/(?:[\w-]+)/s/(?P<id>\d+)(\.html)?'
    _TESTS = [{
        'url': 'https://www.rtl.lu/radio/5-vir-12/s/4033058.html',
        'skip': 'video gone',
        'info_dict': {
            'id': '4033058',
            'ext': 'mp3',
            'description': 'md5:f855a4f3e3235393ae47ed1db5d934b9',
            'title': '5 vir 12 - Stau um Stau',
            'thumbnail': 'https://static.rtl.lu/rtlg//2022/06/24/c9c19e5694a14be46a3647a3760e1f62.jpg',
        },
    }]
