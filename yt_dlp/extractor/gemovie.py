import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_age_limit,
    parse_qs,
    traverse_obj,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class GeMovieIE(InfoExtractor):
    IE_NAME = 'ge.movie'
    IE_DESC = 'GE.MOVIE'
    _VALID_URL = r'https?://(?:www\.)?ge\.movie/(?:movie|serial)/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?'
    _TESTS = [
        {
            'url': 'https://ge.movie/movie/49574/superman',
            'md5': 'acf34768a366cb4dad89cd4101dc9c48',
            'info_dict': {
                'id': '49574',
                'ext': 'mp4',
                'display_id': 'superman',
                'title': 'სუპერმენი',
                'alt_title': 'Superman',
                'description': 'md5:32ba65e5154b34430136eb70cb02daee',
                'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png|webp)',
                'release_year': 2025,
                'timestamp': 1743811257,
                'upload_date': '20250405',
                'age_limit': 13,
                'genres': ['ფანტასტიკა', 'მძაფრ-სიუჟეტიანი', 'სათავგადასავლო'],
            },
        },
        {
            'url': 'https://ge.movie/movie/49574/superman-qartulad',
            'only_matching': True,
        },
        {
            'url': 'https://ge.movie/movie/49523/a-minecraft-movie',
            'only_matching': True,
        },
        {
            'url': 'https://ge.movie/serial/49582/such-brave-girls?season=1&episode=2',
            'only_matching': True,
        },
    ]

    _AUDIO_LANGS = {
        'ქართულად': 'ka',
        'ქართული': 'ka',
        'georgian': 'ka',
        'ინგლისურად': 'en',
        'ინგლისური': 'en',
        'english': 'en',
        'რუსულად': 'ru',
        'რუსული': 'ru',
        'russian': 'ru',
        'უკრაინულად': 'uk',
        'უკრაინული': 'uk',
        'ukrainian': 'uk',
        'თურქულად': 'tr',
        'თურქული': 'tr',
        'turkish': 'tr',
        'ფრანგულად': 'fr',
        'ფრანგული': 'fr',
        'french': 'fr',
        'გერმანულად': 'de',
        'გერმანული': 'de',
        'german': 'de',
        'იტალიურად': 'it',
        'იტალიური': 'it',
        'italian': 'it',
        'იაპონურად': 'ja',
        'იაპონური': 'ja',
        'japanese': 'ja',
        'კორეულად': 'ko',
        'კორეული': 'ko',
        'korean': 'ko',
        'ესპანურად': 'es',
        'ესპანური': 'es',
        'spanish': 'es',
    }
    _QUALITY_RANK = {
        '4k': 4,
        'uhd': 4,
        '2160p': 4,
        'fhd': 3,
        'fullhd': 3,
        '1080p': 3,
        'hd': 2,
        '720p': 2,
        'sd': 1,
        '480p': 1,
        '360p': 0,
        '240p': -1,
    }

    def _playlist_url(self, embed_url):
        parsed = urllib.parse.urlparse(embed_url)
        query = {
            k: v[-1]
            for k, v in urllib.parse.parse_qs(parsed.query, keep_blank_values=True).items()
            if k not in ('img', 'referer', 'v')
        }
        query['p'] = 'l.playlist'
        return urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, '/file/play', '', urllib.parse.urlencode(query), ''),
        )

    def _language_code(self, label):
        if not label:
            return None
        return self._AUDIO_LANGS.get(label) or self._AUDIO_LANGS.get(label.lower())

    def _parse_playerjs_file(self, file_str, video_id, headers):
        formats = []
        for quality_part in (file_str or '').split(','):
            quality_part = quality_part.strip()
            if not quality_part:
                continue
            quality = None
            quality_m = re.match(r'\[([^\]]+)\]', quality_part)
            if quality_m:
                quality = quality_m.group(1)
                quality_part = quality_part[quality_m.end() :]
            quality_id = (quality or '').lower() or None
            height = int_or_none(self._search_regex(r'(\d{3,4})p', quality_id or '', 'height', default=None))
            for i, track in enumerate(quality_part.split(';')):
                track = track.strip()
                if not track:
                    continue
                audio = None
                audio_m = re.match(r'\{([^}]+)\}', track)
                if audio_m:
                    audio = audio_m.group(1)
                    track = track[audio_m.end() :]
                media_url = url_or_none(track.strip())
                if not media_url:
                    continue
                lang = self._language_code(audio)
                format_id = join_nonempty(quality_id, lang or (f'audio{i}' if audio else None))
                ext = determine_ext(media_url, 'mp4')
                if ext == 'm3u8':
                    for hls_fmt in self._extract_m3u8_formats(
                        media_url, video_id, 'mp4', m3u8_id=format_id or 'hls', fatal=False, headers=headers,
                    ):
                        hls_fmt.setdefault('http_headers', headers)
                        if lang:
                            hls_fmt.setdefault('language', lang)
                        formats.append(hls_fmt)
                    continue
                formats.append(
                    {
                        'url': media_url,
                        'format_id': format_id or 'http',
                        'ext': ext,
                        'height': height,
                        'language': lang,
                        'format_note': audio,
                        'quality': self._QUALITY_RANK.get(quality_id, -1),
                        'language_preference': 10 if lang == 'ka' else -1,
                        'http_headers': headers,
                    },
                )
        return formats

    def _walk_playerjs_items(self, node, season_hint=None):
        if isinstance(node, str):
            yield {'file': node, 'season_number': season_hint}
            return
        if isinstance(node, list):
            for child in node:
                yield from self._walk_playerjs_items(child, season_hint)
            return
        if not isinstance(node, dict):
            return
        folder = node.get('folder')
        if folder:
            season_number = int_or_none(
                self._search_regex(r'(\d+)', str(node.get('title') or ''), 'season', default=None),
            )
            for child in folder:
                yield from self._walk_playerjs_items(child, season_number)
            return
        if not node.get('file'):
            return
        item = dict(node)
        item_id = str(node.get('id') or '')
        id_m = re.fullmatch(r'(\d+)-(\d+)', item_id)
        if id_m:
            item['season_number'] = int(id_m.group(1))
            item['episode_number'] = int(id_m.group(2))
        elif season_hint is not None:
            item['season_number'] = season_hint
        yield item

    def _extract_json_ld(self, webpage, video_id):
        for ld in self._yield_json_ld(webpage, video_id, default=[]):
            if isinstance(ld, dict) and ld.get('@type') in ('Movie', 'TVSeries', 'TVEpisode'):
                return ld
        return {}

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id, impersonate=True)

        embed_url = url_or_none(
            urljoin(
                url,
                self._html_search_regex(
                    (
                        r'<iframe[^>]+id=["\'](?:movie|serial)_embed["\'][^>]+src=["\']([^"\']+)',
                        r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]+id=["\'](?:movie|serial)_embed',
                    ),
                    webpage,
                    'embed url',
                ),
            ),
        )
        if not embed_url:
            raise ExtractorError('Unable to extract player embed', expected=True)

        parsed_embed = urllib.parse.urlparse(embed_url)
        headers = {'Referer': f'{parsed_embed.scheme}://{parsed_embed.netloc}/'}

        playlist = self._download_json(
            self._playlist_url(embed_url),
            video_id,
            'Downloading Playerjs playlist',
            headers=headers,
            impersonate=True,
            fatal=False,
        )
        if playlist is None:
            embed_page = self._download_webpage(
                embed_url, video_id, 'Downloading embed page', headers={'Referer': url}, impersonate=True,
            )
            playlist_url = self._search_regex(
                r'\bfile\s*:\s*(["\'])(?P<url>https?://[^"\']+)\1', embed_page, 'playlist url', group='url',
            )
            playlist = self._download_json(
                playlist_url, video_id, 'Downloading Playerjs playlist', headers=headers, impersonate=True,
            )

        items = list(self._walk_playerjs_items(playlist))
        if not items:
            raise ExtractorError('No video sources found', expected=True)

        qs = parse_qs(url)
        wanted_season = int_or_none(traverse_obj(qs, ('season', 0)))
        wanted_episode = int_or_none(traverse_obj(qs, ('episode', 0)))
        if wanted_episode is not None:
            wanted_season = wanted_season or 1
            items = [
                item
                for item in items
                if item.get('season_number') == wanted_season and item.get('episode_number') == wanted_episode
            ]
            if not items:
                raise ExtractorError(f'Episode S{wanted_season}E{wanted_episode} is not available', expected=True)

        json_ld = self._extract_json_ld(webpage, video_id)
        title = (
            self._html_search_regex(r'data-title_ge="([^"]+)"', webpage, 'title', default=None)
            or traverse_obj(json_ld, ('name', {str}))
            or self._og_search_title(webpage)
        )
        alt_title = self._html_search_regex(r'data-title_en="([^"]+)"', webpage, 'English title', default=None)
        description = traverse_obj(json_ld, ('description', {str})) or self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage, default=None) or traverse_obj(json_ld, ('image', {url_or_none}))
        release_year = int_or_none(self._html_search_regex(r'data-year="(\d{4})"', webpage, 'year', default=None))
        timestamp = unified_timestamp(traverse_obj(json_ld, ('datePublished', {str})))
        age_limit = parse_age_limit(traverse_obj(json_ld, ('contentRating', {str})))
        genres = traverse_obj(json_ld, ('genre', ..., {str})) or None

        def make_entry(item):
            season_number = int_or_none(item.get('season_number'))
            episode_number = int_or_none(item.get('episode_number'))
            entry_id = video_id
            if season_number is not None and episode_number is not None:
                entry_id = f'{video_id}-{season_number}-{episode_number}'
            episode_title = traverse_obj(item, ('title', {str}))
            formats = self._parse_playerjs_file(item.get('file'), entry_id, headers)
            if not formats:
                self.raise_no_formats('No video sources found', expected=True, video_id=entry_id)
            return {
                'id': entry_id,
                'display_id': display_id,
                'title': join_nonempty(title, episode_title, delim=' - '),
                'alt_title': alt_title,
                'description': description,
                'thumbnail': thumbnail,
                'release_year': release_year,
                'timestamp': timestamp,
                'age_limit': age_limit,
                'genres': genres,
                'season_number': season_number,
                'episode_number': episode_number,
                'episode': episode_title,
                'formats': formats,
                'http_headers': headers,
            }

        if len(items) > 1:
            return self.playlist_result((make_entry(item) for item in items), video_id, title, description)

        return make_entry(items[0])
