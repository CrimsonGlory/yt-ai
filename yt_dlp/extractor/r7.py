from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class R7IE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'''(?x)
                        https?://
                        (?:
                            (?:[a-zA-Z]+)\.r7\.com(?:/[^/]+)+/idmedia/|
                            noticias\.r7\.com(?:/[^/]+)+/[^/]+-|
                            player\.r7\.com/video/i/
                        )
                        (?P<id>[\da-f]{24})
                    '''
    _TESTS = [{
        'url': 'http://player.r7.com/video/i/54e7050b0cf2ff57e0279389',
        'info_dict': {
            'id': '54e7050b0cf2ff57e0279389',
            'ext': 'mp4',
            'title': 'Policiais humilham suspeito à beira da morte: Morre com dignidade',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'duration': 98,
            'view_count': int,
            'timestamp': 1424426251,
            'upload_date': '20150220',
        },
    }, {
        'url': 'http://videos.r7.com/policiais-humilham-suspeito-a-beira-da-morte-morre-com-dignidade-/idmedia/54e7050b0cf2ff57e0279389.html',
        'md5': '403c4e393617e8e8ddc748978ee8efde',
        'info_dict': {
            'id': '54e7050b0cf2ff57e0279389',
            'ext': 'mp4',
            'title': 'Policiais humilham suspeito à beira da morte: "Morre com dignidade"',
            'description': 'md5:01812008664be76a6479aa58ec865b72',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 98,
            'like_count': int,
            'view_count': int,
        },
        'skip': 'video gone',
    }, {
        'url': 'http://esportes.r7.com/videos/cigano-manda-recado-aos-fas/idmedia/4e176727b51a048ee6646a1b.html',
        'only_matching': True,
    }, {
        'url': 'http://noticias.r7.com/record-news/video/representante-do-instituto-sou-da-paz-fala-sobre-fim-do-estatuto-do-desarmamento-5480fc580cf2285b117f438d/',
        'only_matching': True,
    }, {
        'url': 'http://player.r7.com/video/i/54e7050b0cf2ff57e0279389?play=true&video=http://vsh.r7.com/54e7050b0cf2ff57e0279389/ER7_RE_BG_MORTE_JOVENS_570kbps_2015-02-2009f17818-cc82-4c8f-86dc-89a66934e633-ATOS_copy.mp4&linkCallback=http://videos.r7.com/policiais-humilham-suspeito-a-beira-da-morte-morre-com-dignidade-/idmedia/54e7050b0cf2ff57e0279389.html&thumbnail=http://vtb.r7.com/ER7_RE_BG_MORTE_JOVENS_570kbps_2015-02-2009f17818-cc82-4c8f-86dc-89a66934e633-thumb.jpg&idCategory=192&share=true&layout=full&full=true',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            f'https://player.r7.com/video/i/{video_id}', video_id)

        metadata = self._search_json(
            r'\bmetadata=\'', webpage, 'metadata', video_id, default={})

        formats, subtitles = [], {}
        seen_urls = set()
        for entry in self._parse_html5_media_entries(
                f'https://player.r7.com/video/i/{video_id}', webpage, video_id,
                m3u8_id='hls') or []:
            for fmt in entry.get('formats') or []:
                fmt_url = fmt.get('url')
                if not fmt_url or 'amp_video_error' in fmt_url or fmt_url in seen_urls:
                    continue
                seen_urls.add(fmt_url)
                formats.append(fmt)
            entry_url = entry.get('url')
            if entry_url and 'amp_video_error' not in entry_url and entry_url not in seen_urls:
                seen_urls.add(entry_url)
                formats.append({'url': entry_url})
            subtitles = self._merge_subtitles(subtitles, entry.get('subtitles') or {})

        if not formats:
            raise ExtractorError('No media found', expected=True)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles or None,
            'thumbnail': url_or_none(self._search_regex(
                r'\bposter=["\']([^"\']+)', webpage, 'poster', default=None)),
            **traverse_obj(metadata, {
                'title': ('title', {clean_html}),
                'duration': ('duration', {lambda v: int_or_none(v, scale=1000)}),
                'view_count': ('views', {int_or_none}),
                'timestamp': ('createdDate', {parse_iso8601}),
            }),
        }


