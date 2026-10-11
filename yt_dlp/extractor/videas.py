import json

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
    urljoin,
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
            'duration': 9017.0,
            'thumbnail': r're:https?://(?:app|cdn)\.videas\.fr/.+',
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

    def _extract_from_visitor_api(self, webpage, display_id):
        config = self._search_json(
            r'<script[^>]+\bid=["\']videas-embed-config["\'][^>]*>',
            webpage, 'embed config', display_id)
        embed_id = traverse_obj(config, ('embedId', {str})) or display_id
        api_base = (traverse_obj(config, ('apiBaseUrl', {str})) or '/api/visitor/embed').rstrip('/')
        visitor_root = api_base[:-len('/embed')] if api_base.endswith('/embed') else '/api/visitor'
        headers = {}
        opening = traverse_obj(config, ('opening', {str}))
        if opening:
            headers['X-Embed-Opening'] = opening

        embed = self._download_json(
            urljoin('https://app.videas.fr', f'{api_base}/{embed_id}/'),
            display_id, headers=headers)
        playback_token = embed.get('playback_token')
        if not playback_token:
            raise ExtractorError('No playback token in embed data', expected=True)

        entries = []
        for item in traverse_obj(embed, ('items', ..., {dict})) or []:
            asset = item.get('asset') or {}
            asset_id = traverse_obj(asset, ('uid', {str})) or display_id
            playback = self._download_json(
                urljoin('https://app.videas.fr', f'{visitor_root}/playback/info/'),
                asset_id, data=json.dumps({
                    'asset_id': asset_id,
                    'playback_token': playback_token,
                    'session_id': embed.get('session_id'),
                }).encode(), headers={
                    'Content-Type': 'application/json',
                    **headers,
                })
            if traverse_obj(playback, 'blocked'):
                continue
            hls = urljoin(
                'https://app.videas.fr',
                traverse_obj(playback, ('hls_url', 'url', {str})))
            if not hls:
                continue
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls, asset_id, 'mp4', m3u8_id='hls')
            thumbnail = urljoin(
                'https://app.videas.fr',
                traverse_obj(asset, ('thumbnail_url', {str}))
                or traverse_obj(embed, ('thumbnail_url', {str}))) or self._og_search_thumbnail(
                    webpage, default=None)
            entries.append({
                'id': asset_id,
                'display_id': display_id,
                'title': (traverse_obj(item, ('custom_title', {str}))
                          or traverse_obj(asset, ('name', {str}))
                          or traverse_obj(embed, ('name', {str}))
                          or self._og_search_title(webpage, default=None)),
                'description': clean_html(
                    traverse_obj(item, ('custom_description', {str}))
                    or traverse_obj(asset, ('description', {str}))
                    or traverse_obj(embed, ('description', {str}))),
                'thumbnail': thumbnail,
                'duration': float_or_none(asset.get('duration')),
                'formats': formats,
                'subtitles': subtitles,
            })
        return entries, traverse_obj(embed, ('name', {str}))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        embed_url = url if '/embed/' in url else f'https://app.videas.fr/embed/{display_id}/'
        webpage = self._download_webpage(embed_url, display_id)

        data = self._search_json(
            r'<script[^>]+\bid=["\']data-embed["\'][^>]*>',
            webpage, 'embed data', display_id, default=None)
        if data:
            medias = traverse_obj(data, ('medias', lambda _, v: url_or_none(v.get('src'))))
            entries = []
            for media in medias or []:
                entry = self._extract_media(media, data, display_id, webpage)
                if entry:
                    entries.append(entry)
            if entries:
                if len(entries) == 1:
                    return entries[0]
                return self.playlist_result(
                    entries, display_id, traverse_obj(data, ('metadata', 'title', {str})))

        entries, title = self._extract_from_visitor_api(webpage, display_id)
        if not entries:
            raise ExtractorError('No playable media found', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, display_id, title)
