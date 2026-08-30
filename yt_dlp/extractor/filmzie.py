from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_age_limit,
    parse_iso8601,
    parse_qs,
    update_url_query,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class FilmzieIE(InfoExtractor):
    IE_DESC = 'Filmzie'
    _VALID_URL = r'https?://(?:www\.)?filmzie\.com/content/(?P<id>[^/?#]+)'
    _API_BASE = 'https://filmzie.com/api/v1'
    _CDN_BASE = 'https://d3qxhvuywdalwo.cloudfront.net/'
    _TESTS = [{
        'url': 'https://filmzie.com/content/intermate-2019',
        'md5': 'a852ddbc2b1b0d3f7f4fd925a03f578e',
        'info_dict': {
            'id': '63a43a6c9b52a1714855eba0',
            'ext': 'mp4',
            'title': 'Intermate',
            'description': 'md5:4dc313028ad2850aaea4084e1814da9e',
            'display_id': 'intermate-2019',
            'duration': 5147,
            'thumbnail': r're:https://d3qxhvuywdalwo\.cloudfront\.net/.+',
            'age_limit': 16,
            'cast': ['Lauren Swickard', 'Allison Dunbar', 'Vedette Lim', 'Maya Stojan',
                     'Blythe Auffarth', 'Tony Napoli', 'Malea Rose'],
            'creators': ['Richard Lerner'],
            'categories': ['sci_fi'],
            'uploader': 'Flashout Films',
            'release_timestamp': 1546300800,
            'release_date': '20190101',
            'timestamp': 1671707244,
            'upload_date': '20221222',
        },
    }, {
        'url': 'https://filmzie.com/content/heroes-manufactured-creators-unleashed-2020',
        'info_dict': {
            'id': '620f4e11e837ef001e6fcb2b',
            'title': 'Heroes Manufactured: Creators Unleashed',
            'description': 'md5:6df9bacf1297c7fdbfd552a007a7c9fe',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://filmzie.com/content/intermate-2019?sourceId=613744175971e8001d714ce7',
        'only_matching': True,
    }, {
        'url': 'https://www.filmzie.com/content/intermate-2019',
        'only_matching': True,
    }]

    def _call_api(self, path, video_id, note=None):
        response = self._download_json(
            f'{self._API_BASE}/{path}', video_id, note=note, headers={
                'Accept': 'application/json',
                'Referer': 'https://filmzie.com/',
            })
        error = traverse_obj(response, ('error', 0, {dict}))
        if error:
            raise ExtractorError(
                traverse_obj(error, (('desc', 'msg'), {str}, any)) or 'Filmzie API error',
                expected=True)
        return response.get('data')

    def _thumbnail(self, images):
        for key in traverse_obj(images, (('poster', 'featured2'), 'amazonKey', {str}, all)):
            if key:
                return urljoin(self._CDN_BASE, key)

    def _age_limit(self, content):
        age_limit = (
            parse_age_limit(traverse_obj(content, ('ratings', 'mpaa', {str})))
            or parse_age_limit(traverse_obj(content, ('pgRating', {str})))
            or parse_age_limit(traverse_obj(content, ('ratings', 'bbfc', {str}))))
        if age_limit is None and traverse_obj(content, 'adultsOnly'):
            return 18
        return age_limit

    def _select_video(self, content, video_id):
        videos = traverse_obj(content, ('videos', ..., {dict})) or []
        if video_id:
            video = next((v for v in videos if v.get('id') == video_id), None)
            if not video:
                raise ExtractorError(f'Video {video_id} not found', expected=True)
            return video
        return (
            next((v for v in videos if v.get('type') == 'PAID_CONTENT'), None)
            or next((v for v in videos if v.get('type') not in (None, 'TRAILER')), None)
            or next(iter(videos), None))

    def _episode_entries(self, slug, content, seasons):
        entries = []
        for season in seasons or []:
            for episode in traverse_obj(season, ('episodes', ..., {dict})):
                video_id = traverse_obj(episode, ('videoId', {str}))
                if video_id:
                    entries.append(self.url_result(
                        update_url_query(
                            f'https://filmzie.com/content/{slug}', {'videoId': video_id}),
                        ie=self.ie_key(), video_id=video_id,
                        video_title=traverse_obj(episode, ('title', {str}))))
        if entries:
            return entries
        return [
            self.url_result(
                update_url_query(f'https://filmzie.com/content/{slug}', {'videoId': video_id}),
                ie=self.ie_key(), video_id=video_id)
            for video_id in traverse_obj(
                content, ('videos', lambda _, v: v['type'] == 'EPISODE', 'id', {str}, all))
        ]

    def _episode_meta(self, content, video_id):
        content_id = traverse_obj(content, ('id', {str}))
        if not content_id:
            return {}
        seasons = self._call_api(
            f'content/{content_id}/season', video_id, 'Downloading seasons JSON') or []
        for season in seasons:
            for idx, episode in enumerate(traverse_obj(season, ('episodes', ..., {dict})), 1):
                if episode.get('videoId') != video_id:
                    continue
                title = traverse_obj(episode, ('title', {str}))
                episode_number = int_or_none(
                    self._search_regex(r'^(\d+)', title or '', 'episode number', default=None)) or idx
                return {
                    'title': title,
                    'description': traverse_obj(episode, ('description', {str})),
                    'duration': traverse_obj(episode, ('duration', {int_or_none})),
                    'thumbnail': self._thumbnail(traverse_obj(episode, ('images', {dict}))),
                    'series': traverse_obj(content, ('title', {str})),
                    'series_id': content_id,
                    'season': traverse_obj(season, ('title', {str})),
                    'season_id': traverse_obj(season, ('id', {str})),
                    'season_number': traverse_obj(season, ('seasonNumber', {int_or_none})),
                    'episode': title,
                    'episode_id': traverse_obj(episode, ('id', {str})),
                    'episode_number': episode_number,
                    'cast': traverse_obj(episode, ('actors', ..., {str}, all)) or None,
                    'creators': traverse_obj(episode, ('directors', ..., {str}, all)) or None,
                }
        return {
            'series': traverse_obj(content, ('title', {str})),
            'series_id': content_id,
        }

    def _extract_stream(self, video_id):
        stream = self._call_api(f'video/stream/{video_id}', video_id, 'Downloading stream JSON')
        media_url = traverse_obj(stream, (
            'source', (('hlsV2', {url_or_none}), ('sources', ..., 'file', {url_or_none})), any))
        if not media_url:
            self.raise_no_formats('No video source', expected=True, video_id=video_id)
            return [], {}
        return self._extract_m3u8_formats_and_subtitles(
            media_url, video_id, 'mp4', m3u8_id='hls')

    def _real_extract(self, url):
        slug = self._match_id(url)
        requested_id = traverse_obj(parse_qs(url), ('videoId', 0, {str}))
        content = self._call_api(f'content/{slug}', slug, 'Downloading content JSON')
        if not isinstance(content, dict):
            raise ExtractorError('Unable to extract Filmzie content', expected=True)
        if traverse_obj(content, 'comingSoon'):
            raise ExtractorError('This title is not yet available', expected=True)

        content_id = traverse_obj(content, ('id', {str})) or slug
        content_type = traverse_obj(content, ('type', {str}))

        if content_type == 'TV_SHOW' and not requested_id:
            seasons = self._call_api(
                f'content/{content_id}/season', slug, 'Downloading seasons JSON') or []
            entries = self._episode_entries(slug, content, seasons)
            first_id = traverse_obj(entries, (0, 'id', {str}))
            if entries and self._yes_playlist(content_id, first_id):
                return self.playlist_result(
                    entries, content_id,
                    traverse_obj(content, ('title', {str})),
                    traverse_obj(content, ('description', {str})))
            requested_id = first_id

        video = self._select_video(content, requested_id)
        if not video:
            raise ExtractorError('No playable video found', expected=True)
        video_id = traverse_obj(video, ('id', {str})) or requested_id or slug
        formats, subtitles = self._extract_stream(video_id)

        info = {
            'id': video_id,
            'display_id': slug,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': self._thumbnail(traverse_obj(content, ('images', {dict}))),
            'age_limit': self._age_limit(content),
            **traverse_obj(content, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'duration': ('duration', {int_or_none}),
                'cast': ('actors', ..., {str}, all),
                'creators': ('directors', ..., {str}, all),
                'categories': ('category', ..., {str}, all),
                'uploader': ('studio', {str}),
                'release_timestamp': ('released', {parse_iso8601}),
            }),
            **traverse_obj(video, {
                'duration': ('duration', {int_or_none}),
                'timestamp': ('created', {parse_iso8601}),
            }),
        }
        if content_type == 'TV_SHOW':
            info.update(self._episode_meta(content, video_id))
        return info
