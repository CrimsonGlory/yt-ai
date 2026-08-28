from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    parse_resolution,
    qualities,
    str_to_int,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class RadioJavanIE(InfoExtractor):
    _VALID_URL = [
        r'https?://(?:www\.)?radiojavan\.com/videos/video/(?P<id>[^/?#]+)',
        r'https?://(?:www\.)?play\.radiojavan\.com/video/(?P<id>[^/?#]+)',
    ]
    _TESTS = [{
        'url': 'http://www.radiojavan.com/videos/video/chaartaar-ashoobam',
        'md5': 'e85208ffa3ca8b83534fca9fe19af95b',
        'info_dict': {
            'id': 'chaartaar-ashoobam',
            'ext': 'mp4',
            'title': 'Chaartaar - "Ashoobam"',
            'thumbnail': r're:https?://.*\.(?:jpe?g|png)',
            'uploader': 'Chaartaar',
            'track': 'Ashoobam',
            'timestamp': 1424026317,
            'upload_date': '20150215',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        },
        'params': {'format': 'hd/hq'},
    }, {
        'url': 'https://play.radiojavan.com/video/chaartaar-ashoobam',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'https://play.radiojavan.com/api/p/video', video_id,
            query={'id': video_id}, headers={
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'https://play.radiojavan.com/video/{video_id}',
            })
        if not traverse_obj(data, 'permlink'):
            raise ExtractorError('Video not found', expected=True)

        quality = qualities(('hq', 'hd', '4k'))
        formats, seen = [], set()
        for media_url in traverse_obj(data, (
            ('lq_link', 'link', 'hq_link', 'hd_4k_link'), {url_or_none},
        )):
            if media_url in seen:
                continue
            seen.add(media_url)
            format_id = self._search_regex(
                r'/media/music_video/([^/]+)/', media_url, 'format id', default='http')
            f = parse_resolution(format_id) or {}
            f.update({
                'url': media_url,
                'format_id': format_id,
                'quality': quality(format_id),
                'ext': 'mp4',
            })
            formats.append(f)

        hls_url = traverse_obj(data, (
            ('hls', 'high_web', 'low_web', 'high', 'low'), {url_or_none}), get_all=False)
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        return {
            'id': video_id,
            'title': traverse_obj(data, 'title'),
            'thumbnail': traverse_obj(
                data, (('photo', 'thumbnail', 'photo_large'), {url_or_none}), get_all=False),
            'timestamp': parse_iso8601(traverse_obj(data, 'created_at')),
            'view_count': str_to_int(traverse_obj(data, 'views')),
            'like_count': str_to_int(traverse_obj(data, 'likes')),
            'dislike_count': str_to_int(traverse_obj(data, 'dislikes')),
            'uploader': traverse_obj(data, 'artist'),
            'track': traverse_obj(data, 'song'),
            'formats': formats,
        }
