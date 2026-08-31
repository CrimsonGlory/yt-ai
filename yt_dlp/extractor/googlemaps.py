import re
import urllib.parse

from .common import InfoExtractor
from ..networking import HEADRequest
from ..utils import int_or_none


class GoogleMapsIE(InfoExtractor):
    IE_DESC = 'Google Maps user-uploaded videos'
    _VALID_URL = (
        r'https?://maps\.app\.goo\.gl/(?P<id>[^/?#]+)',
        r'https?://goo\.gl/maps/(?P<id>[^/?#]+)',
        r'https?://(?:(?:www\.)?google\.[^/]+/maps|maps\.google\.[^/]+)/[^#]*(?:!|%21)1s(?P<id>AF1Qip[\w-]+)',
    )
    _TESTS = [
        {
            'url': 'https://maps.app.goo.gl/p1b9kDiD4tXMaYBK8',
            'md5': 'a1bb146410e975da5cb3056d60de0ef7',
            'info_dict': {
                'id': 'AF1QipN5tBYtrxCbrQ5F7jd8ftUHXyEJCMmKz4P9hEhr',
                'ext': 'mp4',
                'title': 'Hamburg',
                'thumbnail': r're:https://lh3\.googleusercontent\.com/p/AF1Qip',
                'width': 1920,
                'height': 1080,
            },
        },
        {
            'url': 'https://www.google.com/maps/place/Hamburg/@53.5510846,9.9936819,3a,75y,90t/data=!3m8!1e5!3m6!1sAF1QipN5tBYtrxCbrQ5F7jd8ftUHXyEJCMmKz4P9hEhr!2e10!3e10!7i1920!8i1080',
            'only_matching': True,
        },
        {
            'url': 'https://goo.gl/maps/p1b9kDiD4tXMaYBK8',
            'only_matching': True,
        },
    ]
    _PHOTO_ID_RE = r'AF1Qip[\w-]+'
    # Progressive MP4 itags used by Google Photos / Maps user content
    _ITAGS = (
        (18, 360),
        (22, 720),
        (37, 1080),
    )

    def _real_initialize(self):
        # Avoid the consent.google.com interstitial when resolving share links
        self._set_cookie('.google.com', 'CONSENT', 'YES+')
        self._set_cookie('.google.com', 'SOCS', 'CAI')

    def _photo_id_from_text(self, text):
        return self._search_regex(rf'(?:!1s|/p/)({self._PHOTO_ID_RE})', text, 'photo id', default=None)

    def _media_url(self, photo_id, suffix):
        return f'https://lh3.googleusercontent.com/p/{photo_id}={suffix}'

    def _probe_video(self, media_url, video_id, note):
        urlh = self._request_webpage(
            HEADRequest(media_url),
            video_id,
            note=note,
            errnote=False,
            fatal=False,
            expected_status=404,
        )
        if not urlh or getattr(urlh, 'status', None) == 404:
            return None
        content_type = (urlh.headers.get('Content-Type') or '').split(';')[0].strip().lower()
        if not content_type.startswith('video/'):
            return None
        return {
            'filesize': int_or_none(urlh.headers.get('Content-Length')),
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        maps_url = urllib.parse.unquote(url)
        webpage = None

        photo_id = display_id if re.fullmatch(self._PHOTO_ID_RE, display_id) else None
        photo_id = photo_id or self._photo_id_from_text(maps_url)

        if not photo_id:
            webpage, urlh = self._download_webpage_handle(url, display_id, note='Resolving Maps URL')
            maps_url = urllib.parse.unquote(urlh.url)
            if 'consent.google.com' in urllib.parse.urlparse(maps_url).netloc:
                continue_url = urllib.parse.parse_qs(urllib.parse.urlparse(maps_url).query).get('continue', [None])[0]
                if continue_url:
                    webpage, urlh = self._download_webpage_handle(
                        continue_url,
                        display_id,
                        note='Downloading Maps page',
                    )
                    maps_url = urllib.parse.unquote(urlh.url)
            photo_id = self._photo_id_from_text(maps_url)
            if not photo_id and webpage:
                photo_id = self._photo_id_from_text(webpage)

        if not photo_id:
            self.raise_no_formats(
                'This Google Maps URL does not contain a user-uploaded video',
                expected=True,
                video_id=display_id,
            )

        width = int_or_none(self._search_regex(r'!7i(\d+)', maps_url, 'width', default=None))
        height = int_or_none(self._search_regex(r'!8i(\d+)', maps_url, 'height', default=None))
        place = self._search_regex(r'/maps/place/([^/@?#]+)', maps_url, 'place name', default=None)
        title = urllib.parse.unquote_plus(place) if place else photo_id
        thumbnail = self._search_regex(
            r'!6s(https://lh\d+\.googleusercontent\.com/[^!]+)',
            maps_url,
            'thumbnail',
            default=None,
        ) or self._media_url(photo_id, 'w1280-h720-k-no')

        formats = []
        for itag, itag_height in self._ITAGS:
            fmt_url = self._media_url(photo_id, f'm{itag}')
            extra = self._probe_video(fmt_url, photo_id, f'Checking itag {itag}')
            if extra is None:
                continue
            formats.append(
                {
                    'url': fmt_url,
                    'format_id': str(itag),
                    'ext': 'mp4',
                    'height': itag_height,
                    **extra,
                },
            )

        original_url = self._media_url(photo_id, 'dv')
        extra = self._probe_video(original_url, photo_id, 'Checking original video')
        if extra is not None:
            formats.append(
                {
                    'url': original_url,
                    'format_id': 'original',
                    'ext': 'mp4',
                    'width': width,
                    'height': height,
                    'quality': 1,
                    **extra,
                },
            )

        if not formats:
            self.raise_no_formats(
                'No video formats found; this Maps link may be a photo or panorama',
                expected=True,
                video_id=photo_id,
            )

        return {
            'id': photo_id,
            'title': title,
            'thumbnail': thumbnail,
            'width': width,
            'height': height,
            'formats': formats,
        }
