import json

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    clean_html,
    # remove_end,
    str_or_none,
    strip_or_none,
    unified_timestamp,
)


class PacktPubBaseIE(InfoExtractor):
    # _PACKT_BASE = 'https://www.packtpub.com'
    _STATIC_PRODUCTS_BASE = 'https://static.packt-cdn.com/products/'


class PacktPubIE(PacktPubBaseIE):
    _VALID_URL = r'https?://(?:(?:www\.)?packtpub\.com/mapt|subscription\.packtpub\.com)/video/[^/]+/(?P<course_id>\d+)/(?P<chapter_id>[^/]+)/(?P<id>[^/]+)(?:/(?P<display_id>[^/?&#]+))?'

    _TESTS = [{
        'url': 'https://subscription.packtpub.com/video/programming/9781837024155/p1/video1_1/intro-to-rust',
        'md5': '49582345e6225394d1d2deedb22cd3a5',
        'info_dict': {
            'id': 'video1_1',
            'ext': 'mp4',
            'title': 'Intro to Rust',
            'thumbnail': r're:(?i)^https?://.*\.(?:jpg|jpeg|png)',
            'timestamp': 1732752000,
            'upload_date': '20241128',
        },
    }, {
        'url': 'https://www.packtpub.com/mapt/video/web-development/9781787122215/20528/20530/Project+Intro',
        'skip': 'video gone',
        'md5': '1e74bd6cfd45d7d07666f4684ef58f70',
        'info_dict': {
            'id': '20530',
            'ext': 'mp4',
            'title': 'Project Intro',
            'thumbnail': r're:(?i)^https?://.*\.jpg',
            'timestamp': 1490918400,
            'upload_date': '20170331',
        },
    }, {
        'url': 'https://subscription.packtpub.com/video/web_development/9781787122215/20528/20530/project-intro',
        'only_matching': True,
    }, {
        'url': 'https://subscription.packtpub.com/video/programming/9781838988906/p1/video1_1/business-card-project',
        'only_matching': True,
    }]
    _NETRC_MACHINE = 'packtpub'
    _TOKEN = None

    def _perform_login(self, username, password):
        try:
            self._TOKEN = self._download_json(
                'https://services.packtpub.com/auth-v1/users/tokens', None,
                'Downloading Authorization Token', data=json.dumps({
                    'username': username,
                    'password': password,
                }).encode())['data']['access']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (400, 401, 404):
                message = self._parse_json(e.cause.response.read().decode(), None)['message']
                raise ExtractorError(message, expected=True)
            raise

    def _real_extract(self, url):
        course_id, chapter_id, video_id, display_id = self._match_valid_url(url).groups()

        headers = {}
        if self._TOKEN:
            headers['Authorization'] = 'Bearer ' + self._TOKEN
        try:
            video = self._download_json(
                f'https://subscription.packtpub.com/api/products/{course_id}/{chapter_id}/{video_id}',
                video_id, 'Downloading JSON video', headers=headers)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (400, 401, 403):
                self.raise_login_required('This video is locked')
            raise

        video_url = video.get('data')
        if not video_url:
            self.raise_login_required('This video is locked')

        title = display_id or video_id
        toc = self._download_json(
            self._STATIC_PRODUCTS_BASE + f'{course_id}/toc', video_id, fatal=False)
        for chapter in (toc or {}).get('chapters') or []:
            if str_or_none(chapter.get('id')) != chapter_id:
                continue
            for section in chapter.get('sections') or []:
                if str_or_none(section.get('id')) == video_id:
                    title = strip_or_none(section.get('title')) or title
                    break
            break

        metadata = self._download_json(
            self._STATIC_PRODUCTS_BASE + f'{course_id}/summary',
            video_id, fatal=False) or {}

        subtitles = {}
        for caption in video.get('captions') or []:
            caption_url = caption.get('location')
            if not caption_url:
                continue
            subtitles.setdefault('en', []).append({
                'url': caption_url,
                'ext': caption.get('type'),
            })

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': metadata.get('coverImage'),
            'timestamp': unified_timestamp(metadata.get('publicationDate')),
            'subtitles': subtitles,
        }


class PacktPubCourseIE(PacktPubBaseIE):
    _VALID_URL = r'(?P<url>https?://(?:(?:www\.)?packtpub\.com/mapt|subscription\.packtpub\.com)/video/[^/]+/(?P<id>\d+))'
    _TESTS = [{
        'url': 'https://www.packtpub.com/mapt/video/web-development/9781787122215',
        'info_dict': {
            'id': '9781787122215',
            'title': 'Learn Nodejs by building 12 projects [Video]',
            'description': 'md5:022061f8491074cd1dd00b2f0a37193b',
        },
        'playlist_count': 90,
    }, {
        'url': 'https://subscription.packtpub.com/video/web_development/9781787122215',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if PacktPubIE.suitable(url) else super().suitable(url)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        url, course_id = mobj.group('url', 'id')

        course = self._download_json(
            self._STATIC_PRODUCTS_BASE + f'{course_id}/toc', course_id)
        metadata = self._download_json(
            self._STATIC_PRODUCTS_BASE + f'{course_id}/summary',
            course_id, fatal=False) or {}

        entries = []
        for chapter_num, chapter in enumerate(course['chapters'], 1):
            chapter_id = str_or_none(chapter.get('id'))
            sections = chapter.get('sections')
            if not chapter_id or not isinstance(sections, list):
                continue
            chapter_info = {
                'chapter': chapter.get('title'),
                'chapter_number': chapter_num,
                'chapter_id': chapter_id,
            }
            for section in sections:
                section_id = str_or_none(section.get('id'))
                if not section_id or section.get('contentType') != 'video':
                    continue
                entry = {
                    '_type': 'url_transparent',
                    'url': '/'.join([url, chapter_id, section_id]),
                    'title': strip_or_none(section.get('title')),
                    'description': clean_html(section.get('summary')),
                    'thumbnail': metadata.get('coverImage'),
                    'timestamp': unified_timestamp(metadata.get('publicationDate')),
                    'ie_key': PacktPubIE.ie_key(),
                }
                entry.update(chapter_info)
                entries.append(entry)

        return self.playlist_result(
            entries, course_id, metadata.get('title'),
            clean_html(metadata.get('about')))
