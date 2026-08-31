import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    parse_qs,
    str_or_none,
    traverse_obj,
    url_or_none,
    urljoin,
)


class LookMovie2IE(InfoExtractor):
    IE_DESC = 'LookMovie2'
    _VALID_URL = r'https?://(?:www\.)?lookmovie2\.to/(?P<media_type>movies|shows)/(?:play|view)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.lookmovie2.to/movies/play/1756855-coyote-vs-acme-2026',
        'md5': '8e7519f52d6a9912bb1daa4d8d9e2cf3',
        'info_dict': {
            'id': '156087',
            'ext': 'mp4',
            'title': 'Coyote vs. Acme',
            'description': 'After Acme products fail him one too many times in his dogged pursuit of the Roadrunner, Wile E. Coyote decides to hire a billboard lawyer to sue the Acme Corporation.',
            'display_id': '1756855-coyote-vs-acme-2026',
            'release_year': 2026,
            'thumbnail': r're:https?://www\.lookmovie2\.to/images/.+\.webp',
        },
    }, {
        'url': 'https://www.lookmovie2.to/movies/view/1756855-coyote-vs-acme-2026',
        'only_matching': True,
    }, {
        'url': 'https://lookmovie2.to/shows/play/0149460-futurama-1999#S1-E1-93931',
        'only_matching': True,
    }, {
        'url': 'https://www.lookmovie2.to/shows/view/0149460-futurama-1999?season=1&episode=1&id_episode=93931',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        media_type, slug = self._match_valid_url(url).group('media_type', 'id')
        play_url = re.sub(r'/(?:view|play)/', '/play/', url, count=1)
        webpage = self._download_webpage(play_url, slug)

        if media_type == 'shows':
            return self._extract_show(play_url, webpage, slug)
        return self._extract_movie(play_url, webpage, slug)

    def _extract_movie(self, url, webpage, slug):
        storage = self._search_json(
            r'window\[[\'"]movie_storage[\'"]\]\s*=', webpage,
            'movie storage', slug, transform_source=js_to_json)
        movie_id = str_or_none(storage.get('id_movie')) or slug
        formats, subtitles = self._extract_access(
            url, 'movie-access', {'id_movie': storage.get('id_movie')},
            storage, movie_id)
        return {
            'id': movie_id,
            'display_id': slug,
            'formats': formats,
            'subtitles': subtitles,
            'description': self._og_search_description(webpage, default=None),
            **traverse_obj(storage, {
                'title': ('title', {str}),
                'release_year': ('year', {int_or_none}),
                'thumbnail': (('movie_poster', 'backdrop_huge', 'backdrop_medium'), {str}, {
                    lambda x: url_or_none(urljoin(url, x))}, any),
            }),
        }

    def _extract_show(self, url, webpage, slug):
        storage = self._search_json(
            r'window\[[\'"]show_storage[\'"]\]\s*=', webpage,
            'show storage', slug, transform_source=js_to_json)
        episode = self._select_episode(url, storage.get('seasons') or [])
        episode_id = str_or_none(episode.get('id_episode'))
        if not episode_id:
            raise ExtractorError('Unable to determine episode', expected=True)

        formats, subtitles = self._extract_access(
            url, 'episode-access', {'id_episode': episode_id}, storage, episode_id)
        series = traverse_obj(storage, ('title', {str}))
        episode_title = traverse_obj(episode, ('title', {str}))
        return {
            'id': episode_id,
            'display_id': slug,
            'title': episode_title or series,
            'formats': formats,
            'subtitles': subtitles,
            'description': self._og_search_description(webpage, default=None),
            'series': series,
            **traverse_obj(episode, {
                'episode': ('title', {str}),
                'episode_number': ('episode', {int_or_none}),
                'season_number': ('season', {int_or_none}),
            }),
            **traverse_obj(storage, {
                'release_year': ('year', {int_or_none}),
                'thumbnail': (('poster_medium', 'backdrop_huge', 'backdrop_medium'), {str}, {
                    lambda x: url_or_none(urljoin(url, x))}, any),
            }),
        }

    def _select_episode(self, url, seasons):
        query = parse_qs(url)
        episode_id = int_or_none(traverse_obj(query, ('id_episode', 0)))
        season_number = int_or_none(traverse_obj(query, ('season', 0)))
        episode_number = int_or_none(traverse_obj(query, ('episode', 0)))

        fragment = re.fullmatch(
            r'S(\d+)-E(\d+)-(\d+)', urllib.parse.urlparse(url).fragment or '', re.I)
        if fragment:
            season_number, episode_number, episode_id = map(int, fragment.groups())

        for episode in seasons:
            if episode_id and int_or_none(episode.get('id_episode')) == episode_id:
                return episode
        for episode in seasons:
            if (season_number is not None
                    and int_or_none(episode.get('season')) == season_number
                    and episode_number is not None
                    and int_or_none(episode.get('episode')) == episode_number):
                return episode
        return traverse_obj(seasons, 0) or {}

    def _extract_access(self, url, endpoint, id_query, storage, video_id):
        hash_, expires = traverse_obj(storage, ('hash', {str})), storage.get('expires')
        if not hash_ or expires is None:
            raise ExtractorError('Unable to extract stream access token', expected=True)

        access = self._download_json(
            urljoin(url, f'/api/v1/security/{endpoint}'), video_id,
            query={**id_query, 'hash': hash_, 'expires': expires})
        if not access.get('success'):
            raise ExtractorError(
                traverse_obj(access, ('message', {str})) or 'Unable to access media',
                expected=True)

        formats, subtitles = [], {}
        for quality, stream_url in (access.get('streams') or {}).items():
            stream_url = url_or_none(stream_url)
            if not stream_url:
                continue
            height = int_or_none(re.sub(r'p$', '', str(quality), flags=re.I))
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id=str(quality), fatal=False)
            for fmt in fmts:
                if height and not fmt.get('height'):
                    fmt['height'] = height
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if not formats:
            self.raise_no_formats('No public HLS streams', expected=True, video_id=video_id)

        for sub in traverse_obj(access, ('subtitles', ..., {dict})):
            sub_url = url_or_none(urljoin(url, sub.get('file')))
            if not sub_url:
                continue
            lang = sub.get('language') or 'und'
            subtitles.setdefault(lang, []).append({'url': sub_url})

        return formats, subtitles
