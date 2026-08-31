import re

from .common import InfoExtractor
from ..networking.impersonate import ImpersonateTarget
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    orderedSet,
    unescapeHTML,
    unified_timestamp,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class TelegraphIE(InfoExtractor):
    IE_DESC = 'The Telegraph'
    _VALID_URL = r'https?://(?:www\.)?telegraph\.co\.uk/(?:[^/?#]+/)+(?P<id>[^/?#]+)/?'
    _TESTS = [
        {
            'url': 'https://www.telegraph.co.uk/us/news/2026/08/31/flash-flooding-grand-canyon-national-park-arizona/',
            'md5': 'a0a995ac9b1dffc3ff482452af359476',
            'info_dict': {
                'id': 'bbd4e244',
                'ext': 'mp4',
                'title': 'Grand Canyon Flash Flooding',
                'description': 'md5:1260bca4e34b93385cf24c01ccac63e0',
                'thumbnail': r're:https?://cf\.eip\.telegraph\.co\.uk/.+',
                'duration': 16.033333,
                'timestamp': 1788139980,
                'upload_date': '20260831',
                'uploader': 'The Telegraph',
                'creators': ['Kelly-Anne Taylor'],
            },
        },
        {
            'url': 'https://www.telegraph.co.uk/world-news/2024/06/28/biden-trump-first-presidential-debate-cnn-key-moments/',
            'info_dict': {
                'id': 'biden-trump-first-presidential-debate-cnn-key-moments',
                'title': 'Five key moments from the Biden Trump debate',
                'description': str,
            },
            'playlist_mincount': 5,
            'params': {'skip_download': True},
        },
        {
            'url': 'https://www.telegraph.co.uk/world-news/2026/08/30/six-dead-ferry-capsizes-off-cyprus-coast/',
            'only_matching': True,
        },
    ]
    _IMPERSONATE_TARGET = ImpersonateTarget('edge', '101')

    def _call_with_impersonate(self, *args, **kwargs):
        kwargs.setdefault('impersonate', self._IMPERSONATE_TARGET)
        kwargs.setdefault('require_impersonation', True)
        return self._download_webpage(*args, **kwargs)

    def _extract_particle(self, url, display_id):
        webpage = self._call_with_impersonate(url, display_id, 'Downloading particle iframe', fatal=False)
        if not webpage:
            return

        if 'window.videos' not in webpage:
            return
        videos = self._search_json(
            r'window\.videos\s*=', webpage, 'videos', display_id, contains_pattern=r'\[(?s:.+)\]', fatal=False,
        )
        if not videos:
            return

        settings = (
            self._search_json(r'window\.videoSettings\s*=', webpage, 'video settings', display_id, fatal=False) or {}
            if 'window.videoSettings' in webpage
            else {}
        )

        formats, video_id, duration, thumbnail = [], display_id, None, None
        for rendition in videos:
            rendition_url = url_or_none(rendition.get('url'))
            if not rendition_url or rendition.get('status') not in (None, 'ready'):
                continue

            thumbnail = thumbnail or traverse_obj(
                rendition, (('poster', 'thumbnail', ('posters', ('high', 'low'))), {url_or_none}, any),
            )
            if rendition.get('adaptive') or determine_ext(rendition_url) == 'm3u8':
                m3u8_doc = self._call_with_impersonate(
                    rendition_url, display_id, 'Downloading m3u8 information', fatal=False,
                )
                if m3u8_doc:
                    hls_fmts, _ = self._parse_m3u8_formats_and_subtitles(
                        m3u8_doc, rendition_url, 'mp4', m3u8_id='hls', fatal=False,
                    )
                    for fmt in hls_fmts:
                        fmt['impersonate'] = self._IMPERSONATE_TARGET
                    formats.extend(hls_fmts)
                duration = duration or float_or_none(traverse_obj(rendition, ('data', 0, 'duration')), scale=1000)
                fallback = url_or_none(rendition.get('fallback'))
                if fallback:
                    formats.append(
                        {
                            'url': fallback,
                            'ext': determine_ext(fallback, 'mp4'),
                            'format_id': 'http-fallback',
                            'impersonate': self._IMPERSONATE_TARGET,
                        },
                    )
                continue

            media_id = self._search_regex(r'/vid-media/([^/]+)/', rendition_url, 'media id', default=None)
            if media_id:
                video_id = media_id
            video_stream = traverse_obj(
                rendition, ('data', 'streams', lambda _, v: v.get('codec_type') == 'video', any),
            )
            formats.append(
                {
                    'url': rendition_url,
                    'ext': determine_ext(rendition_url, 'mp4'),
                    'format_id': 'http-orig',
                    'quality': 1,
                    **traverse_obj(
                        video_stream,
                        {
                            'width': ('width', {int_or_none}),
                            'height': ('height', {int_or_none}),
                            'vcodec': ('codec_name', {str}),
                        },
                    ),
                    'tbr': float_or_none(traverse_obj(video_stream, 'bit_rate'), scale=1000),
                    'duration': float_or_none(traverse_obj(rendition, ('data', 'format', 'duration'))),
                    'impersonate': self._IMPERSONATE_TARGET,
                },
            )
            duration = duration or float_or_none(traverse_obj(rendition, ('data', 'format', 'duration')))

        if not formats:
            return

        title = (
            unescapeHTML(self._search_regex(r'data-widget-title="([^"]+)"', webpage, 'title', default=None))
            or traverse_obj(settings, ('contentAnalysis', 'classifiedFrom', 'title', {str}))
            or video_id
        )

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': duration,
            'thumbnail': thumbnail,
            'impersonate': self._IMPERSONATE_TARGET,
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._call_with_impersonate(url, display_id)

        entries = []
        for iframe_url in orderedSet(
            re.findall(
                r'<iframe[^>]+src=["\']([^"\']+)',
                webpage,
            ),
        ):
            iframe_url = urljoin(url, iframe_url)
            if 'cf-particle-html.eip.telegraph.co.uk' not in iframe_url:
                continue
            particle_id = self._search_regex(r'/([0-9a-f-]+)\.html', iframe_url, 'particle id', default=display_id)
            entry = self._extract_particle(iframe_url, particle_id)
            if entry:
                entries.append(entry)

        json_ld = self._search_json_ld(webpage, display_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('id', None)
        article_title = self._og_search_title(webpage, default=None) or json_ld.get('title')
        description = self._og_search_description(webpage, default=None) or json_ld.get('description')
        timestamp = json_ld.get('timestamp') or unified_timestamp(
            self._search_regex(r'"datePublished"\s*:\s*"([^"]+)"', webpage, 'timestamp', default=None),
        )
        creators = traverse_obj(
            self._yield_json_ld(webpage, display_id, fatal=False), (..., 'author', ..., 'name', {str}),
        )

        if not entries:
            self.raise_no_formats('No Telegraph videos found', expected=True, video_id=display_id)

        extra = {
            'description': description,
            'uploader': 'The Telegraph',
            'timestamp': timestamp,
        }
        if creators:
            extra['creators'] = creators
        for entry in entries:
            for key, value in extra.items():
                entry.setdefault(key, value)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, display_id, article_title, description)
