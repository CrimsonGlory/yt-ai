from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    parse_duration,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class VideasIE(InfoExtractor):
    _UUID_RE = r'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}'
    _VALID_URL = rf'''(?x)
        https?://(?:www\.)?app\.videas\.fr/
        (?:v/|embed/(?:media/(?:uid/)?)?)?
        (?P<id>{_UUID_RE})
    '''
    _EMBED_REGEX = [
        rf'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://(?:www\.)?app\.videas\.fr/(?:v/|embed/)(?:media/(?:uid/)?)?(?:{_UUID_RE})[^"\']*)\1',
    ]
    _TESTS = [{
        'url': 'https://app.videas.fr/v/7dde6333-0506-4d95-a2d7-312d4188a5af/',
        'md5': '1a693a728bbd51d7cc7d5d7688a23c39',
        'info_dict': {
            'id': '8a229ff7-44a2-41ab-92ab-b5c94e41c659',
            'ext': 'mp4',
            'display_id': '7dde6333-0506-4d95-a2d7-312d4188a5af',
            'title': '10月課程新.mp4',
            'description': '',
            'duration': 9017.0,
            'thumbnail': r're:https?://cdn\.videas\.fr/.+',
            'timestamp': 1675236880,
            'upload_date': '20230201',
        },
        'params': {
            # fMP4 HLS: native --test only fetches the EXT-X-MAP init segment
            'external_downloader': 'ffmpeg',
        },
    }, {
        'url': 'https://app.videas.fr/embed/7dde6333-0506-4d95-a2d7-312d4188a5af/',
        'only_matching': True,
    }, {
        'url': 'https://app.videas.fr/7dde6333-0506-4d95-a2d7-312d4188a5af/',
        'only_matching': True,
    }, {
        'url': 'https://app.videas.fr/embed/media/uid/8a229ff7-44a2-41ab-92ab-b5c94e41c659/',
        'only_matching': True,
    }, {
        'url': 'https://app.videas.fr/embed/media/8a229ff7-44a2-41ab-92ab-b5c94e41c659/',
        'only_matching': True,
    }]

    def _extract_media(self, media, data, display_id, webpage):
        video_id = traverse_obj(media, ('uid', {str})) or display_id
        src = traverse_obj(media, ('src', {url_or_none}))
        if not src:
            return None

        subtitles = {}
        for sub in traverse_obj(media, ('subtitles', ..., {dict})) or []:
            sub_url = url_or_none(sub.get('file'))
            if not sub_url:
                continue
            lang = sub.get('language_code') or 'und'
            subtitles.setdefault(lang, []).append({'url': sub_url})

        ext = determine_ext(src)
        if ext == 'm3u8':
            formats, m3u8_subs = self._extract_m3u8_formats_and_subtitles(
                src, video_id, 'mp4', m3u8_id='hls')
            self._merge_subtitles(m3u8_subs, target=subtitles)
        else:
            formats = [{'url': src}]

        chapters = []
        for chapter in traverse_obj(media, ('chapters', ..., {dict})) or []:
            start = parse_duration(chapter.get('time'))
            if start is None:
                continue
            chapters.append({
                'start_time': start,
                'title': chapter.get('name') or '',
            })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': (traverse_obj(media, ('name', {str}))
                      or traverse_obj(data, ('metadata', 'title', {str}))
                      or self._og_search_title(webpage, default=None)),
            'description': clean_html(
                traverse_obj(media, ('description', {str}))
                or traverse_obj(data, ('metadata', 'description', {str}))),
            'thumbnail': (
                traverse_obj(data, ('metadata', 'thumbnail', 'image', {url_or_none}))
                or self._og_search_thumbnail(webpage, default=None)),
            'duration': (float_or_none(media.get('duration'))
                         or traverse_obj(data, ('metadata', 'duration', {float_or_none}))),
            'timestamp': unified_timestamp(media.get('created_at')),
            'formats': formats,
            'subtitles': subtitles,
            'chapters': chapters or None,
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        embed_url = url if '/embed/' in url else f'https://app.videas.fr/embed/{display_id}/'
        webpage = self._download_webpage(embed_url, display_id)

        data = self._search_json(
            r'<script[^>]+\bid=["\']data-embed["\'][^>]*>',
            webpage, 'embed data', display_id)

        medias = traverse_obj(data, ('medias', lambda _, v: url_or_none(v.get('src'))))
        if not medias:
            raise ExtractorError('No playable media found', expected=True)

        entries = []
        for media in medias:
            entry = self._extract_media(media, data, display_id, webpage)
            if entry:
                entries.append(entry)

        if not entries:
            raise ExtractorError('No playable media found', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, display_id, traverse_obj(data, ('metadata', 'title', {str})))
