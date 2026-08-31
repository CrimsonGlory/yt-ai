from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    parse_duration,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PMVHavenIE(InfoExtractor):
    IE_NAME = 'pmvhaven'
    IE_DESC = 'PMVHaven'
    _VALID_URL = r'https?://(?:www\.)?pmvhaven\.com/(?:video/(?:[^/?#]*_)?|videos/)(?P<id>[0-9a-fA-F]{24})'
    _TESTS = [{
        'url': 'https://pmvhaven.com/video/MARAVILLOSA-PMV-_66195f01d0f2168854325fd0',
        'md5': '532b79a8c34a810d9f32fee0cee5ae21',
        'info_dict': {
            'id': '66195f01d0f2168854325fd0',
            'ext': 'mp4',
            'title': 'MARAVILLOSA (PMV)',
            'description': 'MARAVILLOSA (PMV) byShchokoitsia',
            'thumbnail': r're:https?://.+\.webp',
            'duration': 183,
            'timestamp': 1712938753,
            'upload_date': '20240412',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'average_rating': float,
            'width': 1920,
            'height': 1080,
            'uploader': 'ShchokoitsiaPMV',
            'uploader_id': '68fbd851b99aaf24a4c04d38',
            'uploader_url': 'https://pmvhaven.com/profile/ShchokoitsiaPMV',
            'age_limit': 18,
            'tags': ['Anal', 'Blowjob', 'Cum', 'Cum in mouth', 'Cute'],
            'cast': ['Aeries steele', 'Leana lovings', 'Ruth lee', 'Sweetie fox'],
            'creators': ['ShchokoitsiaPMV'],
        },
    }, {
        'url': 'https://pmvhaven.com/video/maravillosa-pmv_66195f01d0f2168854325fd0',
        'only_matching': True,
    }, {
        'url': 'https://pmvhaven.com/videos/66195f01d0f2168854325fd0',
        'only_matching': True,
    }, {
        'url': 'https://pmvhaven.com/videos/68fbd85ab99aaf24a4c04d44',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = traverse_obj(self._download_json(
            f'https://pmvhaven.com/api/videos/{video_id}', video_id), ('data', {dict}))
        if not data:
            raise ExtractorError('Unable to extract video data', expected=True)

        formats, subtitles = [], {}
        hls_url = traverse_obj(data, ('hlsMasterPlaylistUrl', {url_or_none}))
        if hls_url:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        video_url = traverse_obj(data, ('videoUrl', {url_or_none}))
        if video_url:
            formats.append({
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
                'format_id': 'http',
                'quality': 1,
                **traverse_obj(data, {
                    'width': ('width', {int_or_none}),
                    'height': ('height', {int_or_none}),
                    'filesize': ('fileSize', {int_or_none}),
                }),
            })

        if not formats:
            self.raise_no_formats('No video formats available', expected=True, video_id=video_id)

        uploader = traverse_obj(data, (('uploaderUsername', 'uploader'), {str}, any))
        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 18,
            'duration': (int_or_none(data.get('durationSeconds'))
                         or parse_duration(data.get('duration'))),
            'uploader_url': f'https://pmvhaven.com/profile/{uploader}' if uploader else None,
            **traverse_obj(data, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
                'timestamp': (('uploadDate', 'releaseDate'), {parse_iso8601}, any),
                'view_count': ('views', {int_or_none}),
                'like_count': ('likes', {int_or_none}),
                'dislike_count': ('dislikes', {int_or_none}),
                'average_rating': ('rating', {float_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'uploader': (('uploaderUsername', 'uploader'), {str}, any),
                'uploader_id': ('uploaderId', {str}),
                'tags': ('tags', ..., {str}),
                'cast': ('starsTags', ..., {str}),
                'creators': ('creator', ..., {str}),
            }),
        }
