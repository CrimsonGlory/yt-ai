import re

from .common import InfoExtractor
from ..utils import ExtractorError, parse_qs, remove_start, traverse_obj, url_or_none


class RbgTumIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<hostname>(?:live\.rbg\.tum\.de|tum\.live))/w/(?P<id>[^?#]+)'
    _TESTS = [{
        # Combined view
        'url': 'https://live.rbg.tum.de/w/cpp/22128',
        'skip': 'stale test sample / site changed',
        'md5': '53a5e7b3e07128e33bbf36687fe1c08f',
        'info_dict': {
            'id': 'cpp/22128',
            'ext': 'mp4',
            'title': 'Lecture: October 18. 2022',
            'series': 'Concepts of C++ programming (IN2377)',
        },
    }, {
        # Presentation only
        'url': 'https://live.rbg.tum.de/w/I2DL/12349/PRES',
        'md5': '2161064c44e90ccc50afeea291f9ee52',
        'info_dict': {
            'id': 'I2DL/12349/PRES',
            'ext': 'mp4',
            'title': 'Lecture 3: Introduction to Neural Networks',
            'series': 'Introduction to Deep Learning (IN2346)',
        },
    }, {
        # Camera only
        'url': 'https://live.rbg.tum.de/w/fvv-info/16130/CAM',
        'skip': 'stale test sample / site changed',
        'md5': 'e04189d92ff2f56aedf5cede65d37aad',
        'info_dict': {
            'id': 'fvv-info/16130/CAM',
            'ext': 'mp4',
            'title': 'Fachschaftsvollversammlung',
            'series': 'Fachschaftsvollversammlung Informatik',
        },
    }, {
        'url': 'https://tum.live/w/linalginfo/27102',
        'only_matching': True,
    }]

    _VIEW_KIND = {
        'PRES': 'WATCH_VIEW_KIND_PRESENTATION',
        'CAM': 'WATCH_VIEW_KIND_CAMERA',
        'COMB': 'WATCH_VIEW_KIND_COMBINED',
    }

    def _real_extract(self, url):
        video_id, hostname = self._match_valid_url(url).group('id', 'hostname')
        parts = video_id.strip('/').split('/')
        view = None
        if len(parts) >= 3 and parts[-1] in self._VIEW_KIND:
            view = parts[-1]
            slug, stream_id = parts[0], parts[1]
        elif len(parts) >= 2:
            slug, stream_id = parts[0], parts[1]
        else:
            raise ExtractorError('Unable to parse TUM-Live watch URL', expected=True)

        watch = self._download_json(
            f'https://{hostname}/api/v2/streams/{slug}/{stream_id}/watch',
            video_id, fatal=False, errnote=False)
        views = traverse_obj(watch, ('views', ..., {dict})) or []
        wanted = self._VIEW_KIND.get(view)
        selected = None
        if wanted:
            selected = next((item for item in views if item.get('kind') == wanted), None)
        if not selected:
            selected = next(
                (item for item in views if item.get('kind') == 'WATCH_VIEW_KIND_COMBINED'),
                None) or (views[0] if views else None)
        m3u8 = traverse_obj(selected, ('playlistUrl', {url_or_none}))

        if not m3u8:
            webpage = self._download_webpage(url, video_id)
            m3u8 = self._html_search_regex(
                r'"(https://[^"]+\.m3u8[^"]*)', webpage, 'm3u8', default=None)
            lecture_title = self._html_search_regex(
                r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', fatal=False)
            lecture_series_title = remove_start(self._html_extract_title(webpage), 'TUM-Live | ')
        else:
            lecture_title = traverse_obj(watch, ('stream', ('displayName', 'name'), {str}, any))
            lecture_series_title = traverse_obj(watch, ('course', 'name', {str}))

        if not m3u8:
            raise ExtractorError('Unable to extract m3u8', expected=True)

        formats = self._extract_m3u8_formats(
            m3u8, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')

        return {
            'id': video_id,
            'title': lecture_title,
            'series': lecture_series_title,
            'formats': formats,
        }


class RbgTumCourseIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<hostname>(?:live\.rbg\.tum\.de|tum\.live))/old/course/(?P<id>(?P<year>\d+)/(?P<term>\w+)/(?P<slug>[^/?#]+))'
    _TESTS = [{
        'url': 'https://live.rbg.tum.de/old/course/2022/S/fpv',
        'skip': 'video gone',
        'info_dict': {
            'title': 'Funktionale Programmierung und Verifikation (IN0003)',
            'id': '2022/S/fpv',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 13,
    }, {
        'url': 'https://tum.live/old/course/2025/W/WiSe25_26_ItDL',
        'skip': 'video gone',
        'info_dict': {
            'title': 'Introduction to Deep Learning (IN2346)',
            'id': '2025/W/WiSe25_26_ItDL',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 1,
    }, {
        'url': 'https://live.rbg.tum.de/old/course/2022/W/set',
        'skip': 'video gone',
        'info_dict': {
            'title': 'SET FSMPIC',
            'id': '2022/W/set',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 6,
    }, {
        'url': 'https://tum.live/old/course/2023/S/linalginfo',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id, hostname, year, term, slug = self._match_valid_url(url).group('id', 'hostname', 'year', 'term', 'slug')
        meta = self._download_json(
            f'https://{hostname}/api/courses/{slug}/', course_id, fatal=False,
            errnote=False, query={'year': year, 'term': term}) or {}
        lecture_series_title = meta.get('Name')
        lectures = [self.url_result(f'https://{hostname}/w/{slug}/{stream_id}', RbgTumIE)
                    for stream_id in traverse_obj(meta, ('Streams', ..., 'ID'))]

        if not lectures:
            webpage = self._download_webpage(url, course_id)
            lecture_series_title = remove_start(self._html_extract_title(webpage), 'TUM-Live | ')
            lectures = [self.url_result(f'https://{hostname}{lecture_path}', RbgTumIE)
                        for lecture_path in re.findall(r'href="(/w/[^/"]+/[^/"]+)"', webpage)]

        return self.playlist_result(lectures, course_id, lecture_series_title)


class RbgTumNewCourseIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<hostname>(?:live\.rbg\.tum\.de|tum\.live))/\?'
    _TESTS = [{
        'url': 'https://live.rbg.tum.de/?year=2022&term=S&slug=fpv&view=3',
        'skip': 'video gone',
        'info_dict': {
            'title': 'Funktionale Programmierung und Verifikation (IN0003)',
            'id': '2022/S/fpv',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 13,
    }, {
        'url': 'https://tum.live/?year=2025&term=W&slug=WiSe25_26_ItDL&view=3',
        'skip': 'video gone',
        'info_dict': {
            'title': 'Introduction to Deep Learning (IN2346)',
            'id': '2025/W/WiSe25_26_ItDL',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 1,
    }, {
        'url': 'https://live.rbg.tum.de/?year=2022&term=W&slug=set&view=3',
        'skip': 'video gone',
        'info_dict': {
            'title': 'SET FSMPIC',
            'id': '2022/W/set',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 6,
    }, {
        'url': 'https://tum.live/?year=2023&term=S&slug=linalginfo&view=3',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        query = parse_qs(url)
        errors = [key for key in ('year', 'term', 'slug') if not query.get(key)]
        if errors:
            raise ExtractorError(f'Input URL is missing query parameters: {", ".join(errors)}')
        year, term, slug = query['year'][0], query['term'][0], query['slug'][0]
        hostname = self._match_valid_url(url).group('hostname')

        return self.url_result(f'https://{hostname}/old/course/{year}/{term}/{slug}', RbgTumCourseIE)
