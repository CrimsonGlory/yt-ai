from .common import InfoExtractor
from .vimeo import VimeoIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ProkoBaseIE(InfoExtractor):
    _API_BASE = 'https://www.proko.com/api'
    _API_HEADERS = {
        'Accept': 'application/json',
        'Referer': 'https://www.proko.com/',
    }

    def _call_api(self, path, video_id, note=None, fatal=True, expected_status=None):
        return self._download_json(
            f'{self._API_BASE}/{path}', video_id, note=note,
            headers=self._API_HEADERS, fatal=fatal,
            expected_status=expected_status)

    def _cover_url(self, cover, kind):
        signature = traverse_obj(cover, ('signature', {str}))
        if signature:
            return f'https://img-resizer.proko.com/resize/{kind}/cover_image/800x450x1/{signature}'

    def _download_video(self, video_id, display_id, note):
        return traverse_obj(self._call_api(
            f'videos/{video_id}', display_id, note,
            fatal=False, expected_status=(401, 403, 404)), ('data', {dict}))


class ProkoIE(ProkoBaseIE):
    IE_NAME = 'proko'
    IE_DESC = 'Proko'
    _VALID_URL = r'https?://(?:www\.)?proko\.com/(?:course-lesson|lesson)/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.proko.com/course-lesson/learning-how-to-draw',
        'md5': '8a678469d8182e1ac0c0735fe320452a',
        'info_dict': {
            'id': 'tx5kJvI14Jg',
            'ext': 'mp4',
            'display_id': 'learning-how-to-draw',
            'title': 'Learning How to Draw',
            'description': 'md5:23cb3de0bb68246d17400bbae00d5f15',
            'duration': 436,
            'timestamp': 1671116848,
            'upload_date': '20221215',
            'thumbnail': r're:https://img-resizer\.proko\.com/resize/lesson/cover_image/.+',
            'view_count': int,
            'age_limit': 0,
            'uploader': 'Proko',
            'uploader_id': '@ProkoTV',
            'uploader_url': 'https://www.youtube.com/@ProkoTV',
            'channel': 'Proko',
            'channel_id': 'UClM2LuQ1q5WEc23462tQzBg',
            'channel_url': 'https://www.youtube.com/channel/UClM2LuQ1q5WEc23462tQzBg',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'like_count': int,
            'comment_count': int,
            'categories': ['Education'],
            'tags': 'count:12',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
            'heatmap': 'count:100',
            'chapters': [{
                'start_time': 0,
                'title': 'Intro',
                'end_time': 59,
            }, {
                'start_time': 59,
                'title': 'Can I Learn to Draw?',
                'end_time': 163,
            }, {
                'start_time': 163,
                'title': 'Physical and Intellectual',
                'end_time': 282,
            }, {
                'start_time': 282,
                'title': 'The Mindset',
                'end_time': 436,
            }],
        },
        'add_ie': ['Youtube'],
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
        ],
    }, {
        'url': 'https://www.proko.com/course-lesson/how-to-draw-gesture',
        'info_dict': {
            'id': '1055665300',
            'ext': 'mp4',
            'display_id': 'how-to-draw-gesture',
            'title': 'How to Draw Gesture',
            'description': 'md5:7772cb66249776e21aaad8c228a8768c',
            'duration': 571,
            'timestamp': 1371452400,
            'upload_date': '20130617',
            'thumbnail': r're:https://img-resizer\.proko\.com/resize/lesson/cover_image/.+',
            'view_count': int,
            'uploader': 'Proko',
            'uploader_id': 'proko',
            'uploader_url': 'https://vimeo.com/proko',
        },
        'add_ie': ['Vimeo'],
        'params': {'skip_download': 'm3u8'},
        'expected_warnings': ['Failed to parse XML'],
    }, {
        'url': 'https://www.proko.com/lesson/learning-how-to-draw',
        'only_matching': True,
    }, {
        'url': 'https://www.proko.com/course-lesson/project-get-your-tools-and-start-playing',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        slug = self._match_id(url)
        lesson = traverse_obj(self._call_api(
            f'lessons/{slug}', slug, 'Downloading lesson metadata',
            expected_status=404), ('data', {dict}))
        if not lesson:
            raise ExtractorError('Lesson not found', expected=True)

        video = None
        premium_id = traverse_obj(lesson, ('premium_video_id', {str}))
        free_id = traverse_obj(lesson, ('free_video_id', {str}))
        if premium_id:
            video = self._download_video(
                premium_id, slug, 'Downloading premium video metadata')
        if not video and free_id:
            video = self._download_video(
                free_id, slug, 'Downloading free video metadata')
        if not video:
            if premium_id:
                self.raise_login_required(
                    'This lesson is only available to Proko members', method=None)
            raise ExtractorError('No video is available for this lesson', expected=True)

        info = {
            'display_id': slug,
            'thumbnail': self._cover_url(lesson.get('cover_image'), 'lesson'),
            'duration': int_or_none(video.get('duration')),
            **traverse_obj(lesson, {
                'title': ('title', {str}),
                'description': (('description', 'short_description'), {clean_html}, filter, any),
                'timestamp': ('published_at', {parse_iso8601}),
                'view_count': ('views_count', {int_or_none}),
            }),
        }
        if traverse_obj(lesson, ('has_mature_content', {bool})):
            info['age_limit'] = 18

        video_type = (video.get('video_type') or '').lower()
        host_id = traverse_obj(video, ('video_id', {str}))
        if video_type == 'youtube' and host_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={host_id}',
                YoutubeIE, host_id, url_transparent=True, **info)
        if video_type == 'vimeo' and host_id:
            return self.url_result(
                VimeoIE._smuggle_referrer(
                    f'https://player.vimeo.com/video/{host_id}',
                    f'https://www.proko.com/course-lesson/{slug}'),
                VimeoIE, host_id, url_transparent=True, **info)

        media_url = traverse_obj(video, (
            ('url', 'src', 'source', 'hls_url', 'mp4_url'), {url_or_none}), any)
        if media_url:
            return {
                **info,
                'id': traverse_obj(video, ('id', {str})) or slug,
                'url': media_url,
            }

        raise ExtractorError(
            f'Unsupported Proko video type: {video_type or "unknown"}', expected=True)


