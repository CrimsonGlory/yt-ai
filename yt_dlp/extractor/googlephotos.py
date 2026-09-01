import re

from .common import InfoExtractor
from ..networking import HEADRequest
from ..utils import (
    ExtractorError,
    determine_ext,
    extract_attributes,
    float_or_none,
    int_or_none,
    parse_qs,
    update_url_query,
    url_or_none,
    urlhandle_detect_ext,
)
from ..utils.traversal import traverse_obj


class GooglePhotosBaseIE(InfoExtractor):
    _NETLOC_RE = r'https?://photos\.google\.com/(?:u/\d+/)?'
    _ID_RE = r'AF1Qip[\w-]+'
    _MEDIA_KEY = '76647426'

    def _real_initialize(self):
        # Avoid the consent.google.com interstitial on some locales
        self._set_cookie('.google.com', 'CONSENT', 'YES+')
        self._set_cookie('.google.com', 'SOCS', 'CAI')

    def _share_key(self, url):
        return traverse_obj(parse_qs(url), ('key', 0, {str}))

    def _parse_init_data(self, webpage, video_id):
        blobs = []
        for mobj in re.finditer(r'AF_initDataCallback\(\s*\{\s*key:\s*[\'"]ds:\d+[\'"][^}]*?\bdata:\s*', webpage):
            parsed = self._parse_json(webpage[mobj.end() :], video_id, fatal=False, ignore_extra=True)
            if parsed is not None:
                blobs.append(parsed)
        return blobs

    def _photo_url(self, album_id, photo_id, key=None):
        return update_url_query(
            f'https://photos.google.com/share/{album_id}/photo/{photo_id}', {'key': key} if key else {},
        )

    @staticmethod
    def _dv_url(media_url):
        media_url = url_or_none(media_url)
        if not media_url:
            return None
        return re.sub(r'=.*$', '', media_url) + '=dv'

    @staticmethod
    def _is_video_item(item):
        return any(isinstance(part, dict) and GooglePhotosBaseIE._MEDIA_KEY in part for part in item or [])

    def _media_element_attrs(self, webpage, media_id):
        element = self._search_regex(
            rf'<c-wiz[^>]+data-media-key="{re.escape(media_id)}"[^>]*>',
            webpage, 'media element', default='', group=0)
        return extract_attributes(element) if element else {}


class GooglePhotosIE(GooglePhotosBaseIE):
    IE_NAME = 'google:photos'
    IE_DESC = 'Google Photos shared videos'
    _VALID_URL = rf'{GooglePhotosBaseIE._NETLOC_RE}share/(?P<album>{GooglePhotosBaseIE._ID_RE})/photo/(?P<id>{GooglePhotosBaseIE._ID_RE})'
    _TESTS = [
        {
            'url': 'https://photos.google.com/share/AF1QipNi8VN2pw2Ya_xCV8eFgzEZmiXDy1-GwhXbqFtvXoH3HypF10as9puV8FdoVZpOZA/photo/AF1QipPIoUaSCvCyqWszRQz6n_lz4V8boxtmRO_Ow3OJ?key=WkZjQTIxQTM5a01oZkNUYTE2ZllKTVJKZk1CMTR3',
            'md5': '68954c517ff6c848df9a330c84f9d961',
            'info_dict': {
                'id': 'AF1QipPIoUaSCvCyqWszRQz6n_lz4V8boxtmRO_Ow3OJ',
                'ext': 'mp4',
                'title': '1316.WP_Mint_Light-414w-896h@2x~iphone.mp4',
                'thumbnail': r're:https://lh3\.googleusercontent\.com/pw/',
                'duration': 2.999,
                'timestamp': 1564689889,
                'upload_date': '20190801',
                'uploader': 'Евгений Богун',
                'uploader_id': '115313459248541544360',
                'album': 'iOS Wallpapers',
                'width': 998,
                'height': 2160,
            },
        },
        {
            'url': 'https://photos.google.com/u/0/share/AF1QipNi8VN2pw2Ya_xCV8eFgzEZmiXDy1-GwhXbqFtvXoH3HypF10as9puV8FdoVZpOZA/photo/AF1QipPIoUaSCvCyqWszRQz6n_lz4V8boxtmRO_Ow3OJ?key=WkZjQTIxQTM5a01oZkNUYTE2ZllKTVJKZk1CMTR3',
            'only_matching': True,
        },
    ]

    def _extract_photo_blob(self, blobs, video_id):
        for blob in blobs:
            if traverse_obj(blob, (0, 0, {str})) == video_id:
                return blob
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        blob = self._extract_photo_blob(self._parse_init_data(webpage, video_id), video_id)
        item = traverse_obj(blob, (0, {list})) or []
        attrs = self._media_element_attrs(webpage, video_id)

        lh3_url = traverse_obj(item, (1, 0, {url_or_none})) or url_or_none(attrs.get('data-url'))
        download_url = url_or_none(traverse_obj(blob, (1, {str})))
        if download_url and 'video-downloads.googleusercontent.com' not in download_url:
            download_url = None

        is_video = self._is_video_item(item) or attrs.get('data-isvideo') == 'true' or bool(download_url)
        if not is_video:
            raise ExtractorError('This Google Photos item is not a video', expected=True)

        media_url = download_url or self._dv_url(lh3_url)
        if not media_url:
            if 'accounts.google.com/ServiceLogin' in webpage and not item:
                self.raise_login_required('This Google Photos link requires a shared album key or login')
            self.raise_no_formats('Unable to extract Google Photos video URL', expected=True, video_id=video_id)

        headers = {'Referer': 'https://photos.google.com/'}
        urlh = self._request_webpage(
            HEADRequest(media_url),
            video_id,
            note='Downloading video headers',
            errnote='Unable to download video headers',
            fatal=False,
            headers=headers,
        )
        title = video_id
        ext = 'mp4'
        filesize = None
        if urlh:
            media_url = urlh.url
            filesize = int_or_none(urlh.headers.get('Content-Length'))
            cd = urlh.headers.get('Content-Disposition')
            filename = self._search_regex(r'\bfilename="([^"]+)"', cd, 'filename', default=None) if cd else None
            if filename:
                title = filename
            ext = urlhandle_detect_ext(urlh, default=determine_ext(title, 'mp4')) or 'mp4'

        video_meta = traverse_obj(item, (..., {dict}, self._MEDIA_KEY, {list}, any)) or []

        return {
            'id': video_id,
            'title': title,
            'ext': ext,
            'url': media_url,
            'filesize': filesize,
            'http_headers': headers,
            'thumbnail': lh3_url,
            **traverse_obj(
                item,
                {
                    'width': (1, 1, {int_or_none}),
                    'height': (1, 2, {int_or_none}),
                    'timestamp': (2, {int_or_none(scale=1000)}),
                },
            ),
            **traverse_obj(
                video_meta,
                {
                    'duration': (0, {float_or_none(scale=1000)}),
                    'width': (2, {int_or_none}),
                    'height': (3, {int_or_none}),
                },
            ),
            **traverse_obj(
                blob,
                {
                    'uploader_id': (3, 1, {str}),
                    'uploader': (3, 11, 0, {str}),
                    'album': (4, '131657093', 5, {str}),
                },
            ),
        }


