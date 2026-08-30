from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
    str_or_none,
    unescapeHTML,
    unified_strdate,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class KanIE(InfoExtractor):
    IE_DESC = 'Kan (Israeli Public Broadcasting Corporation)'
    _BASE_URL = 'https://www.kan.org.il/'
    _VALID_URL = r'https?://(?:www\.)?kan\.org\.il/(?:(?P<live>live)/?|(?:content/.+?/)(?P<id>\d+)/?)(?:[?#]|$)'
    _GEO_COUNTRIES = ['IL']
    _TESTS = [{
        # Podcast episode (Omny MP3). VOD HLS is geo-restricted to Israel.
        'url': 'https://www.kan.org.il/content/kan/podcasts/p-8266/1094114/',
        'md5': 'a6d9afd7a417a846e4b830f3210244bb',
        'info_dict': {
            'id': '1094114',
            'ext': 'mp3',
            'title': 'תמיד יש לי כוח בעולמך להיות',
            'description': 'md5:25e30228ae3615573b32713b05677a99',
            'thumbnail': r're:https?://www\.kan\.org\.il/media/.+',
            'duration': 2718,
            'series': 'מה שכרוך',
            'channel': 'כאן הסכתים',
            'episode': 'תמיד יש לי כוח בעולמך להיות',
            'episode_number': 1730,
            'upload_date': '20260830',
        },
    }, {
        # TV VOD: RedGalaxy player JSON with 1080p HLS (geo-restricted CDN)
        'url': 'https://www.kan.org.il/content/kan/kan-11/p-11843/s8/756427/',
        'info_dict': {
            'id': '756427',
            'ext': 'mp4',
            'title': 'בואו לאכול איתי עונה 8 | פרק 1 - שבוע צפון, יום א\'',
            'description': 'md5:bf6674df79a679f407dce9a5c9ba6025',
            'thumbnail': r're:https?://www\.kan\.org\.il/media/.+',
            'duration': 1747,
            'timestamp': 1717317045,
            'upload_date': '20240602',
            'series': 'בואו לאכול איתי',
            'channel': 'כאן 11',
            'season': 'Season 8',
            'season_number': 8,
            'episode_number': 1,
            'episode': 'שבוע צפון, יום א\'',
            'categories': ['בישול', 'אוכל', 'קומדיה'],
            'live_status': 'not_live',
        },
        'params': {'skip_download': True},
        'expected_warnings': ['Failed to download m3u8'],
    }, {
        'url': 'https://www.kan.org.il/live/',
        'only_matching': True,
    }, {
        'url': 'https://www.kan.org.il/content/kan/kan-11/p-864341/s2/1071176/',
        'only_matching': True,
    }, {
        'url': 'https://kan.org.il/content/kan/podcasts/p-8266/1094114',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id') or mobj.group('live')
        webpage = self._download_webpage(url, video_id, impersonate=True)

        redge = self._search_json(
            r'<script[^>]+data-redge-config="[^"]+"[^>]*>',
            webpage, 'redge player config', video_id, default=None)
        if redge:
            return self._extract_redge(redge, webpage, video_id)

        playlist = self._search_json(
            r'window\.audioPlayerPlaylist\s*=', webpage, 'audio playlist',
            video_id, contains_pattern=r'\[(?s:.+)', default=None)
        if playlist:
            return self._extract_audio(playlist, webpage, video_id)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        media_url = traverse_obj(json_ld, 'url', {url_or_none})
        if media_url:
            json_ld.pop('url', None)
            return {
                'id': video_id,
                **json_ld,
                'formats': self._extract_media_url(media_url, video_id),
            }

        self.raise_no_formats('No Kan player or media URL found', expected=True)

    def _abs_url(self, url):
        if not url:
            return None
        if url.startswith('//'):
            return f'https:{url}'
        return urljoin(self._BASE_URL, url)

    def _page_meta(self, webpage, video_id):
        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('formats', None)
        data_layer = self._search_json(
            r'dataLayer\.push\(', webpage, 'data layer', video_id,
            transform_source=js_to_json, default=None) or {}
        return json_ld, {
            key: value
            for key, value in traverse_obj(data_layer, {
                'duration': ('item_duration', {int_or_none}),
                'series': ('program_name', {unescapeHTML}),
                'episode': ('episode_title', {unescapeHTML}),
                'episode_number': ('episode_number', {int_or_none}),
                'season_number': ('season', {int_or_none}, {lambda n: n or None}),
                'upload_date': ('date_time', {unified_strdate}),
                'channel': ('channel_name', {unescapeHTML}),
                'categories': ('genre_tags', {self._split_tags}),
            }).items() if value is not None
        }

    @staticmethod
    def _split_tags(value):
        if not value:
            return None
        return [unescapeHTML(tag.strip()) for tag in value.split(',') if tag.strip()]

    def _extract_media_url(self, media_url, video_id):
        headers = {'Referer': self._BASE_URL}
        ext = determine_ext(media_url)
        if ext == 'm3u8' or 'playlist.m3u8' in media_url:
            formats, _ = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                headers=headers)
            if formats:
                return formats
            return [{
                'format_id': 'hls',
                'url': media_url,
                'ext': 'mp4',
                'protocol': 'm3u8_native',
                'http_headers': headers,
            }]
        return [{
            'url': media_url,
            'ext': ext or 'mp4',
            'http_headers': headers,
            'vcodec': 'none' if ext in ('mp3', 'm4a', 'aac') else None,
        }]

    def _extract_redge(self, config, webpage, display_id):
        video_id = str_or_none(config.get('id')) or display_id
        if traverse_obj(config, ('drm', 'widevine'), ('drm', 'fairplay', 'src')):
            self.report_drm(video_id)

        json_ld, data_layer = self._page_meta(webpage, video_id)
        headers = {'Referer': self._BASE_URL}
        formats, subtitles = [], {}
        hls = self._abs_url(traverse_obj(config, ('file', 'hls', {str})))
        if hls:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls, video_id, 'mp4', m3u8_id='hls', fatal=False,
                live=bool(config.get('isLive')), headers=headers)
            if hls_fmts:
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
            else:
                formats.append({
                    'format_id': 'hls',
                    'url': hls,
                    'ext': 'mp4',
                    'protocol': 'm3u8_native',
                    'http_headers': headers,
                })
        if not formats:
            self.raise_no_formats('No media formats in RedGalaxy player config', expected=True)

        is_live = bool(config.get('isLive'))
        meta = config.get('meta') or {}
        live_meta = traverse_obj(config, ('liveMetaData', 0, {dict})) or {}
        thumbnail = self._abs_url(
            traverse_obj(config, ('poster', {str})) or json_ld.get('thumbnail'))

        return {
            'id': video_id,
            **json_ld,
            **data_layer,
            'title': (
                json_ld.get('title')
                or self._og_search_title(webpage, default=None)
                or traverse_obj(meta, ('title', {unescapeHTML}))),
            'thumbnail': thumbnail,
            'series': data_layer.get('series') or traverse_obj(meta, ('seriesName', {unescapeHTML})),
            'season_number': (
                data_layer.get('season_number')
                or int_or_none(meta.get('seasonNumber'))
                or int_or_none(live_meta.get('Season'))),
            'episode_number': (
                data_layer.get('episode_number')
                or int_or_none(live_meta.get('EpisodeNumber'))),
            'episode': data_layer.get('episode') or traverse_obj(meta, ('title', {unescapeHTML})),
            'categories': data_layer.get('categories') or traverse_obj(
                meta, ('genre', ..., {unescapeHTML}, filter)),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            'live_status': 'is_live' if is_live else 'not_live',
        }

    def _extract_audio(self, playlist, webpage, video_id):
        item = traverse_obj(playlist, (
            lambda _, v: str_or_none(v.get('id')) == video_id, any,
        )) or traverse_obj(playlist, 0) or {}
        media_url = traverse_obj(item, ('sources', ..., 'src', {url_or_none}, any))
        if not media_url:
            self.raise_no_formats('No audio source found', expected=True)

        json_ld, data_layer = self._page_meta(webpage, video_id)
        thumbnail = self._abs_url(
            traverse_obj(item, ('poster', {str})) or json_ld.get('thumbnail'))
        duration = data_layer.get('duration')
        if duration is None:
            # Playlist duration is in minutes when it is a short integer
            raw_duration = int_or_none(item.get('duration'))
            duration = raw_duration * 60 if raw_duration and raw_duration < 1000 else raw_duration

        return {
            'id': str_or_none(item.get('id')) or video_id,
            **json_ld,
            **data_layer,
            'title': (
                traverse_obj(item, ('title', {unescapeHTML}))
                or json_ld.get('title')
                or self._og_search_title(webpage, default=None)),
            'description': (
                traverse_obj(item, ('description', {unescapeHTML}))
                or json_ld.get('description')),
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': self._extract_media_url(media_url, video_id),
        }
