import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    parse_age_limit,
    remove_end,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class GiphyIE(InfoExtractor):
    IE_NAME = 'giphy'
    IE_DESC = 'GIPHY'
    _VALID_URL = (
        r'https?://(?:www\.)?giphy\.com/(?:gifs|stickers|clips|embed)/(?:[^/?#]*-)?(?P<id>[\w]+)',
        r'https?://i(?:s\d*)?\.giphy\.com/(?P<id>[\w]+)\.(?:gif|mp4|webp|gifv)',
        r'https?://media\d*\.giphy\.com/media/(?:v1\.[^/]+/)?(?P<id>[\w]+)/',
    )
    _TESTS = [
        {
            'url': 'https://giphy.com/gifs/allsxxingeyes-laugh-laughing-spit-XHeLeuirRbwptHhSWd',
            'md5': 'e9709f7ab47a3674c5e9086189745fd7',
            'info_dict': {
                'id': 'XHeLeuirRbwptHhSWd',
                'ext': 'mp4',
                'title': 'Meme Lol GIF by ALL SEEING EYES',
                'thumbnail': r're:https?://media\d*\.giphy\.com/media/.+',
                'uploader': 'ALL SEEING EYES',
                'uploader_id': 'allsxxingeyes',
                'uploader_url': r're:https?://giphy\.com/.+',
                'timestamp': 1595454985,
                'upload_date': '20200722',
                'age_limit': 0,
                'tags': list,
                'width': int,
                'height': int,
            },
        },
        {
            'url': 'https://giphy.com/gifs/XHeLeuirRbwptHhSWd',
            'only_matching': True,
        },
        {
            'url': 'https://giphy.com/stickers/playlist-reader-lecteur-QDxWS5wmVvDv6Hi1LH',
            'only_matching': True,
        },
        {
            'url': 'https://giphy.com/clips/therokuchannel-roku-zoeys-extraordinary-playlist-christmas-lsb4tsk8a3mB19MKuS',
            'only_matching': True,
        },
        {
            'url': 'https://giphy.com/embed/XHeLeuirRbwptHhSWd',
            'only_matching': True,
        },
        {
            'url': 'https://i.giphy.com/XHeLeuirRbwptHhSWd.mp4',
            'only_matching': True,
        },
        {
            'url': 'https://media0.giphy.com/media/XHeLeuirRbwptHhSWd/giphy.mp4',
            'only_matching': True,
        },
        {
            'url': 'https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZWZrNmU0d2xiaGxod2JiYzY5am5iMXJjcG82c2l3dnVoNW80NzZudSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/XHeLeuirRbwptHhSWd/giphy.mp4',
            'only_matching': True,
        },
    ]
    _MEDIA_HEADERS = {'Accept': '*/*'}
    _MEDIA_PATH_RE = re.compile(
        r'https?://(?:media\d*\.|i\.)giphy\.com/media/(?:v1\.[^/]+/)?(?P<id>[\w]+)/(?P<file>[^/?#]+)',
    )

    @classmethod
    def _rewrite_media_url(cls, url):
        url = url_or_none(url)
        if not url:
            return None
        m = cls._MEDIA_PATH_RE.match(url)
        if not m:
            return url
        gif_id, filename = m.group('id'), m.group('file')
        if filename in ('giphy.mp4', 'giphy.gif', 'giphy.webp'):
            return f"https://i.giphy.com/{gif_id}.{filename.rsplit('.', 1)[1]}"
        return f'https://media.giphy.com/media/{gif_id}/{filename}'

    def _extract_gif_data(self, webpage, video_id):
        if not webpage:
            return {}
        for m in re.finditer(r'self\.__next_f\.push\(', webpage):
            if not webpage.startswith('[', m.end()):
                continue
            payload = self._parse_json(webpage[m.end() :], video_id, fatal=False, ignore_extra=True)
            if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], str):
                continue
            text = payload[1]
            if f'"id":"{video_id}"' not in text:
                continue
            gif = self._search_json(
                rf'"gif"\s*:\s*(?={{"type":"[^"]+","id":"{re.escape(video_id)}")',
                text,
                'gif data',
                video_id,
                fatal=False,
            )
            if traverse_obj(gif, ('id', {str})) == video_id:
                return gif
        return {}

    def _add_media(self, formats, seen, url, format_id, **kwargs):
        url = self._rewrite_media_url(url)
        if not url or url in seen:
            return
        seen.add(url)
        ext = determine_ext(url, kwargs.pop('ext', None) or 'mp4')
        fmt = {
            'url': url,
            'format_id': format_id,
            'ext': ext,
            'http_headers': self._MEDIA_HEADERS,
            **kwargs,
        }
        if ext in ('gif', 'webp'):
            fmt.setdefault('acodec', 'none')
            fmt.setdefault('preference', -10 if ext == 'gif' else -5)
            if ext == 'gif':
                fmt.setdefault('vcodec', 'gif')
        formats.append(fmt)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://giphy.com/gifs/{video_id}', video_id, fatal=False) or ''
        gif = self._extract_gif_data(webpage, video_id)

        ld = {}
        for item in self._yield_json_ld(webpage, video_id, fatal=False) or []:
            if isinstance(item, dict) and item.get('@type') == 'Article':
                ld = item
                break

        formats, seen = [], set()
        for format_id, asset in traverse_obj(gif, ('video', 'assets', {dict.items}, ...)):
            if not isinstance(asset, dict):
                continue
            self._add_media(
                formats,
                seen,
                asset.get('url'),
                str(format_id),
                width=int_or_none(asset.get('width')),
                height=int_or_none(asset.get('height')),
            )

        for rendition, info in traverse_obj(gif, ('images', {dict.items}, ...)):
            if rendition not in ('original', 'original_mp4', 'hd', 'source') or not isinstance(info, dict):
                continue
            width = int_or_none(info.get('width'))
            height = int_or_none(info.get('height'))
            if rendition == 'original':
                self._add_media(
                    formats,
                    seen,
                    info.get('mp4'),
                    'original-mp4',
                    width=width,
                    height=height,
                    filesize=int_or_none(info.get('mp4_size')),
                )
                self._add_media(
                    formats,
                    seen,
                    info.get('webp'),
                    'original-webp',
                    width=width,
                    height=height,
                    filesize=int_or_none(info.get('webp_size')),
                )
                self._add_media(
                    formats,
                    seen,
                    info.get('url'),
                    'original-gif',
                    width=width,
                    height=height,
                    filesize=int_or_none(info.get('size')),
                )
            else:
                self._add_media(
                    formats,
                    seen,
                    info.get('mp4') or info.get('url'),
                    rendition,
                    width=width,
                    height=height,
                    filesize=int_or_none(info.get('mp4_size') or info.get('size')),
                )

        if not formats:
            self._add_media(formats, seen, f'https://i.giphy.com/{video_id}.mp4', 'mp4')
            self._add_media(formats, seen, f'https://i.giphy.com/{video_id}.webp', 'webp')
            self._add_media(formats, seen, f'https://i.giphy.com/{video_id}.gif', 'gif')

        thumbnails = []
        for thumb_id, key in (('still', 'original_still'), ('480w_still', '480w_still')):
            thumb = traverse_obj(gif, ('images', key, {dict})) or {}
            thumb_url = self._rewrite_media_url(traverse_obj(thumb, ('url', {url_or_none})))
            if thumb_url:
                thumbnails.append(
                    {
                        'id': thumb_id,
                        'url': thumb_url,
                        'http_headers': self._MEDIA_HEADERS,
                        'width': traverse_obj(thumb, ('width', {int_or_none})),
                        'height': traverse_obj(thumb, ('height', {int_or_none})),
                    },
                )
        if not thumbnails:
            still = self._rewrite_media_url(f'https://media.giphy.com/media/{video_id}/giphy_s.gif')
            if still:
                thumbnails.append(
                    {'id': 'still', 'url': still, 'http_headers': self._MEDIA_HEADERS},
                )

        title = (
            traverse_obj(gif, ('title', {str}))
            or traverse_obj(ld, ('headline', {str}))
            or remove_end(self._og_search_title(webpage, default=''), ' - Find & Share on GIPHY')
            or video_id
        )

        return {
            'id': video_id,
            'title': title,
            'description': traverse_obj(gif, ('alt_text', {str})) or None,
            'thumbnail': traverse_obj(thumbnails, (0, 'url', {url_or_none})),
            'thumbnails': thumbnails or None,
            'uploader': traverse_obj(gif, ('user', 'display_name', {str})) or traverse_obj(gif, ('username', {str})),
            'uploader_id': traverse_obj(gif, ('user', 'username', {str})) or traverse_obj(gif, ('username', {str})),
            'uploader_url': traverse_obj(gif, ('user', 'profile_url', {url_or_none})),
            'timestamp': unified_timestamp(
                traverse_obj(gif, ('import_datetime', {str})) or traverse_obj(ld, ('datePublished', {str})),
            ),
            'duration': float_or_none(traverse_obj(gif, ('video', 'duration'))),
            'age_limit': parse_age_limit(traverse_obj(gif, ('rating', {str}))),
            'tags': traverse_obj(gif, ('tags', ..., {str})) or None,
            'formats': formats,
        }