class GooglePhotosAlbumIE(GooglePhotosBaseIE):
    IE_NAME = 'google:photos:album'
    IE_DESC = 'Google Photos shared albums'
    _VALID_URL = rf'{GooglePhotosBaseIE._NETLOC_RE}share/(?P<id>{GooglePhotosBaseIE._ID_RE})/?(?:[?#]|$)'
    _TESTS = [
        {
            'url': 'https://photos.google.com/share/AF1QipNi8VN2pw2Ya_xCV8eFgzEZmiXDy1-GwhXbqFtvXoH3HypF10as9puV8FdoVZpOZA?key=WkZjQTIxQTM5a01oZkNUYTE2ZllKTVJKZk1CMTR3',
            'info_dict': {
                'id': 'AF1QipNi8VN2pw2Ya_xCV8eFgzEZmiXDy1-GwhXbqFtvXoH3HypF10as9puV8FdoVZpOZA',
                'title': 'iOS Wallpapers',
            },
            'playlist_mincount': 10,
            'params': {
                'skip_download': True,
                'extract_flat': 'in_playlist',
            },
        },
        {
            'url': 'https://photos.google.com/u/0/share/AF1QipNi8VN2pw2Ya_xCV8eFgzEZmiXDy1-GwhXbqFtvXoH3HypF10as9puV8FdoVZpOZA?key=WkZjQTIxQTM5a01oZkNUYTE2ZllKTVJKZk1CMTR3',
            'only_matching': True,
        },
    ]

    def _extract_album_blob(self, blobs):
        for blob in blobs:
            first_id = traverse_obj(blob, (1, 0, 0, {str})) or ''
            if first_id.startswith('AF1Qip'):
                return blob
        return None

    def _real_extract(self, url):
        album_id = self._match_id(url)
        key = self._share_key(url)
        webpage = self._download_webpage(url, album_id)

        blob = self._extract_album_blob(self._parse_init_data(webpage, album_id))
        if not blob:
            if 'accounts.google.com/ServiceLogin' in webpage:
                self.raise_login_required('This Google Photos album requires a shared album key or login')
            raise ExtractorError('Unable to extract Google Photos album data', expected=True)

        entries = []
        for item in traverse_obj(blob, (1, ..., {list})):
            photo_id = traverse_obj(item, (0, {str}))
            if not photo_id or not photo_id.startswith('AF1Qip') or not self._is_video_item(item):
                continue
            entries.append(
                self.url_result(self._photo_url(album_id, photo_id, key), ie=GooglePhotosIE, video_id=photo_id),
            )

        return self.playlist_result(entries, album_id, traverse_obj(blob, (3, 1, {str})))
