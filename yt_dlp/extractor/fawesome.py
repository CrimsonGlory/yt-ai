import re
import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_age_limit,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class FawesomeIE(InfoExtractor):
    IE_NAME = 'fawesome'
    IE_DESC = 'Fawesome'
    _VALID_URL = r'https?://(?:www\.)?fawesome\.tv/(?:movies|tv-shows)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://fawesome.tv/movies/10527435/calla-lily',
        'md5': '95edfd85b8468d49de2308aaf4e46ac7',
        'info_dict': {
            'id': '10527435',
            'ext': 'mp4',
            'title': 'Calla Lily',
            'description': 'md5:7a26a1754e8e81373d22b320582cc5dc',
            'duration': 4945,
            'thumbnail': r're:https://ftmain\.cachefly\.net/files/.+\.jpg',
            'creators': ['FilmHub'],
            'cast': ['Cynthia Stone', 'Rudolph Mendy'],
            'categories': ['Drama', 'Romance'],
            'age_limit': 16,
            'language': 'en',
            'timestamp': 1693440000,
            'upload_date': '20230831',
            'release_timestamp': 1451606400,
            'release_date': '20160101',
        },
    }, {
        'url': 'https://fawesome.tv/tv-shows/10598460/s01-e01-back-to-californy-the-beverly-hillbillies',
        'only_matching': True,
    }, {
        'url': 'https://www.fawesome.tv/movies/10527435/calla-lily',
        'only_matching': True,
    }]

    _API_QUERY = {
        'appId': '9',
        'siteId': '236',
        'auth-token': '1217575',  # website platform_id
        'apiEnv': 'production',
    }

    def _call_api(self, version, endpoint, video_id, device_id, query=None, headers=None, note=None):
        return self._download_json(
            f'https://fawesome.tv/home/new/{version}/api/{endpoint}', video_id,
            note=note, headers=headers, query={
                **self._API_QUERY,
                'deviceId': device_id,
                **(query or {}),
            })

    @staticmethod
    def _parse_api_timestamp(date_str, day_first=False):
        if not date_str:
            return None
        date_str = re.sub(r'\s+-.*$', '', date_str).replace('.', '').replace(',', '')
        return unified_timestamp(date_str, day_first=day_first)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        version = self._search_regex(
            r'/home/new/(v\d+)/', webpage, 'api version', default='v453')
        device_id = str(uuid.uuid4())

        token = traverse_obj(self._call_api(
            version, 'getSecurityToken.php', video_id, device_id,
            note='Downloading security token',
        ), ('securityToken', {str}))
        if not token:
            raise ExtractorError('Unable to extract security token')

        metadata = traverse_obj(self._call_api(
            version, 'recipes.php', video_id, device_id,
            query={
                'searchType': 'nodeid',
                'start-index': '0',
                'dltype': '1',
                'nid': video_id,
            },
            headers={'Token': token, 'Referer': url},
            note='Downloading video metadata',
        ), ('results', 0, {dict}, {require('video metadata')}))

        if int_or_none(metadata.get('drm')) == 1:
            self.report_drm(video_id)

        formats, subtitles = [], {}
        seen_urls = set()
        for media_url in traverse_obj(metadata, (
            ('video_hls_url', 'video_url', 'video_flv_url'), {url_or_none},
        )):
            if media_url in seen_urls:
                continue
            seen_urls.add(media_url)
            ext = determine_ext(media_url)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    media_url, video_id, mpd_id='dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append({
                    'url': media_url,
                    'ext': ext or 'mp4',
                    'format_id': 'http',
                    'quality': 1,
                })

        cc_url = traverse_obj(metadata, ('cc_path', {url_or_none}))
        if cc_url:
            lang = traverse_obj(metadata, ('content_language_iso2', {str})) or 'en'
            self._merge_subtitles({lang: [{'url': cc_url}]}, target=subtitles)

        if not formats:
            if traverse_obj(metadata, ('nodeRestrictionType', {str})) == 'geo-restricted':
                self.raise_geo_restricted()
            self.raise_no_formats('No video URL available', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(metadata, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': (('main_picture', 'picture'), {url_or_none}, any),
                'duration': ('runtime', {int_or_none}),
                'creators': ('author', {str}, filter, all, filter),
                'cast': ('actors', ..., {str}, {str.strip}, filter),
                'categories': ('content_genre', {str}, {
                    lambda s: [c.strip() for c in s.split(',') if c.strip()]}),
                'age_limit': ('age_appropriate_rating', {parse_age_limit}),
                'language': ('content_language_iso2', {str}),
                'timestamp': ('date', {lambda s: self._parse_api_timestamp(s, day_first=False)}),
                'release_timestamp': ('release_date', {
                    lambda s: self._parse_api_timestamp(s, day_first=True)}),
                'series': ('series_name', {str}, filter),
                'season_number': ('season', {int_or_none}),
                'episode_number': ('episode', {int_or_none}),
                'episode': ('episode_title', {str}, filter),
            }),
        }
