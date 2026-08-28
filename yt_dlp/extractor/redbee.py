import json
import time
import urllib.parse
import uuid

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    traverse_obj,
    try_call,
    unified_timestamp,
    url_or_none,
)


class RedBeeBaseIE(InfoExtractor):
    _DEVICE_ID = str(uuid.uuid4())

    @property
    def _API_URL(self):
        """
        Ref: https://apidocs.emp.ebsd.ericsson.net
        Subclasses must set _REDBEE_CUSTOMER, _REDBEE_BUSINESS_UNIT
        """
        return f'https://exposure.api.redbee.live/v2/customer/{self._REDBEE_CUSTOMER}/businessunit/{self._REDBEE_BUSINESS_UNIT}'

    def _get_bearer_token(self, asset_id, jwt=None):
        request = {
            'deviceId': self._DEVICE_ID,
            'device': {
                'deviceId': self._DEVICE_ID,
                'name': 'Mozilla Firefox 102',
                'type': 'WEB',
            },
        }
        if jwt:
            request['jwt'] = jwt

        return self._download_json(
            f'{self._API_URL}/auth/{"gigyaLogin" if jwt else "anonymous"}',
            asset_id, data=json.dumps(request).encode(), headers={
                'Content-Type': 'application/json;charset=utf-8',
            })['sessionToken']

    def _get_formats_and_subtitles(self, asset_id, **kwargs):
        bearer_token = self._get_bearer_token(asset_id, **kwargs)
        api_response = self._download_json(
            f'{self._API_URL}/entitlement/{asset_id}/play',
            asset_id, headers={
                'Authorization': f'Bearer {bearer_token}',
                'Accept': 'application/json, text/plain, */*',
            })

        formats, subtitles = [], {}
        for format_data in api_response['formats']:
            if not format_data.get('mediaLocator'):
                continue

            fmts, subs = [], {}
            if format_data.get('format') == 'DASH':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    format_data['mediaLocator'], asset_id, fatal=False)
            elif format_data.get('format') == 'SMOOTHSTREAMING':
                fmts, subs = self._extract_ism_formats_and_subtitles(
                    format_data['mediaLocator'], asset_id, fatal=False)
            elif format_data.get('format') == 'HLS':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    format_data['mediaLocator'], asset_id, fatal=False)

            if format_data.get('drm'):
                for f in fmts:
                    f['has_drm'] = True

            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return formats, subtitles