class ProkoCourseIE(ProkoBaseIE):
    IE_NAME = 'proko:course'
    IE_DESC = 'Proko courses'
    _VALID_URL = (
        r'https?://(?:www\.)?proko\.com/course/(?P<id>[\w-]+)'
        r'(?:/(?:overview|lessons|comments))?/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://www.proko.com/course/drawing-basics/overview',
        'info_dict': {
            'id': 'drawing-basics',
            'title': 'Drawing Basics',
            'description': 'md5:fdbe7b2d77b1905f59cce3e9ec1f7ac8',
            'thumbnail': r're:https://img-resizer\.proko\.com/resize/course/cover_image/.+',
        },
        'playlist_mincount': 50,
    }, {
        'url': 'https://www.proko.com/course/drawing-basics',
        'only_matching': True,
    }, {
        'url': 'https://www.proko.com/course/drawing-basics/lessons',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        slug = self._match_id(url)
        course = traverse_obj(self._call_api(
            f'courses/{slug}', slug, 'Downloading course metadata',
            expected_status=404), ('data', {dict}))
        if not course:
            raise ExtractorError('Course not found', expected=True)

        course_id = traverse_obj(course, ('id', {str}))
        playlist = {}
        if course_id:
            playlist = self._call_api(
                f'courses/{course_id}/playlist', slug,
                'Downloading course playlist') or {}

        entries = [
            self.url_result(
                f'https://www.proko.com/course-lesson/{lesson_slug}',
                ProkoIE, lesson_slug)
            for lesson_slug in traverse_obj(playlist, ('meta', 'lessons', ..., {str}))
        ]

        return self.playlist_result(
            entries, slug,
            **traverse_obj(course, {
                'title': ('title', {str}),
                'description': (('description', 'short_description'), {clean_html}, filter, any),
            }),
            thumbnail=self._cover_url(course.get('cover_image'), 'course'))
