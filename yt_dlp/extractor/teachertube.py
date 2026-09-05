import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    qualities,
)


class TeacherTubeIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'teachertube'
    IE_DESC = 'teachertube.com videos'

    _VALID_URL = r'https?://(?:www\.)?teachertube\.com/(?:viewVideo\.php\?video_id=|music\.php\?music_id=|videos?/(?:[\da-z-]+-)?|audio/)(?P<id>\d+)'

    _TESTS = [{
        # flowplayer
        'url': 'https://www.teachertube.com/videos/339997',
        'skip': 'extractor broken: [teachertube] teachertube extractor failed (ExtractorError: [teachertube] unable',
        'md5': 'f9434ef992fd65936d72999951ee254c',
        'info_dict': {
            'id': '339997',
            'ext': 'mp4',
            'title': 'Measures of dispersion from a frequency table',
            'description': 'Measures of dispersion from a frequency table',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
        },
    }, {
        # jwplayer
        'url': 'https://www.teachertube.com/videos/graphing-quadratic-inequalities-on-desmos-507405',
        'skip': 'extractor broken: [teachertube] teachertube extractor failed (ExtractorError: [teachertube] unable',
        'md5': '01e8352006c65757caf7b961f6050e21',
        'info_dict': {
            'id': '507405',
            'ext': 'mp3',
            'title': 'PER ASPERA AD ASTRA',
            'description': 'RADIJSKA EMISIJA ZRAKOPLOVNE TEHNI?KE ?KOLE P',
        },
    }, {
        # unavailable video
        'url': 'http://www.teachertube.com/video/intro-video-schleicher-297790',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        error = self._search_regex(
            r'<div\b[^>]+\bclass=["\']msgBox error[^>]+>([^<]+)', webpage,
            'error', default=None)
        if error:
            raise ExtractorError(f'{self.IE_NAME} said: {error}', expected=True)

        title = (
            self._html_search_meta('title', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage, default=video_id))
        TITLE_SUFFIX = ' - TeacherTube'
        if title.endswith(TITLE_SUFFIX):
            title = title[:-len(TITLE_SUFFIX)].strip()

        description = self._html_search_meta('description', webpage, 'description')
        if description:
            description = description.strip()

        quality = qualities(['mp3', 'flv', 'mp4'])

        media_urls = re.findall(r'data-contenturl="([^"]+)"', webpage)
        media_urls.extend(re.findall(r'var\s+filePath\s*=\s*"([^"]+)"', webpage))
        media_urls.extend(re.findall(r'\'file\'\s*:\s*["\']([^"\']+)["\'],', webpage))
        media_urls.extend(re.findall(r'sourceMP4\.src\s*=\s*[\'"]([^\'"]+)', webpage))
        media_urls.extend(re.findall(r'<source[^>]+src=["\']([^"\']+)', webpage))

        formats = [
            {
                'url': media_url,
                'quality': quality(determine_ext(media_url)),
            } for media_url in set(media_urls)
        ]
        if not formats:
            html5 = self._parse_html5_media_entries(url, webpage, video_id)
            if html5:
                formats = html5[0].get('formats') or (
                    [{'url': html5[0]['url']}] if html5[0].get('url') else [])

        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._html_search_meta(
            'thumbnail', webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class TeacherTubeUserIE(InfoExtractor):
    IE_NAME = 'teachertube:user:collection'
    IE_DESC = 'teachertube.com user and collection videos'

    _VALID_URL = r'https?://(?:www\.)?teachertube\.com/(user/profile|collection)/(?P<user>[0-9a-zA-Z]+)/?'

    _MEDIA_RE = r'''(?sx)
        class="?sidebar_thumb_time"?>[0-9:]+</div>
        \s*
        <a\s+href="(https?://(?:www\.)?teachertube\.com/(?:video|audio)/[^"]+)"
    '''
    _TEST = {
        'url': 'http://www.teachertube.com/user/profile/rbhagwati2',
        'skip': 'video gone',
        'info_dict': {
            'id': 'rbhagwati2',
        },
        'playlist_mincount': 179,
    }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        user_id = mobj.group('user')

        urls = []
        webpage = self._download_webpage(url, user_id)
        urls.extend(re.findall(self._MEDIA_RE, webpage))

        pages = re.findall(rf'/ajax-user/user-videos/{user_id}\?page=([0-9]+)', webpage)[:-1]
        for p in pages:
            more = f'http://www.teachertube.com/ajax-user/user-videos/{user_id}?page={p}'
            webpage = self._download_webpage(more, user_id, f'Downloading page {p}/{len(pages)}')
            video_urls = re.findall(self._MEDIA_RE, webpage)
            urls.extend(video_urls)

        entries = [self.url_result(vurl, 'TeacherTube') for vurl in urls]
        return self.playlist_result(entries, user_id)
