import base64

from .common import InfoExtractor
from .videa import VideaIE
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    orderedSet,
    parse_iso8601,
    parse_resolution,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class SmuleIE(InfoExtractor):
    IE_DESC = 'Smule'
    _VALID_URL = (
        r'https?://(?:www\.)?smule\.com/'
        r'(?:recording/(?P<display_id>[^/?#]+)|sing-recording|p|c)/'
        r'(?P<id>\d+_\d+)(?:/(?:frame(?:/box)?|twitter|json))?'
    )
    _EMBED_REGEX = [rf'<iframe[^>]+src=["\'](?P<url>{_VALID_URL})']
    _TESTS = [
        {
            'url': 'https://www.smule.com/recording/billie-happier-than-ever-acoustic/33197115_4356089929',
            'md5': 'e89bdc24625b881f045162ddd71807a0',
            'info_dict': {
                'id': '33197115_4356089929',
                'title': 'Happier Than Ever - Acoustic',
                'display_id': 'billie-happier-than-ever-acoustic',
                'ext': 'mp4',
                'thumbnail': r're:https?://.*\.jpg',
                'description': 'md5:aed4e5342a7d9b29c1012003d12a8b41',
                'creators': ['Kait_is_here', 'EllinaRyz'],
                'timestamp': 1651701380,
                'upload_date': '20220504',
                'channel': 'Kait_is_here',
                'channel_id': '33196155',
                'channel_url': 'https://www.smule.com/Kait_is_here',
                'channel_is_verified': False,
                'duration': 295,
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'artists': ['Billie'],
            },
        },
        {
            'url': 'https://www.smule.com/sing-recording/33197115_4356089929',
            'only_matching': True,
        },
        {
            'url': 'https://www.smule.com/p/33197115_4356089929',
            'only_matching': True,
        },
        {
            'url': 'https://www.smule.com/c/33197115_4356089929',
            'only_matching': True,
        },
        {
            'url': 'https://www.smule.com/recording/billie-happier-than-ever-acoustic/33197115_4356089929/frame',
            'only_matching': True,
        },
        {
            'url': 'https://www.smule.com/recording/billie-happier-than-ever-acoustic/33197115_4356089929/frame/box',
            'only_matching': True,
        },
    ]
    _STATIC_SECRET = 'M=|ZUyMu^-qWb}VL^jJd}Mv)8y%bQWXf>IFBDcJ>%4zg2Ci|telj`dVZ@'

    def _decode_media_url(self, encoded):
        if not encoded:
            return None
        if not encoded.startswith('e:'):
            return url_or_none(encoded)
        try:
            return url_or_none(VideaIE.rc4(base64.b64decode(encoded[2:]), self._STATIC_SECRET))
        except (ValueError, UnicodeDecodeError):
            return None

    def _extract_formats(self, video_id, performance):
        formats = []
        seen = set()
        video_res = parse_resolution(performance.get('video_resolution'))
        for key, format_id in (
            ('media_url', 'm4a'),
            ('visualizer_media_url', 'visualizer'),
            ('video_media_mp4_url', 'mp4'),
            ('video_media_url', 'video'),
        ):
            media_url = self._decode_media_url(performance.get(key))
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)
            if determine_ext(media_url) == 'm3u8':
                m3u8_doc = self._download_webpage(
                    media_url, video_id, 'Downloading m3u8 information', impersonate=True, fatal=False,
                )
                if not m3u8_doc:
                    continue
                hls_fmts, _ = self._parse_m3u8_formats_and_subtitles(
                    m3u8_doc, media_url, ext='mp4', m3u8_id='hls', video_id=video_id,
                )
                for fmt in hls_fmts:
                    fmt.setdefault('impersonate', True)
                formats.extend(hls_fmts)
                continue
            fmt = {
                'url': media_url,
                'format_id': format_id,
                'impersonate': True,
            }
            if key == 'media_url':
                fmt.update(vcodec='none', ext='m4a')
            else:
                fmt.update(video_res)
            formats.append(fmt)
        return formats

    def _extract_creators(self, performance):
        creators = traverse_obj(performance, ('owner', 'handle', {lambda c: [c] if c else []}), default=[])
        creators.extend(traverse_obj(performance, ('other_performers', ..., 'handle', {str}), default=[]))
        return orderedSet(creators)

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        performance = self._download_json(f'https://www.smule.com/p/{video_id}/json', video_id, impersonate=True)
        if not isinstance(performance, dict):
            raise ExtractorError('Unable to extract Smule performance', expected=True)

        if performance.get('private'):
            self.raise_login_required('This performance is private')

        formats = self._extract_formats(video_id, performance)
        if not formats:
            self.raise_no_formats('No public media URL', expected=True, video_id=video_id)

        if not display_id:
            display_id = self._search_regex(
                r'/recording/([^/]+)/', performance.get('web_url') or '', 'display id', default=None,
            )

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'impersonate': True,
            'creators': self._extract_creators(performance),
            **traverse_obj(
                performance,
                {
                    'title': ('title', {str}),
                    'description': ('message', {str}),
                    'timestamp': ('created_at', {parse_iso8601}),
                    'duration': ('song_length', {int_or_none}),
                    'thumbnail': ('cover_url', {url_or_none}),
                    'view_count': ('stats', 'total_listens', {int_or_none}),
                    'like_count': ('stats', 'total_loves', {int_or_none}),
                    'comment_count': ('stats', 'total_comments', {int_or_none}),
                    'artists': ('artist', {str}, filter, all),
                    'channel': ('owner', 'handle', {str}),
                    'channel_id': ('owner', 'account_id', {str_or_none}),
                    'channel_url': ('owner', 'url', {lambda p: urljoin('https://www.smule.com', p)}),
                    'channel_is_verified': ('owner', 'is_verified', {bool}),
                },
            ),
        }
