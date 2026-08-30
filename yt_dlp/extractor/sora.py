import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    qualities,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class SoraIE(InfoExtractor):
    IE_NAME = 'sora'
    IE_DESC = 'Sora'
    _VALID_URL = r'https?://(?:www\.)?(?:sora\.chatgpt\.com|sora\.com)/p/(?P<id>s_[0-9a-fA-F]+)'
    _TESTS = [{
        'url': 'https://sora.chatgpt.com/p/s_68dc4b85a408819185372cd68c5a5cfc',
        'md5': 'd9274869e5ffa566c0343800e0e9baa4',
        'info_dict': {
            'id': 's_68dc4b85a408819185372cd68c5a5cfc',
            'ext': 'mp4',
            'title': '@sama starring in a power of war mobile ad, he is in medival rome. super cliche ad of something thinking he has lower power, but the @sama says "BUT I HAVE 6 MILLION POWER", make a super cliche exaggerated ad of this',
            'description': 'md5:e40d1193338be39b8d2b5078a09798fa',
            'thumbnail': r're:https://videos\.openai\.com/.+',
            'duration': 9.4,
            'timestamp': 1759267717,
            'upload_date': '20250930',
            'like_count': int,
            'view_count': int,
            'comment_count': int,
            'repost_count': int,
            'uploader': 'gabriel',
            'uploader_id': 'user-Bz2Xh0ulS68ASnl2ao82493X',
            'uploader_url': 'https://sora.chatgpt.com/profile/gabriel',
            'channel': 'gabriel',
            'channel_id': 'user-Bz2Xh0ulS68ASnl2ao82493X',
            'channel_url': 'https://sora.chatgpt.com/profile/gabriel',
            'width': 352,
            'height': 640,
        },
    }, {
        'url': 'https://sora.com/p/s_68dc4b85a408819185372cd68c5a5cfc',
        'only_matching': True,
    }, {
        'url': 'https://www.sora.com/p/s_68dc292e01908191bb065eda890e5aed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parsed = urllib.parse.urlparse(url)
        origin = f'{parsed.scheme}://{parsed.netloc}'
        data = self._download_json(
            f'{origin}/backend/project_y/post/{video_id}', video_id,
            impersonate=True, headers={
                'Accept': 'application/json',
                'Origin': origin,
                'Referer': f'{origin}/p/{video_id}',
            })

        post = traverse_obj(data, ('post', {dict}))
        if not post:
            raise ExtractorError('Unable to extract post data', expected=True)
        if post.get('tombstoned_at'):
            raise ExtractorError('This post has been deleted', expected=True)
        if traverse_obj(post, ('permissions', 'can_read')) is False:
            self.raise_login_required('This post is private')

        formats, seen = [], set()
        quality = qualities(('ld', 'md', 'watermark', 'source', 'no_watermark'))

        def add_format(media_url, format_id, extra=None):
            media_url = url_or_none(media_url)
            if not media_url or media_url in seen:
                return
            seen.add(media_url)
            fmt = {
                'url': media_url,
                'ext': 'mp4',
                'format_id': format_id,
                'quality': quality(format_id),
            }
            if extra:
                fmt.update(extra)
            formats.append(fmt)

        attachment = None
        for att in traverse_obj(post, ('attachments', ..., {dict})) or []:
            extra = traverse_obj(att, {
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'duration': ('duration_s', {float_or_none}),
            })
            encodings = traverse_obj(att, ('encodings', {dict})) or {}
            before = len(formats)
            add_format(traverse_obj(encodings, ('source', 'path')), 'source', {
                **extra,
                **traverse_obj(encodings, ('source', {
                    'filesize': ('size', {int_or_none}),
                    'duration': ('duration_secs', {float_or_none}),
                })),
            })
            add_format(traverse_obj(encodings, ('source_wm', 'path')), 'watermark', {
                **extra,
                **traverse_obj(encodings, ('source_wm', {
                    'filesize': ('size', {int_or_none}),
                    'duration': ('duration_secs', {float_or_none}),
                })),
            })
            add_format(traverse_obj(att, ('download_urls', 'no_watermark')), 'no_watermark', extra)
            add_format(traverse_obj(att, ('download_urls', 'watermark')), 'watermark', extra)
            add_format(att.get('downloadable_url') or att.get('url'), 'source', extra)
            for key in ('md', 'ld'):
                add_format(traverse_obj(encodings, (key, 'path')), key, {
                    **extra,
                    **traverse_obj(encodings, (key, {
                        'filesize': ('size', {int_or_none}),
                    })),
                })
            if len(formats) > before and not attachment:
                attachment = att

        if not formats:
            if traverse_obj(post, ('attachments', ..., 'output_blocked', {bool}, any)):
                raise ExtractorError('This video is blocked', expected=True)
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        subtitles = {}
        for key, ext in (('vtt_url', 'vtt'), ('srt_url', 'srt')):
            sub_url = traverse_obj(post, (key, {url_or_none}))
            if sub_url:
                subtitles.setdefault('en', []).append({'url': sub_url, 'ext': ext})

        username = traverse_obj(data, ('profile', 'username', {str}))
        title = traverse_obj(post, ('text', {strip_or_none})) or (
            f'{username} on Sora' if username else video_id)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(post, {
                'description': ('text', {strip_or_none}),
                'timestamp': ('posted_at', {int_or_none}),
                'like_count': ('like_count', {int_or_none}),
                'view_count': ('view_count', {int_or_none}),
                'comment_count': ('reply_count', {int_or_none}),
                'repost_count': ('repost_count', {int_or_none}),
            }),
            **traverse_obj(attachment, {
                'duration': (('duration_s', ('encodings', 'source', 'duration_secs')), {float_or_none}, any),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'thumbnail': ('encodings', 'thumbnail', 'path', {url_or_none}),
            }),
            **traverse_obj(data, {
                'uploader': ('profile', ('display_name', 'username'), {str}, any),
                'uploader_id': ('profile', 'user_id', {str}),
                'uploader_url': ('profile', 'permalink', {url_or_none}),
                'channel': ('profile', ('display_name', 'username'), {str}, any),
                'channel_id': ('profile', 'user_id', {str}),
                'channel_url': ('profile', 'permalink', {url_or_none}),
            }),
        }
