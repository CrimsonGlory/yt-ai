from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
    traverse_obj,
    try_get,
    url_or_none,
    urljoin,
)


class TVPlayIE(InfoExtractor):
    IE_NAME = 'mtg'
    IE_DESC = 'MTG services'
    _VALID_URL = r'''(?x)
                    (?:
                        mtg:|
                        https?://
                            (?:www\.)?
                            (?:
                                tvplay(?:\.skaties)?\.lv(?:/parraides)?|
                                (?:tv3play|play\.tv3)\.lt(?:/programos)?|
                                tv3play(?:\.tv3)?\.ee/sisu
                            )
                            /(?:[^/]+/)+
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [
        {
            'url': 'http://www.tvplay.lv/parraides/fiba-horvatija---latvija-speles-apskats/12265110',
            'md5': 'e6fbb9a80f1c9ab2f56d53413f8637b4',
            'info_dict': {
                'id': '12265110',
                'ext': 'mp4',
                'title': 'FIBA. Horvātija - Latvija. Spēles apskats',
                'duration': 199,
                'timestamp': 1787861069,
                'upload_date': '20260827',
                'series': 'FIBA Pasaules kauss',
                'season': 'FIBA Pasaules kausa kvalifikācija',
                'season_number': 2026,
                'release_year': 2026,
                'thumbnail': r're:https://static3\.go3\.tv/.+',
            },
            'params': {
                'format': 'preview',
            },
        },
        {
            'url': 'http://www.tvplay.lv/parraides/vinas-melo-labak/418113?autostart=true',
            'skip': 'Old MTG playapi.mtgx.tv shut down',
            'info_dict': {
                'id': '418113',
                'ext': 'mp4',
                'title': 'Kādi ir īri? - Viņas melo labāk',
            },
        },
        {
            'url': 'http://play.tv3.lt/programos/moterys-meluoja-geriau/409229?autostart=true',
            'skip': 'Old MTG playapi.mtgx.tv shut down',
            'info_dict': {
                'id': '409229',
                'ext': 'flv',
                'title': 'Moterys meluoja geriau',
            },
        },
        {
            'url': 'http://www.tv3play.ee/sisu/kodu-keset-linna/238551?autostart=true',
            'skip': 'Old MTG playapi.mtgx.tv shut down',
            'info_dict': {
                'id': '238551',
                'ext': 'flv',
                'title': 'Kodu keset linna 398537',
            },
        },
        {
            'url': 'http://tvplay.skaties.lv/parraides/vinas-melo-labak/418113?autostart=true',
            'only_matching': True,
        },
        {
            'url': 'https://tvplay.skaties.lv/vinas-melo-labak/418113/?autostart=true',
            'only_matching': True,
        },
        {
            # views is null
            'url': 'http://tvplay.skaties.lv/parraides/tv3-zinas/760183',
            'only_matching': True,
        },
        {
            'url': 'http://tv3play.tv3.ee/sisu/kodu-keset-linna/238551?autostart=true',
            'only_matching': True,
        },
        {
            'url': 'mtg:418113',
            'only_matching': True,
        },
    ]

    def _extract_go3_vod(self, video_id, country, is_live=False):
        # play.tv3.lv is behind a Cloudflare managed challenge; the shared
        # frontend API on play.tv3.lt serves the same catalog per tenant.
        country = (country or 'lv').upper()
        tenant = f'AVOD_{country}'
        api_base = 'https://play.tv3.lt'
        api_path = 'lives/programmes' if is_live else 'vods'
        data = self._download_json(
            f'{api_base}/api/products/{api_path}/{video_id}', video_id,
            query={'platform': 'BROWSER', 'lang': country, 'tenant': tenant})

        if traverse_obj(data, 'loginRequired'):
            self.raise_login_required()

        video_type = 'CATCHUP' if is_live else 'MOVIE'
        stream_id = data.get('programRecordingId') if is_live else video_id
        stream = self._download_json(
            f'{api_base}/api/products/{stream_id}/videos/playlist', video_id,
            query={
                'videoType': video_type,
                'platform': 'BROWSER',
                'lang': country,
                'tenant': tenant,
            })

        def _abs_url(value):
            if not value:
                return value
            if value.startswith('//'):
                return 'https:' + value
            return urljoin('https://play.tv3.lt/', value)

        formats, subtitles = [], {}
        hls = traverse_obj(stream, ('sources', 'HLS', 0, 'src'), expected_type=url_or_none)
        if hls:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                _abs_url(hls), video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False)
            # Master playlists omit EXT-X-KEY; FairPlay is only on variants.
            if stream.get('drm'):
                for fmt in fmts:
                    fmt['has_drm'] = True
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        # Full streams are FairPlay/Widevine; public clips still publish a
        # clear preview MP4 next to preview.json.
        preview = traverse_obj(data, 'previewUrl', expected_type=url_or_none)
        if preview:
            preview = _abs_url(preview)
            if preview.endswith('preview.json'):
                preview = preview[:-len('preview.json')] + 'preview.mp4'
            formats.append({
                'url': preview,
                'ext': 'mp4',
                'format_id': 'preview',
                'format_note': 'preview',
                'quality': -10,
            })

        if not formats:
            if data.get('geolocked'):
                self.raise_geo_restricted(countries=[country], metadata_available=True)
            if stream.get('drm'):
                self.report_drm(video_id)
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        thumbnails = [{
            'url': _abs_url(thumb_url),
            'ext': 'jpg',
        } for thumb_url in set(traverse_obj(
            data, (('gallery', 'galary', 'images', 'artworks'), ..., ..., ('miniUrl', 'mainUrl')),
            expected_type=url_or_none) or [])]

        def _clean(value):
            return value.strip() if isinstance(value, str) else value

        return {
            'id': str(video_id),
            'title': _clean(data.get('title')),
            'description': _clean(traverse_obj(data, 'description', 'lead')),
            'duration': int_or_none(data.get('duration')),
            'timestamp': parse_iso8601(data.get('since')),
            'series': _clean(traverse_obj(data, ('parentProduct', 'serial', 'title'), ('season', 'serial', 'title'))),
            'season': _clean(traverse_obj(data, ('parentProduct', 'title'), ('season', 'title'))),
            'season_number': int_or_none(traverse_obj(
                data, ('parentProduct', 'number'), ('season', 'number'))),
            'episode': data.get('title') if data.get('type_') == 'EPISODE' else None,
            'episode_number': int_or_none(data.get('episode')),
            'release_year': int_or_none(traverse_obj(
                data, 'year', ('parentProduct', 'serial', 'year'), ('season', 'serial', 'year'))),
            'thumbnails': thumbnails or None,
            'formats': formats,
            'subtitles': subtitles,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        country = (self._search_regex(
            r'https?://[^/]+\.([a-z]{2})', url,
            'geo country', default='lv') or 'lv').upper()
        self._initialize_geo_bypass({'countries': [country]})
        return self._extract_go3_vod(video_id, country)


class TVPlayHomeIE(InfoExtractor):
    _VALID_URL = r'''(?x)
            https?://
            (?:tv3?)?
            play\.(?:tv3|skaties)\.(?P<country>lv|lt|ee)/
            (?P<live>lives/)?
            [^?#&]+(?:episode|programme|clip)-(?P<id>\d+)
    '''
    _TESTS = [{
        'url': 'https://play.tv3.lt/series/gauju-karai-karveliai,serial-2343791/serija-8,episode-2343828',
        'skip': 'video gone',
        'info_dict': {
            'id': '2343828',
            'ext': 'mp4',
            'title': 'Gaujų karai. Karveliai (2021) | S01E08: Serija 8',
            'description': 'md5:f6fcfbb236429f05531131640dfa7c81',
            'duration': 2710,
            'season': 'Gaujų karai. Karveliai',
            'season_number': 1,
            'release_year': 2021,
            'episode': 'Serija 8',
            'episode_number': 8,
        },
        'params': {
            'skip_download': 'm3u8',
        },
    }, {
        'url': 'https://play.tv3.lt/series/moterys-meluoja-geriau-n-7,serial-2574652/serija-25,episode-3284937',
        'info_dict': {
            'id': '3284937',
            'ext': 'mp4',
            'season': 'Moterys meluoja geriau [N-7]',
            'season_number': 14,
            'release_year': 2021,
            'episode': 'Serija 25',
            'episode_number': 25,
            'title': 'Moterys meluoja geriau [N-7] (2021) | S14|E25: Serija 25',
            'description': 'md5:c6926e9710f1a126f028fbe121eddb79',
            'duration': 2440,
        },
        'skip': '404',
    }, {
        'url': 'https://play.tv3.lt/lives/tv6-lt,live-2838694/optibet-a-lygos-rungtynes-marijampoles-suduva--vilniaus-riteriai,programme-3422014',
        'only_matching': True,
    }, {
        'url': 'https://tv3play.skaties.lv/series/women-lie-better-lv,serial-1024464/women-lie-better-lv,episode-1038762',
        'only_matching': True,
    }, {
        'url': 'https://play.tv3.ee/series/_,serial-2654462/_,episode-2654474',
        'only_matching': True,
    }, {
        'url': 'https://tv3play.skaties.lv/clips/tv3-zinas-valsti-lidz-15novembrim-bus-majsede,clip-3464509',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        country, is_live, video_id = self._match_valid_url(url).groups()

        api_path = 'lives/programmes' if is_live else 'vods'
        data = self._download_json(
            urljoin(url, f'/api/products/{api_path}/{video_id}?platform=BROWSER&lang={country.upper()}'),
            video_id)

        video_type = 'CATCHUP' if is_live else 'MOVIE'
        stream_id = data['programRecordingId'] if is_live else video_id
        stream = self._download_json(
            urljoin(url, f'/api/products/{stream_id}/videos/playlist?videoType={video_type}&platform=BROWSER'), video_id)
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            stream['sources']['HLS'][0]['src'], video_id, 'mp4', 'm3u8_native', m3u8_id='hls')

        thumbnails = set(traverse_obj(
            data, (('galary', 'images', 'artworks'), ..., ..., ('miniUrl', 'mainUrl')), expected_type=url_or_none))

        return {
            'id': video_id,
            'title': self._resolve_title(data),
            'description': traverse_obj(data, 'description', 'lead'),
            'duration': int_or_none(data.get('duration')),
            'season': traverse_obj(data, ('season', 'serial', 'title')),
            'season_number': int_or_none(traverse_obj(data, ('season', 'number'))),
            'episode': data.get('title'),
            'episode_number': int_or_none(data.get('episode')),
            'release_year': int_or_none(traverse_obj(data, ('season', 'serial', 'year'))),
            'thumbnails': [{'url': url, 'ext': 'jpg'} for url in thumbnails],
            'formats': formats,
            'subtitles': subtitles,
        }

    @staticmethod
    def _resolve_title(data):
        return try_get(data, lambda x: (
            f'{data["season"]["serial"]["title"]} ({data["season"]["serial"]["year"]}) | '
            f'S{data["season"]["number"]:02d}E{data["episode"]:02d}: {data["title"]}'
        )) or data.get('title')
