import json

from .common import InfoExtractor
from ..utils import ExtractorError, int_or_none, traverse_obj, url_or_none


class AmazonMiniTVBaseIE(InfoExtractor):
    def _real_initialize(self):
        self._download_webpage(
            'https://www.amazon.in/minitv', None,
            note='Fetching guest session cookies')
        AmazonMiniTVBaseIE.session_id = self._get_cookies('https://www.amazon.in')['session-id'].value

    def _call_api(self, asin, data=None, note=None):
        device = {'clientId': 'ATVIN', 'deviceLocale': 'en_GB'}
        if data:
            data['variables'].update({
                'contentType': 'VOD',
                'sessionIdToken': self.session_id,
                **device,
            })

        resp = self._download_json(
            f'https://www.amazon.in/minitv/api/web/{"graphql" if data else "prs"}',
            asin, note=note, headers={
                'Content-Type': 'application/json',
                'currentpageurl': '/',
                'currentplatform': 'dWeb',
            }, data=json.dumps(data).encode() if data else None,
            query=None if data else {
                'deviceType': 'A1WMMUXPCUJL4N',
                'contentId': asin,
                **device,
            })

        if resp.get('errors'):
            raise ExtractorError(f'MiniTV said: {resp["errors"][0]["message"]}')
        elif not data:
            return resp
        return resp['data'][data['operationName']]


