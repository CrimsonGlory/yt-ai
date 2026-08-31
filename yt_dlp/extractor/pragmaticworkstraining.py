from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    filter_dict,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PragmaticWorksTrainingBaseIE(InfoExtractor):
    _API_BASE = 'https://learning.pragmaticworkstraining.com/api'
    _HEADERS = {
        'Accept': 'application/json',
        'Referer': 'https://learning.pragmaticworkstraining.com/',
    }

    def _call_api(self, path, video_id, note=None):
        data = self._download_json(
            f'{self._API_BASE}/{path}', video_id, note=note, headers=self._HEADERS)
        if data.get('Success') is False:
            raise ExtractorError(
                traverse_obj(data, ('Message', {str})) or 'Pragmatic Works Training API error',
                expected=True)
        return data.get('Object')

    def _extract_mux_video(self, playback_id, video_id, token=None):
        return self._extract_m3u8_formats_and_subtitles(
            f'https://stream.mux.com/{playback_id}.m3u8', video_id, 'mp4', m3u8_id='hls',
            query=filter_dict({'token': token}))


class PragmaticWorksTrainingIE(PragmaticWorksTrainingBaseIE):
    IE_NAME = 'pragmaticworkstraining'
    IE_DESC = 'Pragmatic Works Training'
    _VALID_URL = (
        r'https?://learning\.pragmaticworkstraining\.com/coursePlayer/'
        r'(?P<course_id>[\da-fA-F]{8}-(?:[\da-fA-F]{4}-){3}[\da-fA-F]{12})/'
        r'(?P<id>[\da-fA-F]{8}-(?:[\da-fA-F]{4}-){3}[\da-fA-F]{12})')
    _TESTS = [{
        'url': 'https://learning.pragmaticworkstraining.com/coursePlayer/95ff61b1-1c80-4c35-acc3-3cc136b71b46/F6305848-CEC5-424E-B56F-F5EE9B5DD4DF',
        'md5': '6be83b9107b74b671856d3c3f6159110',
        'info_dict': {
            'id': 'F6305848-CEC5-424E-B56F-F5EE9B5DD4DF',
            'ext': 'mp4',
            'title': 'Module 00A - Course Overview',
            'thumbnail': r're:https://image\.mux\.com/.+/thumbnail\.jpg',
            'subtitles': 'count:2',
        },
    }, {
        'url': 'https://learning.pragmaticworkstraining.com/coursePlayer/95ff61b1-1c80-4c35-acc3-3cc136b71b46/164247B3-48D0-4F8B-8755-0131E33D58B2',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._call_api(
            f'lms/GetVideoPreview/{video_id}', video_id, 'Downloading video preview')
        playback_id = traverse_obj(video, ('MuxPlaybackID', {str}))
        if not playback_id:
            raise ExtractorError('No Mux playback ID for this video', expected=True)

        token = traverse_obj(video, ('Token', {str})) or None
        formats, subtitles = self._extract_mux_video(playback_id, video_id, token)
        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': f'https://image.mux.com/{playback_id}/thumbnail.jpg',
            **traverse_obj(video, {
                'title': ('VideoContentTitle', {str}),
            }),
        }


class PragmaticWorksTrainingCourseIE(PragmaticWorksTrainingBaseIE):
    IE_NAME = 'pragmaticworkstraining:course'
    IE_DESC = 'Pragmatic Works Training courses'
    _VALID_URL = r'https?://learning\.pragmaticworkstraining\.com/course/(?P<id>[\w-]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://learning.pragmaticworkstraining.com/course/automationinaday',
        'info_dict': {
            'id': 'automationinaday',
            'title': 'Automation in a Day',
            'description': 'md5:5d5e611046e3c2bc13eb8b907c6d0c68',
            'thumbnail': r're:https://learning\.pragmaticworkstraining\.com/api/upload/getCourseImage/.+',
        },
        'playlist_mincount': 19,
        'params': {'skip_download': True, 'extract_flat': 'in_playlist'},
    }, {
        'url': 'https://learning.pragmaticworkstraining.com/course/advancedazuredatafactory',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id = self._match_id(url)
        course = self._call_api(
            f'lms/GetCoursePublicInfo/{course_id}', course_id, 'Downloading course info') or {}
        modules = self._call_api(
            f'lms/GetCoursePublicContent/{course_id}', course_id, 'Downloading course content') or []
        course_guid = traverse_obj(course, ('CourseGuid', {str}))
        if not course_guid:
            raise ExtractorError('Unable to extract course GUID', expected=True)

        entries = []
        for module in traverse_obj(modules, (..., {dict})):
            for item in traverse_obj(module, ('CourseModuleContent', ..., {dict})):
                if traverse_obj(item, ('ContentType', {int})) != 3:
                    continue
                content_id = traverse_obj(item, ('CourseModuleContentGuid', {str}))
                if not content_id:
                    continue
                entries.append(self.url_result(
                    f'https://learning.pragmaticworkstraining.com/coursePlayer/{course_guid}/{content_id}',
                    PragmaticWorksTrainingIE, content_id, traverse_obj(item, ('ContentTitle', {str})),
                    **traverse_obj(item, {
                        'duration': ('VideoLength', {int_or_none}),
                    })))

        thumbnail = traverse_obj(course, ('CourseImage', {str}))
        return self.playlist_result(
            entries, course_id,
            **traverse_obj(course, {
                'title': ('CourseTitle', {str}),
                'description': ('CourseDescription', {str}),
            }),
            thumbnail=url_or_none(
                f'https://learning.pragmaticworkstraining.com/api/upload/getCourseImage/{thumbnail}'
                if thumbnail else None),
        )
