from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class RacingTVIE(InfoExtractor):
    IE_NAME = 'racingtv'
    IE_DESC = 'Racing TV'
    _VALID_URL = r'https?://(?:www\.)?racingtv\.com/watch/on-demand/(?:[\w-]+/)?(?P<id>\d+)'
    _API_BASE = 'https://api.racingtv.com/'
    _API_KEY = '936fdbdf-1e46-4f82-9d18-d81b4803537d'
    _PREROLL_WAIT = 6
    _TESTS = [{
        'url': 'https://www.racingtv.com/watch/on-demand/137181',
        'md5': '8d352c0f625c13687dfe66fde90c49ef',
        'info_dict': {
            'id': '137181',
            'ext': 'mp4',
            'title': '2022-02-08 13:50:00 Taunton',
            'description': 'Free Racing 14th March Handicap Hurdle',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 300,
            'timestamp': 1644330626,
            'upload_date': '20220208',
            'categories': ['Replay Archive'],
        },
    }, {
        'url': 'https://www.racingtv.com/watch/on-demand/interviews/1464802',
        'only_matching': True,
    }, {
        'url': 'https://racingtv.com/watch/on-demand/137181',
        'only_matching': True,
    }]

    def _call_api(self, path, video_id, note='Downloading API JSON',
                  query=None, expected_status=None, fatal=True):
        return self._download_json(
            f'{self._API_BASE}{path}', video_id, note, query=query, headers={
                'Accept': 'application/json',
                'API-KEY': self._API_KEY,
            }, expected_status=expected_status, fatal=fatal)

    def _media_urls(self, player):
        return traverse_obj(player, (
            'player', 'sources', ..., 'url', {url_or_none},
            {lambda u: None if not u or 'onspace/media/assets' in u else u}, all)) or []

    def _download_player(self, video_id):
        player = self._call_api(
            f'member/watch/on-demand/videos/{video_id}', video_id,
            'Downloading player JSON', expected_status=(401, 402, 403))
        status = traverse_obj(player, ('meta', 'status', {int}))
        if status == 401:
            self.raise_login_required(
                traverse_obj(player, ('error', 'text', {str}))
                or 'This video is only available to Racing TV members')

        media_urls = self._media_urls(player)
        token = traverse_obj(player, ('player', 'preroll_token', {str}))
        if media_urls or not token:
            return player, media_urls

        self._sleep(self._PREROLL_WAIT, video_id)
        player = self._call_api(
            f'member/watch/on-demand/videos/{video_id}', video_id,
            'Downloading player JSON after preroll',
            query={'preroll_token': token}, expected_status=(402, 403))
        return player, self._media_urls(player)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = traverse_obj(
            self._call_api(
                f'videos/on-demand/{video_id}', video_id,
                'Downloading video JSON', fatal=False),
            ('video', {dict})) or {}

        player, media_urls = self._download_player(video_id)
        if not media_urls:
            raise ExtractorError(
                traverse_obj(player, ('error', 'text', {str}))
                or 'No video source found; this video may require a Racing TV membership',
                expected=True)

        formats, subtitles = [], {}
        for media_url in media_urls:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls')
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(video, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('placeholder_image_url', {url_or_none}),
                'duration': ('duration', {parse_duration}),
                'timestamp': ('published', 'datetime', {parse_iso8601}),
                'categories': ('categories', ..., 'title', {str}, all),
            }),
        }