class AmazonMiniTVIE(AmazonMiniTVBaseIE):
    _VALID_URL = r'(?:https?://(?:www\.)?amazon\.in/minitv/tp/(?:[^/?#]+/)*|amazonminitv:(?:amzn1\.dv\.gti\.)?)(?P<id>[a-f0-9-]+)'
    _TESTS = [{
        'url': 'https://www.amazon.in/minitv/tp/7e03b04f-057c-4d83-b9d5-21ad7461f8f7',
        'md5': '09a4c38c2ce3941d202d2027bd30e7bf',
        'info_dict': {
            'id': 'amzn1.dv.gti.7e03b04f-057c-4d83-b9d5-21ad7461f8f7',
            'ext': 'mp4',
            'title': 'Crossroads',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)',
            'description': 'md5:dca5a6b396a6ce22ef2615d0768b3e65',
            'release_timestamp': 1762300800,
            'release_date': '20251105',
            'duration': 1512,
            'chapters': 'count:4',
            'series': 'First Copy',
            'series_id': 'amzn1.dv.gti.658460dc-db1f-445b-b7f2-1e392db11ccd',
            'season': 'First Copy - Season 2',
            'season_number': 2,
            'season_id': 'amzn1.dv.gti.b1bd236d-5964-4c06-9fe4-e4696957e0d6',
            'episode': 'Crossroads',
            'episode_number': 1,
            'episode_id': 'amzn1.dv.gti.7e03b04f-057c-4d83-b9d5-21ad7461f8f7',
            'cast': ['Munawar Faruqui', 'Ashi Singh', 'Saqib Ayub', 'Raza Murad', 'Saanand Verma', 'Mast Ali', 'Gulshan Grover'],
            'genres': ['Drama', 'Romance', 'Comedy'],
        },
        # DASH --test only fetches the init fragment (~1KB), below the default 10KB check
        'file_minsize': None,
        'params': {
            'format': 'bestvideo[ext=mp4]/best[ext=mp4]/best',
        },
    }, {
        'url': 'https://www.amazon.in/minitv/tp/75fe3a75-b8fe-4499-8100-5c9424344840?referrer=https%3A%2F%2Fwww.amazon.in%2Fminitv',
        'skip': 'video gone',
        'info_dict': {
            'id': 'amzn1.dv.gti.75fe3a75-b8fe-4499-8100-5c9424344840',
            'ext': 'mp4',
            'title': 'May I Kiss You?',
            'language': 'Hindi',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)$',
            'description': 'md5:a549bfc747973e04feb707833474e59d',
            'release_timestamp': 1644710400,
            'release_date': '20220213',
            'duration': 846,
            'chapters': 'count:2',
            'series': 'Couple Goals',
            'series_id': 'amzn1.dv.gti.56521d46-b040-4fd5-872e-3e70476a04b0',
            'season': 'Season 3',
            'season_number': 3,
            'season_id': 'amzn1.dv.gti.20331016-d9b9-4968-b991-c89fa4927a36',
            'episode': 'May I Kiss You?',
            'episode_number': 2,
            'episode_id': 'amzn1.dv.gti.75fe3a75-b8fe-4499-8100-5c9424344840',
        },
    }, {
        'url': 'https://www.amazon.in/minitv/tp/280d2564-584f-452f-9c98-7baf906e01ab?referrer=https%3A%2F%2Fwww.amazon.in%2Fminitv',
        'skip': 'video gone',
        'info_dict': {
            'id': 'amzn1.dv.gti.280d2564-584f-452f-9c98-7baf906e01ab',
            'ext': 'mp4',
            'title': 'Jahaan',
            'language': 'Hindi',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)',
            'description': 'md5:05eb765a77bf703f322f120ec6867339',
            'release_timestamp': 1647475200,
            'release_date': '20220317',
            'duration': 783,
            'chapters': [],
        },
    }, {
        'url': 'https://www.amazon.in/minitv/tp/280d2564-584f-452f-9c98-7baf906e01ab',
        'only_matching': True,
    }, {
        'url': 'https://www.amazon.in/minitv/tp/web-series/first-copy-season-2/episode-1/7e03b04f-057c-4d83-b9d5-21ad7461f8f7',
        'only_matching': True,
    }, {
        'url': 'amazonminitv:amzn1.dv.gti.280d2564-584f-452f-9c98-7baf906e01ab',
        'only_matching': True,
    }, {
        'url': 'amazonminitv:280d2564-584f-452f-9c98-7baf906e01ab',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            f'https://www.amazon.in/minitv/tp/{video_id}', video_id)
        next_data = self._search_nextjs_data(webpage, video_id)
        page_data = traverse_obj(
            next_data, ('props', 'pageProps', 'ssrProps', 'pageLayoutData')) or {}

        widgets = {
            widget.get('type'): widget.get('data') or {}
            for widget in page_data.get('widgets') or []
        }
        player_data = widgets.get('PLAYER') or {}
        playback_assets = player_data.get('playbackAssets') or {}
        player_content = player_data.get('contentDetails') or {}
        meta = traverse_obj(page_data, ('metaData', 'contentDetails')) or {}

        formats, subtitles = [], {}
        seen_manifests = set()

        def add_dash(manifest_url, codec=None):
            manifest_url = url_or_none(manifest_url)
            if not manifest_url or manifest_url in seen_manifests:
                return
            seen_manifests.add(manifest_url)
            mpd_id = 'dash' if not codec else f'dash-{codec.lower()}'
            mpd_fmts, mpd_subs = self._extract_mpd_formats_and_subtitles(
                manifest_url, video_id, mpd_id=mpd_id, fatal=False)
            formats.extend(mpd_fmts)
            self._merge_subtitles(mpd_subs, target=subtitles)

        add_dash(playback_assets.get('manifestURL'))
        for asset in traverse_obj(playback_assets, ('manifestData', lambda _, v: v['manifestURL'])):
            add_dash(asset.get('manifestURL'), asset.get('codec'))

        if not formats:
            geo_msg = traverse_obj(next_data, (
                'props', 'pageProps', 'additionalProps', 'appContextProps',
                'error', 'networkError', 'result', 'message'))
            if geo_msg:
                self.raise_geo_restricted(geo_msg, countries=['IN'])
            raise ExtractorError(
                'Unable to find video data in page; the title may be unavailable',
                expected=True)

        chapters = sorted(({
            'start_time': int_or_none(elem.get('start')),
            'end_time': int_or_none(elem.get('end')),
            'title': (elem.get('elementType') or '').replace('_', ' ').title() or None,
        } for elem in player_content.get('transitionElements') or []),
            key=lambda c: c['start_time'] if c['start_time'] is not None else -1)

        is_episode = meta.get('vodType') == 'EPISODE'
        content_id = meta.get('contentId') or f'amzn1.dv.gti.{video_id}'

        return {
            'id': content_id,
            'title': meta.get('name') or player_content.get('name'),
            'formats': formats,
            'subtitles': subtitles,
            'language': traverse_obj(player_content, ('audioTracks', 0)),
            'thumbnail': url_or_none(meta.get('imageSrc')),
            'description': meta.get('synopsis'),
            'release_timestamp': int_or_none(meta.get('publicReleaseDateUTC'), scale=1000),
            'duration': int_or_none(
                meta.get('contentLengthInSeconds')
                or player_content.get('contentLengthInSeconds')),
            'chapters': chapters,
            'series': meta.get('seriesName') or player_content.get('seriesName'),
            'series_id': player_content.get('seriesId'),
            'season': meta.get('seasonName') or player_content.get('seasonName'),
            'season_number': int_or_none(meta.get('seasonNumber') or player_content.get('seasonNumber')),
            'season_id': player_content.get('seasonId'),
            'episode': (meta.get('name') or player_content.get('name')) if is_episode else None,
            'episode_number': int_or_none(meta.get('episodeNumber') or player_content.get('episodeNumber')),
            'episode_id': content_id if is_episode else None,
            'cast': meta.get('starringCast'),
            'genres': meta.get('genres'),
        }


