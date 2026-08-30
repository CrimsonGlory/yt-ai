from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    format_field,
    int_or_none,
    parse_duration,
    parse_iso8601,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class DeviantArtIE(InfoExtractor):
    IE_NAME = 'DeviantArt'
    IE_DESC = 'DeviantArt'
    _VALID_URL = r'https?://(?:www\.)?deviantart\.com/(?:[^/?#]+/art/[^/?#]+-|view/|deviation/)(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.deviantart.com/animnade/art/Styra-Plushie-Highlights-977847473',
        'md5': '087e292efef8f83ca532fdafd7cb91be',
        'info_dict': {
            'id': '977847473',
            'ext': 'mp4',
            'title': 'Styra Plushie Highlights',
            'description': 'Styra Starsparkle | Styra The Adventurer | S1 EP1 - YouTube',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png|webp)',
            'uploader': 'ANIMNADE',
            'uploader_id': '78842500',
            'uploader_url': 'https://www.deviantart.com/ANIMNADE',
            'duration': 16,
            'timestamp': 1692418510,
            'upload_date': '20230819',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'tags': ['anime', 'video', 'animegirl', 'highlight', 'plush', 'plushie', 'naturescapes', 'naturebeautiful'],
            'age_limit': 0,
        },
    }, {
        'url': 'https://www.deviantart.com/arven92/art/Remember-Me-Warrior-Cats-AMV-ANIMATIC-886311677',
        'only_matching': True,
    }, {
        'url': 'https://www.deviantart.com/view/977847473',
        'only_matching': True,
    }, {
        'url': 'https://www.deviantart.com/deviation/977847473',
        'only_matching': True,
    }]

    def _parse_initial_state(self, webpage, video_id):
        raw = self._search_regex(
            r'window\.__INITIAL_STATE__\s*=\s*JSON\.parse\(("(?:\\.|[^"\\])*")\)',
            webpage, 'initial state', default=None)
        if not raw:
            return {}
        decoded = self._parse_json(
            raw.replace('\\\'', "'"), video_id, fatal=False)
        if isinstance(decoded, str):
            decoded = self._parse_json(decoded, video_id, fatal=False)
        return decoded if isinstance(decoded, dict) else {}

    def _extract_json_ld_video(self, webpage, video_id):
        for ld in self._yield_json_ld(webpage, video_id, fatal=False) or []:
            if not isinstance(ld, dict):
                continue
            graph = ld.get('@graph')
            nodes = graph if isinstance(graph, list) else [ld]
            for node in nodes:
                entity = node.get('mainEntity') if isinstance(node, dict) else None
                if not isinstance(entity, dict):
                    entity = node if isinstance(node, dict) else None
                if not isinstance(entity, dict):
                    continue
                types = entity.get('@type')
                if isinstance(types, str):
                    types = [types]
                if isinstance(types, list) and 'VideoObject' in types:
                    return entity
        return {}

    def _format_from_url(self, video_url):
        fmt = {
            'url': video_url,
            'ext': 'mp4',
        }
        height = int_or_none(self._search_regex(
            r'(?:\.|res_)(\d+)p', video_url, 'height', default=None))
        if height:
            fmt['height'] = height
            fmt['format_id'] = f'{height}p'
        return fmt

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        state = self._parse_initial_state(webpage, video_id)
        deviation = traverse_obj(
            state, ('@@entities', 'deviation', video_id, {dict})) or {}
        extended = traverse_obj(
            state, ('@@entities', 'deviationExtended', video_id, {dict})) or {}
        json_ld = self._extract_json_ld_video(webpage, video_id)

        formats = traverse_obj(deviation, ('media', 'types', lambda _, v: (
            v.get('t') == 'video' and url_or_none(v.get('b'))
        ), {
            'url': ('b', {url_or_none}),
            'format_id': ('q', {str}),
            'width': ('w', {int_or_none}),
            'height': ('h', {int_or_none}),
            'filesize': ('f', {int_or_none}),
        })) or []
        json_ld_url = url_or_none(json_ld.get('contentUrl'))
        if json_ld_url and not any(f.get('url') == json_ld_url for f in formats):
            formats.append(self._format_from_url(json_ld_url))

        is_video = (
            bool(formats)
            or traverse_obj(deviation, 'isVideo') is True
            or traverse_obj(deviation, 'type') == 'film'
            or traverse_obj(deviation, 'filetype') == 'video')
        if not formats:
            if deviation and not is_video:
                raise ExtractorError(
                    'This DeviantArt deviation is not a video', expected=True)
            raise ExtractorError('No video formats found', expected=True)

        author = traverse_obj(deviation, 'author')
        if isinstance(author, dict):
            uploader = traverse_obj(author, ('username', {str}))
            uploader_id = str_or_none(traverse_obj(author, 'userId'))
        else:
            uploader_id = str_or_none(author)
            uploader = traverse_obj(
                state, ('@@entities', 'user', uploader_id, 'username', {str}))

        return {
            'id': video_id,
            'formats': formats,
            'title': (
                traverse_obj(deviation, ('title', {str}))
                or traverse_obj(json_ld, ('name', {str}))
                or self._og_search_title(webpage, default=None)),
            'description': (
                clean_html(traverse_obj(
                    extended, ('descriptionText', 'html', 'markup', {str})))
                or None),
            'thumbnail': (
                traverse_obj(deviation, ('media', 'baseUri', {url_or_none}))
                or url_or_none(json_ld.get('thumbnailUrl'))
                or self._og_search_thumbnail(webpage, default=None)),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': format_field(uploader, None, 'https://www.deviantart.com/%s'),
            'duration': (
                traverse_obj(
                    deviation,
                    ('media', 'types', lambda _, v: v.get('t') == 'video', 'd', {int_or_none}),
                    get_all=False)
                or parse_duration(json_ld.get('duration'))),
            'timestamp': parse_iso8601(
                traverse_obj(deviation, ('publishedTime', {str}))
                or json_ld.get('uploadDate') or json_ld.get('datePublished')),
            'view_count': traverse_obj(deviation, ('stats', 'views', {int_or_none})),
            'like_count': traverse_obj(deviation, ('stats', 'favourites', {int_or_none})),
            'comment_count': traverse_obj(deviation, ('stats', 'comments', {int_or_none})),
            'tags': traverse_obj(extended, ('tags', ..., 'name', {str})) or None,
            'age_limit': 18 if traverse_obj(deviation, 'isMature') or traverse_obj(deviation, 'isNsfg') else 0,
        }