class R7ArticleIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:[a-zA-Z]+)\.r7\.com/(?:[^/]+/)+[^/?#&]+-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://noticias.r7.com/jr-24h/boletim-jr-24h/video/homem-morre-apos-tentar-agredir-policial-em-guarulhos-na-grande-sao-paulo-28082026/',
        'md5': 'cd9c62fb6b883d9917f85e86eb6db8e7',
        'info_dict': {
            'id': '6a9162503e4f1250280e6df3',
            'ext': 'mp4',
            'title': 'Homem morre após tentar agredir policial em Guarulhos, na Grande São Paulo',
            'description': 'Agente era namorado da irmã da vítima; que não aceitava o relacionamento dos dois',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'duration': 25,
            'display_id': '28082026',
            'timestamp': 1787913281,
            'upload_date': '20260828',
        },
        'params': {'format': 'best[protocol=https]'},
    }, {
        'url': 'http://tv.r7.com/record-play/balanco-geral/videos/policiais-humilham-suspeito-a-beira-da-morte-morre-com-dignidade-16102015',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if R7IE.suitable(url) else super().suitable(url)

    def _extract_fusion_video(self, video, display_id):
        video_id = (
            traverse_obj(video, ('additional_properties', 'videoId', {str}))
            or video.get('_id') or display_id)
        formats, urls = [], set()
        for stream in traverse_obj(video, ('streams', ..., {dict})):
            stream_url = url_or_none(stream.get('url'))
            if not stream_url or stream_url in urls:
                continue
            urls.add(stream_url)
            stream_type = stream.get('stream_type')
            if stream_type in ('ts', 'hls'):
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            elif stream_type != 'smil':
                formats.append({
                    'format_id': join_nonempty(stream_type, int_or_none(stream.get('bitrate'))),
                    'url': stream_url,
                    'tbr': int_or_none(stream.get('bitrate')),
                    'width': int_or_none(stream.get('width')),
                    'height': int_or_none(stream.get('height')),
                    'filesize': int_or_none(stream.get('filesize')),
                })
        if not formats:
            raise ExtractorError('No media found', expected=True)
        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            **traverse_obj(video, {
                'title': ('headlines', 'basic', {clean_html}),
                'description': (
                    (('description', 'basic'), ('subheadlines', 'basic')), {clean_html}, any),
                'thumbnail': ('promo_image', 'url', {url_or_none}),
                'duration': ('duration', {lambda v: int_or_none(v, scale=1000)}),
                'timestamp': (
                    ('display_date', 'first_publish_date', 'created_date'), {parse_iso8601}, any),
            }),
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        content = self._search_json(
            r'Fusion\.globalContent\s*=', webpage, 'fusion content', display_id, default=None)

        videos = []
        if traverse_obj(content, 'type') == 'video' and content.get('streams'):
            videos.append(content)
        else:
            for item in traverse_obj(content, ('content_elements', ..., {dict})) or []:
                if item.get('type') == 'video' and item.get('streams'):
                    videos.append(item)
            promo = traverse_obj(content, ('promo_items', 'basic', {dict}))
            if traverse_obj(promo, 'type') == 'video' and promo.get('streams'):
                videos.append(promo)

        if len(videos) == 1:
            return self._extract_fusion_video(videos[0], display_id)
        if len(videos) > 1:
            return self.playlist_result(
                [self._extract_fusion_video(video, display_id) for video in videos],
                display_id)

        video_id = self._search_regex(
            r'<div[^>]+(?:id=["\']player-|class=["\']embed["\'][^>]+id=["\'])([\da-f]{24})',
            webpage, 'video id', default=None)
        if video_id:
            return self.url_result(f'https://player.r7.com/video/i/{video_id}', R7IE.ie_key())

        raise ExtractorError('No video found', expected=True)