class AmazonMiniTVSeasonIE(AmazonMiniTVBaseIE):
    IE_NAME = 'amazonminitv:season'
    _VALID_URL = r'amazonminitv:season:(?:amzn1\.dv\.gti\.)?(?P<id>[a-f0-9-]+)'
    IE_DESC = 'Amazon MiniTV Season, "minitv:season:" prefix'
    _TESTS = [{
        'url': 'amazonminitv:season:amzn1.dv.gti.0aa996eb-6a1b-4886-a342-387fbd2f1db0',
        'skip': 'requires account',
        'playlist_mincount': 6,
        'info_dict': {
            'id': 'amzn1.dv.gti.0aa996eb-6a1b-4886-a342-387fbd2f1db0',
        },
    }, {
        'url': 'amazonminitv:season:0aa996eb-6a1b-4886-a342-387fbd2f1db0',
        'only_matching': True,
    }]

    _GRAPHQL_QUERY = '''
query getEpisodes($sessionIdToken: String!, $clientId: String, $episodeOrSeasonId: ID!, $deviceLocale: String) {
  getEpisodes(
    applicationContextInput: {sessionIdToken: $sessionIdToken, deviceLocale: $deviceLocale, clientId: $clientId}
    episodeOrSeasonId: $episodeOrSeasonId
  ) {
    episodes {
      ... on Episode {
        contentId
        name
        images
        seriesName
        seasonId
        seriesId
        seasonNumber
        episodeNumber
        description {
          synopsis
          contentLengthInSeconds
        }
        publicReleaseDateUTC
      }
    }
  }
}
'''

    def _entries(self, asin):
        season_info = self._call_api(
            asin, note='Downloading season info', data={
                'operationName': 'getEpisodes',
                'variables': {'episodeOrSeasonId': asin},
                'query': self._GRAPHQL_QUERY,
            })

        for episode in season_info['episodes']:
            yield self.url_result(
                f'amazonminitv:{episode["contentId"]}', AmazonMiniTVIE, episode['contentId'])

    def _real_extract(self, url):
        asin = f'amzn1.dv.gti.{self._match_id(url)}'
        return self.playlist_result(self._entries(asin), asin)


class AmazonMiniTVSeriesIE(AmazonMiniTVBaseIE):
    IE_NAME = 'amazonminitv:series'
    _VALID_URL = r'amazonminitv:series:(?:amzn1\.dv\.gti\.)?(?P<id>[a-f0-9-]+)'
    IE_DESC = 'Amazon MiniTV Series, "minitv:series:" prefix'
    _TESTS = [{
        'url': 'amazonminitv:series:amzn1.dv.gti.56521d46-b040-4fd5-872e-3e70476a04b0',
        'skip': 'requires account',
        'playlist_mincount': 3,
        'info_dict': {
            'id': 'amzn1.dv.gti.56521d46-b040-4fd5-872e-3e70476a04b0',
        },
    }, {
        'url': 'amazonminitv:series:56521d46-b040-4fd5-872e-3e70476a04b0',
        'only_matching': True,
    }]

    _GRAPHQL_QUERY = '''
query getSeasons($sessionIdToken: String!, $deviceLocale: String, $episodeOrSeasonOrSeriesId: ID!, $clientId: String) {
  getSeasons(
    applicationContextInput: {deviceLocale: $deviceLocale, sessionIdToken: $sessionIdToken, clientId: $clientId}
    episodeOrSeasonOrSeriesId: $episodeOrSeasonOrSeriesId
  ) {
    seasons {
      seasonId
    }
  }
}
'''

    def _entries(self, asin):
        season_info = self._call_api(
            asin, note='Downloading series info', data={
                'operationName': 'getSeasons',
                'variables': {'episodeOrSeasonOrSeriesId': asin},
                'query': self._GRAPHQL_QUERY,
            })

        for season in season_info['seasons']:
            yield self.url_result(f'amazonminitv:season:{season["seasonId"]}', AmazonMiniTVSeasonIE, season['seasonId'])

    def _real_extract(self, url):
        asin = f'amzn1.dv.gti.{self._match_id(url)}'
        return self.playlist_result(self._entries(asin), asin)
