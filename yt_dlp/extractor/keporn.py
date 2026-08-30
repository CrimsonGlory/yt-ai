import base64

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_duration,
    traverse_obj,
    unified_strdate,
    url_or_none,
    urljoin,
)


def decode_video_url(text):
    return base64.b64decode(text.translate(text.maketrans({
        '\u0405': 'S',
        '\u0406': 'I',
        '\u0408': 'J',
        '\u0410': 'A',
        '\u0412': 'B',
        '\u0415': 'E',
        '\u041a': 'K',
        '\u041c': 'M',
        '\u041d': 'H',
        '\u041e': 'O',
        '\u0420': 'P',
        '\u0421': 'C',
        '\u0425': 'X',
        ',': '/',
        '.': '+',
        '~': '=',
    }))).decode()


class KepornIE(InfoExtractor):
    IE_DESC = 'keporn.vip'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?(?P<host>(?:[\w-]+\.)?keporn\.(?:vip|com))/
        (?:videos?|embed)/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?
    '''
    _TESTS = [{
        'url': 'https://f1.keporn.vip/videos/115237/chubby-huge-boobs-brunette/',
        'md5': 'f3b9a3829c426544d1f935dd2947c1a2',
        'info_dict': {
            'id': '115237',
            'display_id': 'chubby-huge-boobs-brunette',
            'ext': 'mp4',
            'title': 'Chubby Huge Boobs Brunette',
            'description': '',
            'thumbnail': r're:https?://.+',
            'duration': 480,
            'upload_date': '20250718',
            'uploader': 'Jason Moretti',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'age_limit': 18,
            'categories': 'count:17',
            'tags': 'count:11',
        },
    }, {
        'url': 'https://keporn.com/videos/115237/chubby-huge-boobs-brunette/',
        'only_matching': True,
    }, {
        'url': 'https://f1.keporn.vip/embed/115237/',
        'only_matching': True,
    }, {
        'url': 'https://f2.keporn.vip/videos/115237/',
        'only_matching': True,
    }]

    def _call_api(self, url, video_id, fatal=False, **kwargs):
        content = self._download_json(url, video_id, fatal=fatal, **kwargs)
        if traverse_obj(content, 'error'):
            raise self._error_or_warning(ExtractorError(
                f'Keporn said: {content["error"]}', expected=True), fatal=fatal)
        return content or {}

    def _real_extract(self, url):
        video_id, host, display_id = self._match_valid_url(url).group(
            'id', 'host', 'display_id')
        headers = {'Referer': url, 'X-Requested-With': 'XMLHttpRequest'}

        video_file = self._call_api(
            f'https://{host}/api/videofile.php?video_id={video_id}&lifetime=8640000',
            video_id, fatal=True, note='Downloading video file info', headers=headers)
        if not isinstance(video_file, list):
            raise ExtractorError('Unexpected videofile response', expected=True)

        slug = f'{int(1E6 * (int(video_id) // 1E6))}/{1000 * (int(video_id) // 1000)}'
        video_info = self._call_api(
            f'https://{host}/api/json/video/86400/{slug}/{video_id}.json',
            video_id, note='Downloading video info', headers=headers)

        formats = []
        for video in video_file:
            encoded_url = traverse_obj(video, ('video_url', {str}))
            if not encoded_url:
                continue
            decoded_url = decode_video_url(encoded_url)
            formats.append({
                'url': urljoin(f'https://{host}', decoded_url),
                'format_id': (traverse_obj(video, ('format', {str})) or 'mp4').lstrip('.'),
                'ext': determine_ext(decoded_url, 'mp4'),
                'http_headers': {'Referer': url},
            })
        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        return {
            'id': video_id,
            'display_id': display_id or traverse_obj(video_info, ('video', 'dir', {str})),
            'title': traverse_obj(video_info, ('video', 'title', {str})),
            'description': traverse_obj(video_info, ('video', 'description', {str})),
            'uploader': traverse_obj(video_info, ('video', 'user', 'username', {str})),
            'duration': parse_duration(traverse_obj(video_info, ('video', 'duration'))),
            'upload_date': unified_strdate(traverse_obj(video_info, ('video', 'post_date'))),
            'view_count': int_or_none(traverse_obj(video_info, ('video', 'statistics', 'viewed'))),
            'like_count': int_or_none(traverse_obj(video_info, ('video', 'statistics', 'likes'))),
            'dislike_count': int_or_none(traverse_obj(video_info, ('video', 'statistics', 'dislikes'))),
            'thumbnail': traverse_obj(video_info, ('video', 'thumbsrc', {url_or_none})),
            'categories': traverse_obj(video_info, ('video', 'categories', ..., 'title', {str})),
            'tags': traverse_obj(video_info, ('video', 'tags', ..., 'title', {str})),
            'age_limit': 18,
            'formats': formats,
        }
