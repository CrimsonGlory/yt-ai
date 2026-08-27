from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    mimetype2ext,
    parse_iso8601,
    try_get,
    url_or_none,
)


class FancodeVodIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'fancode:vod'

    _VALID_URL = r'https?://(?:www\.)?fancode\.com/(?:video/|(?:[^/?#]+/)+video-highlights/[^/?#]+-)(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'https://fancode.com/video/15043/match-preview-pbks-vs-mi',
            'md5': 'bbf25b8ecee29b9ce9daf9fd3b066a22',
            'info_dict': {
                'id': '15043',
                'ext': 'mp4',
                'title': 'Match Preview: PBKS vs MI',
                'thumbnail': r're:https?://.+\.(?:jpg|jpeg)',
                'timestamp': 1619081750,
                'view_count': int,
                'like_count': int,
                'upload_date': '20210422',
                'duration': 394,
                'tags': list,
            },
        },
        {
            'url': 'https://fancode.com/video/15043',
            'only_matching': True,
        },
        {
            'url': 'https://www.fancode.com/cricket/tour/caribbean-premier-league-2026-19804160/video-highlights/saint-lucia-kings-beat-trinbago-knight-riders-by-36-runs-match-17-222961',
            'only_matching': True,
        },
    ]

    _ACCESS_TOKEN = None
    _NETRC_MACHINE = 'fancode'

    _LOGIN_HINT = 'Use "--username refresh --password <refresh_token>" to login using a refresh token'

    headers = {
        'content-type': 'application/json',
        'origin': 'https://fancode.com',
        'referer': 'https://fancode.com',
    }

    def _perform_login(self, username, password):
        # Access tokens are shortlived, so get them using the refresh token.
        if username != 'refresh':
            self.report_warning(f'Login using username and password is not currently supported. {self._LOGIN_HINT}')

        self.report_login()
        data = (
            '''{
            "query":"mutation RefreshToken($refreshToken: String\\u0021) { refreshToken(refreshToken: $refreshToken) { accessToken }}",
            "variables":{
                "refreshToken":"%s"
            },
            "operationName":"RefreshToken"
        }'''
            % password
        )  # noqa: UP031

        token_json = self.download_gql('refresh token', data, 'Getting the Access token')
        self._ACCESS_TOKEN = try_get(token_json, lambda x: x['data']['refreshToken']['accessToken'])
        if self._ACCESS_TOKEN is None:
            self.report_warning('Failed to get Access token')
        else:
            self.headers.update({'Authorization': f'Bearer {self._ACCESS_TOKEN}'})

    def _check_login_required(self, is_available, is_premium):
        msg = None
        if is_premium and self._ACCESS_TOKEN is None:
            msg = f'This video is only available for registered users. {self._LOGIN_HINT}'
        elif not is_available and self._ACCESS_TOKEN is not None:
            msg = "This video isn't available to the current logged in account"
        if msg:
            self.raise_login_required(msg, metadata_available=True, method=None)

    def download_gql(self, variable, data, note, fatal=False, headers=headers):
        return self._download_json(
            'https://www.fancode.com/graphql', variable, data=data.encode(), note=note, headers=headers, fatal=fatal,
        )

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = (
            '''{
            "query":"query Video($id: Int\\u0021, $filter: SegmentFilter) { media(id: $id, filter: $filter) { id contentId title publishedTime totalViews totalUpvotes provider thumbnail { src } mediaSource { brightcove native youtube } source { title description posterUrl url deliveryType playerType } duration isPremium isUserEntitled tags }}",
            "variables":{
                "id":%s,
                "filter":{
                    "contentDataType":"DEFAULT"
                }
            },
            "operationName":"Video"
        }'''
            % video_id
        )  # noqa: UP031

        metadata_json = self.download_gql(video_id, data, note='Downloading metadata')

        media = try_get(metadata_json, lambda x: x['data']['media'], dict) or {}
        is_premium = media.get('isPremium')
        self._check_login_required(media.get('isUserEntitled'), is_premium)

        source = media.get('source') or {}
        stream_url = url_or_none(source.get('url'))
        media_source = media.get('mediaSource') or {}

        formats = []
        if stream_url:
            if determine_ext(stream_url) == 'm3u8' or mimetype2ext(source.get('deliveryType')) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(stream_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append(
                    {
                        'url': stream_url,
                        'ext': mimetype2ext(source.get('deliveryType')) or determine_ext(stream_url),
                    },
                )

        native = url_or_none(media_source.get('native'))
        if native and 'example.' not in native:
            formats.append(
                {
                    'url': native,
                    'ext': determine_ext(native, 'mp4'),
                    'format_id': 'http-native',
                },
            )

        if not formats:
            webpage = self._download_webpage(url, video_id, fatal=False)
            native = url_or_none(
                self._search_regex(
                    rf'{{"id":{video_id},"contentId":"{video_id}","mediaSource":{{"native":"(https?://[^"]+)"',
                    webpage or '',
                    'native video URL',
                    default=None,
                ),
            )
            if native and 'example.' not in native:
                formats.append(
                    {
                        'url': native,
                        'ext': determine_ext(native, 'mp4'),
                        'format_id': 'http-native',
                    },
                )

        if not formats:
            brightcove_video_id = media_source.get('brightcove')
            if brightcove_video_id and str(brightcove_video_id).isdigit():
                return {
                    '_type': 'url_transparent',
                    'url': f'https://players.brightcove.net/6008340455001/default_default/index.html?videoId={brightcove_video_id}',
                    'ie_key': 'BrightcoveNew',
                    'id': video_id,
                    'title': media.get('title'),
                    'like_count': media.get('totalUpvotes'),
                    'view_count': media.get('totalViews'),
                    'tags': media.get('tags'),
                    'release_timestamp': parse_iso8601(media.get('publishedTime')),
                    'availability': self._availability(needs_premium=is_premium),
                }
            raise ExtractorError('Unable to extract video URL')

        return {
            'id': video_id,
            'title': media.get('title'),
            'formats': formats,
            'thumbnail': try_get(media, lambda x: x['thumbnail']['src']),
            'timestamp': parse_iso8601(media.get('publishedTime')),
            'like_count': media.get('totalUpvotes'),
            'view_count': media.get('totalViews'),
            'tags': media.get('tags'),
            'duration': media.get('duration'),
            'availability': self._availability(needs_premium=is_premium),
        }


class FancodeLiveIE(FancodeVodIE):  # XXX: Do not subclass from concrete IE
    _WEB_FALLBACK = True
    IE_NAME = 'fancode:live'

    _VALID_URL = r'https?://(?:www\.)?fancode\.com/(?:match/|(?:[^/?#]+/)+matches/[^/?#]+-)(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'https://fancode.com/match/35328/cricket-fancode-ecs-hungary-2021-bub-vs-blb?slug=commentary',
            'info_dict': {
                'id': '35328',
                'ext': 'mp4',
                'title': 'BUB vs BLB',
                'timestamp': 1624863600,
                'is_live': True,
                'upload_date': '20210628',
            },
            'skip': 'Ended',
        },
        {
            'url': 'https://fancode.com/match/35328/',
            'only_matching': True,
        },
        {
            'url': 'https://fancode.com/match/35567?slug=scorecard',
            'only_matching': True,
        },
        {
            'url': 'https://www.fancode.com/cricket/tour/top-end-t20-series-2026-19813596/matches/bangladesh-hp-xi-vs-new-zealand-a-4248448/live-match-info',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):

        video_id = self._match_id(url)
        data = (
            '''{
            "query":"query MatchResponse($id: Int\\u0021, $isLoggedIn: Boolean\\u0021) { match: matchWithScores(id: $id) { id matchDesc mediaId videoStreamId videoStreamUrl { ...VideoSource } liveStreams { videoStreamId videoStreamUrl { ...VideoSource } contentId } name startTime streamingStatus isPremium isUserEntitled @include(if: $isLoggedIn) status metaTags bgImage { src } sport { name slug } tour { id name } squads { name shortName } liveStreams { contentId } mediaId }}fragment VideoSource on VideoSource { title description posterUrl url deliveryType playerType}",
            "variables":{
                "id":%s,
                "isLoggedIn":true
            },
            "operationName":"MatchResponse"
        }'''
            % video_id
        )  # noqa: UP031

        info_json = self.download_gql(video_id, data, 'Info json')

        match_info = try_get(info_json, lambda x: x['data']['match'])

        if match_info.get('streamingStatus') != 'STARTED':
            raise ExtractorError("The stream can't be accessed", expected=True)
        self._check_login_required(match_info.get('isUserEntitled'), True)  # all live streams are premium only

        return {
            'id': video_id,
            'title': match_info.get('name'),
            'formats': self._extract_akamai_formats(
                try_get(match_info, lambda x: x['videoStreamUrl']['url']), video_id,
            ),
            'ext': mimetype2ext(try_get(match_info, lambda x: x['videoStreamUrl']['deliveryType'])),
            'is_live': True,
            'release_timestamp': parse_iso8601(match_info.get('startTime')),
        }
