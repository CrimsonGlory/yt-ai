from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    int_or_none,
    join_nonempty,
    parse_age_limit,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AsianGamesHubIE(InfoExtractor):
    IE_DESC = 'Asian Games Hub / Asian Games TV'
    _VALID_URL = r'https?://(?:www\.)?(?:asiangameshub|asiangamestv)\.com/(?P<path>videos?/(?P<id>[^/?#]+))'
    _API_BASE = 'https://world-beach-games.api.viewlift.com'
    _SITE = 'world-beach-games'
    _API_KEY = 'WX41iaJiOw7hJW8sNbDP5JpVwmjaH6t6y3xbQUsc'
    _TESTS = [{
        'url': 'https://asiangamestv.com/videos/welcome-you-to-aichi-nagoya-1787755240131',
        'md5': '7396fce7a38b848d9c3009c111396543',
        'info_dict': {
            'id': 'cc1e5620-4dbd-44ae-bbbe-3475b89c5fdb',
            'ext': 'mp4',
            'display_id': 'welcome-you-to-aichi-nagoya-1787755240131',
            'title': 'WELCOME TO AICHI-NAGOYA | 20TH ASIAN GAMES',
            'description': 'WELCOME TO AICHI-NAGOYA | 20TH ASIAN GAMES',
            'duration': 126,
            'thumbnail': r're:https://.+\.(?:jpe?g|png)',
            'timestamp': 1787756770,
            'upload_date': '20260826',
            'categories': ['20th Asian Games Aichi-Nagoya 2026', 'Featured'],
        },
    }, {
        'url': 'https://www.asiangameshub.com/videos/welcome-you-to-aichi-nagoya-1787755240131',
        'only_matching': True,
    }, {
        'url': 'https://www.asiangameshub.com/videos/replay-ice-dance-free-dance-womens-pair-skating-short-program-figure-skating-2025-harbin-awg',
        'only_matching': True,
    }]

    def _call_api(self, api_base, path, video_id, headers, query=None, note=None):
        try:
            return self._download_json(
                f'{api_base}/{path}', video_id, note=note,
                headers={'Accept': 'application/json', **headers}, query=query)
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError):
                raise
            webpage = e.cause.response.read().decode('utf-8', 'replace')
            message = traverse_obj(self._parse_json(
                webpage, video_id, fatal=False), ('errorMessage', 'message', 'error', {str}))
            if e.cause.status == 403 or (message and 'purchased' in message.lower()):
                self.raise_login_required(message, method='cookies')
            if message:
                raise ExtractorError(message, expected=True)
            raise

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        page_data = self._search_json(
            r'window\.page_data\s*=', webpage, 'page data', display_id)
        video = traverse_obj(page_data, (
            'page', 'modules',
            lambda _, v: v.get('moduleType') == 'VideoDetailModule',
            'contentData', 0, {dict}, any))
        video_id = traverse_obj(video, ('gist', 'id', {str})) or traverse_obj(video, ('id', {str}))
        if not video_id:
            raise ExtractorError('Unable to extract video id', expected=True)

        api_base = self._search_regex(
            r'window\.apiBaseUrl\s*=\s*["\']([^"\']+)["\']',
            webpage, 'api base', default=self._API_BASE).rstrip('/')
        api_key = self._search_regex(
            r'window\.xApiKey\s*=\s*["\']([^"\']+)["\']',
            webpage, 'api key', default=self._API_KEY)
        app_data = self._search_json(
            r'window\.app_data\s*=', webpage, 'app data', display_id, fatal=False)
        site = traverse_obj(app_data, ('site', 'siteInternalName', {str})) or self._SITE

        token = self._call_api(
            api_base, 'identity/anonymous-token', video_id,
            {'x-api-key': api_key}, query={'site': site},
            note='Downloading anonymous token')['authorizationToken']
        entitlement = self._call_api(
            api_base, 'entitlement/video/status', video_id, {
                'Authorization': token,
                'x-api-key': api_key,
            }, query={'id': video_id}, note='Downloading video entitlement')
        content = traverse_obj(entitlement, ('video', {dict})) or {}
        if content.get('drmEnabled'):
            self.report_drm(video_id)
        if entitlement.get('playable') is False:
            self.raise_login_required(
                traverse_obj(entitlement, (('errorMessage', 'message'), {str}, any)),
                method='cookies')

        video_assets = traverse_obj(content, ('streamingInfo', 'videoAssets', {dict})) or {}
        formats, subtitles = [], {}
        hls_url = traverse_obj(video_assets, (('hls', ('hlsDetail', 'url')), {url_or_none}, any))
        if hls_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)

        for video_asset in traverse_obj(video_assets, ('mpeg', lambda _, v: url_or_none(v.get('url')))):
            bitrate = int_or_none(video_asset.get('bitrate'))
            height = int_or_none(self._search_regex(
                r'^_?(\d+)[pP]$', video_asset.get('renditionValue'),
                'height', default=None))
            formats.append({
                'url': video_asset['url'],
                'format_id': join_nonempty('http', height, bitrate),
                'tbr': bitrate,
                'height': height,
                'vcodec': video_asset.get('codec'),
            })

        if not formats:
            self.raise_no_formats('No video formats available', expected=True, video_id=video_id)

        for sub in traverse_obj(content, ('closedCaptions', lambda _, v: url_or_none(v.get('url')))):
            subtitles.setdefault(sub.get('language') or 'en', []).append({'url': sub['url']})

        gist = traverse_obj(content, ('gist', {dict})) or {}
        timestamp = int_or_none(content.get('publishDate') or gist.get('publishDate'))
        if timestamp and timestamp > 1_000_000_000_000:
            timestamp //= 1000

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': int_or_none(content.get('runtime') or gist.get('runtime')),
            'timestamp': timestamp,
            'age_limit': parse_age_limit(content.get('parentalRating')),
            **traverse_obj(content, {
                'title': ('title', {str}),
                'categories': ('categories', ..., 'title', {str}),
                'tags': ('tags', ..., 'title', {str}),
            }),
            **traverse_obj(gist, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': (('videoImageUrl', ('imageGist', 'r16x9')), {url_or_none}, any),
            }),
            'title': str_or_none(content.get('title')) or str_or_none(gist.get('title')) or display_id,
        }