class ParliamentLiveUKIE(RedBeeBaseIE):
    IE_NAME = 'parliamentlive.tv'
    IE_DESC = 'UK parliament videos'
    _VALID_URL = r'(?i)https?://(?:www\.)?parliamentlive\.tv/Event/Index/(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'

    _REDBEE_CUSTOMER = 'UKParliament'
    _REDBEE_BUSINESS_UNIT = 'ParliamentLive'

    _TESTS = [{
        'url': 'http://parliamentlive.tv/Event/Index/c1e9d44d-fd6c-4263-b50f-97ed26cc998b',
        'info_dict': {
            'id': 'c1e9d44d-fd6c-4263-b50f-97ed26cc998b',
            'ext': 'mp4',
            'title': 'Home Affairs Committee',
            'timestamp': 1395153872,
            'upload_date': '20140318',
            'thumbnail': r're:https?://[^?#]+c1e9d44d-fd6c-4263-b50f-97ed26cc998b[^/]*/thumbnail',
        },
    }, {
        'url': 'http://parliamentlive.tv/event/index/3f24936f-130f-40bf-9a5d-b3d6479da6a4',
        'only_matching': True,
    }, {
        'url': 'https://parliamentlive.tv/Event/Index/27cf25e4-e77b-42a3-93c5-c815cd6d7377',
        'info_dict': {
            'id': '27cf25e4-e77b-42a3-93c5-c815cd6d7377',
            'ext': 'mp4',
            'title': 'House of Commons',
            'timestamp': 1658392447,
            'upload_date': '20220721',
            'thumbnail': r're:https?://[^?#]+27cf25e4-e77b-42a3-93c5-c815cd6d7377[^/]*/thumbnail',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        formats, subtitles = self._get_formats_and_subtitles(video_id)

        video_info = self._download_json(
            f'https://www.parliamentlive.tv/Event/GetShareVideo/{video_id}', video_id, fatal=False)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': traverse_obj(video_info, ('event', 'title')),
            'thumbnail': traverse_obj(video_info, 'thumbnailUrl'),
            'timestamp': traverse_obj(
                video_info, ('event', 'publishedStartTime'), expected_type=unified_timestamp),
            '_format_sort_fields': ('res', 'proto'),
        }


class RTBFIE(RedBeeBaseIE):
    _WEB_FALLBACK = True
    _VALID_URL = r'''(?x)
        https?://(?:
            (?:www\.)?rtbf\.be/(?:
                video/[^?]+\?.*\bid=|
                ouftivi/(?:[^/]+/)*[^?]+\?.*\bvideoId=|
                auvio/(?:embed/(?:direct|media)\?.*\bid=|[^/?#]+\?.*\b(?P<live>l)?id=)
            )|
            auvio\.rtbf\.be/(?:
                (?P<live_path>live)/[^/?#]+-|
                media/[^/?#]+-|
                embed/generic/content/(?:media|live)/
            )
        )(?P<id>\d+)'''
    _NETRC_MACHINE = 'rtbf'

    _REDBEE_CUSTOMER = 'RTBF'
    _REDBEE_BUSINESS_UNIT = 'Auvio'
    _BFF_API = 'https://bff-service.rtbf.be/auvio/v1.23'
    _BFF_USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    _TESTS = [{
        'url': 'https://auvio.rtbf.be/media/derniere-game-derniere-game-3507961',
        'md5': '4cbb5137e4af165cab54546f00a4176e',
        'file_minsize': None,
        'info_dict': {
            'id': '3507961',
            'ext': 'mp4',
            'title': "Le plus grand scandale de l'histoire de Minecraft",
            'description': 'md5:525235fc54db59f2eda904b68dad2a00',
            'duration': 1729,
            'timestamp': 1787844600,
            'upload_date': '20260827',
            'series': 'Dernière Game',
            'thumbnail': r're:https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.rtbf.be/video/detail_les-diables-au-coeur-episode-2?id=1921274',
        'md5': '8c876a1cceeb6cf31b476461ade72384',
        'info_dict': {
            'id': '1921274',
            'ext': 'mp4',
            'title': 'Les Diables au coeur (épisode 2)',
            'description': '(du 25/04/2014)',
            'duration': 3099.54,
            'upload_date': '20140425',
            'timestamp': 1398456300,
        },
        'skip': 'No longer available',
    }, {
        # geo restricted
        'url': 'http://www.rtbf.be/ouftivi/heros/detail_scooby-doo-mysteres-associes?id=1097&videoId=2057442',
        'only_matching': True,
    }, {
        'url': 'http://www.rtbf.be/ouftivi/niouzz?videoId=2055858',
        'only_matching': True,
    }, {
        'url': 'http://www.rtbf.be/auvio/detail_jeudi-en-prime-siegfried-bracke?id=2102996',
        'only_matching': True,
    }, {
        # Live
        'url': 'https://www.rtbf.be/auvio/direct_pure-fm?lid=134775',
        'only_matching': True,
    }, {
        # Audio
        'url': 'https://www.rtbf.be/auvio/detail_cinq-heures-cinema?id=2360811',
        'only_matching': True,
    }, {
        # With Subtitle
        'url': 'https://www.rtbf.be/auvio/detail_les-carnets-du-bourlingueur?id=2361588',
        'only_matching': True,
    }, {
        'url': 'https://www.rtbf.be/auvio/detail_investigation?id=2921926',
        'info_dict': {
            'id': '2921926',
            'ext': 'mp4',
            'title': 'Le handicap un confinement perpétuel - Maladie de Lyme',
        },
        'skip': 'Requires login',
    }, {
        'url': 'https://www.rtbf.be/auvio/detail_la-belgique-criminelle?id=2920492',
        'info_dict': {
            'id': '2920492',
            'ext': 'mp4',
            'title': '04 - Le crime de la rue Royale',
        },
        'skip': 'video gone',
    }, {
        'url': 'https://auvio.rtbf.be/live/motogp-essais-libres-grand-prix-aragon-745002',
        'only_matching': True,
    }, {
        'url': 'https://auvio.rtbf.be/embed/generic/content/media/3507961',
        'only_matching': True,
    }]

    _LOGIN_URL = 'https://login.rtbf.be/accounts.login'
    _GIGYA_API_KEY = '3_kWKuPgcdAybqnqxq_MvHVk0-6PN8Zk8pIIkJM_yXOu-qLPDDsGOtIDFfpGivtbeO'
    _LOGIN_COOKIE_ID = f'glt_{_GIGYA_API_KEY}'

    def _perform_login(self, username, password):
        if self._get_cookies(self._LOGIN_URL).get(self._LOGIN_COOKIE_ID):
            return

        self._set_cookie('.rtbf.be', 'gmid', 'gmid.ver4', secure=True, expire_time=time.time() + 3600)

        login_response = self._download_json(
            self._LOGIN_URL, None, data=urllib.parse.urlencode({
                'loginID': username,
                'password': password,
                'APIKey': self._GIGYA_API_KEY,
                'targetEnv': 'jssdk',
                'sessionExpiration': '-2',
            }).encode(), headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            })

        if login_response['statusCode'] != 200:
            raise ExtractorError('Login failed. Server message: {}'.format(login_response['errorMessage']), expected=True)

        self._set_cookie('.rtbf.be', self._LOGIN_COOKIE_ID, login_response['sessionInfo']['login_token'],
                         secure=True, expire_time=time.time() + 3600)

    def _get_gigya_jwt(self, url, media_id):
        login_token = self._get_cookies(url).get(self._LOGIN_COOKIE_ID)
        if not login_token:
            return None
        return try_call(lambda: self._get_cookies(url)['rtbf_jwt'].value) or self._download_json(
            'https://login.rtbf.be/accounts.getJWT', media_id, query={
                'login_token': login_token.value,
                'APIKey': self._GIGYA_API_KEY,
                'sdk': 'js_latest',
                'authMode': 'cookie',
                'pageURL': url,
                'sdkBuild': '13273',
                'format': 'json',
            })['id_token']

    def _get_formats_and_subtitles(self, asset_id, url=None, geo_countries=None):
        try:
            return super()._get_formats_and_subtitles(asset_id)
        except ExtractorError as e:
            if not isinstance(getattr(e, 'cause', None), HTTPError) or e.cause.status not in (401, 403):
                raise

        jwt = self._get_gigya_jwt(url or 'https://www.rtbf.be/', asset_id)
        if jwt:
            try:
                return super()._get_formats_and_subtitles(asset_id, jwt=jwt)
            except ExtractorError as e:
                if geo_countries and isinstance(getattr(e, 'cause', None), HTTPError) and e.cause.status == 403:
                    self.raise_geo_restricted(countries=geo_countries)
                raise

        if geo_countries:
            self.raise_geo_restricted(countries=geo_countries)
        self.raise_login_required()

    def _download_bff_embed(self, media_id, is_live):
        resources = ('live', 'media') if is_live else ('media', 'live')
        for resource in resources:
            info = self._download_json(
                f'{self._BFF_API}/embed/{resource}/{media_id}',
                media_id, query={'userAgent': self._BFF_USER_AGENT},
                fatal=False, expected_status=(400, 404, 410))
            content = traverse_obj(info, ('data', {dict}))
            if content:
                return content, resource == 'live'
        raise ExtractorError('Could not find media data', expected=True)

    def _real_extract(self, url):
        urlm = self._match_valid_url(url)
        media_id = urlm.group('id')
        is_live = bool(urlm.group('live') or urlm.group('live_path'))

        data, is_live = self._download_bff_embed(media_id, is_live)
        is_live = is_live or data.get('playerType') == 'LIVE' or bool(data.get('isLive'))
        asset_id = data.get('assetId') or (f'live_{media_id}' if is_live else media_id)
        geo_countries = ['BE'] if traverse_obj(data, ('geoloc', 'key')) == 'be' else None

        formats, subtitles = self._get_formats_and_subtitles(
            asset_id, url, geo_countries=geo_countries)

        subtitle = strip_or_none(data.get('subtitle'))
        title = subtitle or strip_or_none(data.get('title'))
        return {
            'id': media_id,
            'formats': formats,
            'title': title,
            'description': strip_or_none(data.get('description')),
            'thumbnail': traverse_obj(data, ('background', 'xl', {url_or_none}), ('illustration', 'xl', {url_or_none})),
            'duration': int_or_none(data.get('duration')),
            'timestamp': parse_iso8601(data.get('publishedFrom') or data.get('scheduledFrom')),
            'series': strip_or_none(data.get('title')) if subtitle else None,
            'subtitles': subtitles,
            'is_live': is_live,
            '_format_sort_fields': ('res', 'proto'),
        }
