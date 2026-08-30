import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    join_nonempty,
    orderedSet,
    parse_iso8601,
    unescapeHTML,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class SponsrIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sponsr\.ru/(?P<project>[\w-]+)/(?P<id>\d+)(?:/(?P<slug>[^/?#]*))?'
    _TESTS = [{
        'url': 'https://sponsr.ru/vpered/114539/Rossiya_stroit_zavod_poluprovodnikov_vkosmose_Eksperiment_nachalsya/?autoplay=1',
        'md5': '5636f06fbada38b8d997cfa9b8c984d7',
        'info_dict': {
            'id': '114539',
            'ext': 'mp4',
            'title': 'Россия строит завод полупроводников в\xa0космосе. Эксперимент начался!',
            'description': 'Россия строит завод полупроводников в\xa0космосе. Эксперимент начался!. О позитивных достижениях России в сфере экономики, науки и о подвигах наших соотечественников',
            'thumbnail': r're:https://(?:media\.sponsr\.ru|[^/]*kinescope).+',
            'duration': 754.66,
            'timestamp': 1758474000,
            'upload_date': '20250921',
            'channel': 'Время - вперёд!',
            'channel_id': 'vpered',
            'channel_url': 'https://sponsr.ru/vpered',
            'uploader': 'Время - вперёд!',
            'uploader_id': 'vpered',
            'uploader_url': 'https://sponsr.ru/vpered',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'tags': ['времявперёд'],
        },
        'params': {'format': 'http-360'},
    }, {
        'url': 'https://sponsr.ru/vpered/113655/Rossiya_zanedelu_megaturbina_novyi_reaktor_sputniki_bespilotnik_idrugie_chudesa_tehniki/?autoplay=1',
        'only_matching': True,
    }, {
        'url': 'https://sponsr.ru/vpered/114539',
        'only_matching': True,
    }]
    _KINESCOPE_RE = r'https?://(?:www\.)?kinescope\.io/(?:embed/)?(?!oembed)(?P<id>[A-Za-z0-9_-]+)'

    def _extract_kinescope(self, kinescope_id, video_id, referer):
        headers = {'Referer': referer}
        webpage = self._download_webpage(
            f'https://kinescope.io/{kinescope_id}', video_id,
            'Downloading Kinescope player', headers=headers)
        if re.search(r'<title>\s*Access forbidden', webpage):
            raise ExtractorError('Kinescope rejected the request', expected=True)

        player = self._search_json(
            r'var\s+playerOptions\s*=', webpage, 'kinescope player options',
            video_id, fatal=False) or {}
        if traverse_obj(player, ('playlist', 0, 'drm')):
            self.report_drm(video_id)

        m3u8_url = traverse_obj(player, (
            'playlist', 0, 'sources', ('hls', 'shakahls'), 'src', {url_or_none}, any))
        if not m3u8_url:
            m3u8_url = url_or_none(unescapeHTML(self._search_regex(
                r'https?://kinescope\.io/[^"\']+/master\.m3u8[^"\']*',
                webpage, 'm3u8 url')))
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', headers=headers)
        formats.extend(self._extract_kinescope_http_formats(formats, video_id, headers))

        return {
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
            **traverse_obj(player, ('playlist', 0, {
                'duration': ('meta', 'duration', {float_or_none}),
                'thumbnail': ('poster', 'src', 'src', {url_or_none}),
            })),
        }

    def _extract_kinescope_http_formats(self, hls_formats, video_id, headers):
        http_formats, seen = [], set()
        for fmt in hls_formats:
            if fmt.get('vcodec') == 'none' or not fmt.get('url'):
                continue
            playlist = self._download_webpage(
                fmt['url'], video_id,
                f'Downloading {fmt.get("format_id", "hls")} media playlist',
                fatal=False, headers=headers)
            mp4_url = url_or_none(unescapeHTML(self._search_regex(
                r'URI="([^"]+\.mp4[^"]*)"', playlist or '', 'mp4 url', default=None)))
            if not mp4_url or mp4_url in seen:
                continue
            seen.add(mp4_url)
            height = fmt.get('height')
            http_formats.append({
                'url': mp4_url,
                'ext': 'mp4',
                'format_id': join_nonempty('http', height),
                'width': fmt.get('width'),
                'height': height,
                'fps': fmt.get('fps'),
                'vcodec': fmt.get('vcodec'),
                'acodec': 'none',
                'http_headers': headers,
            })
        return http_formats

    def _kinescope_ids(self, page_props, post):
        html = unescapeHTML(' '.join(filter(None, (
            page_props.get('formatedVideoContent'),
            traverse_obj(post, ('text', 'text', {str})),
        ))))
        kinescope_ids = orderedSet(re.findall(self._KINESCOPE_RE, html or ''))
        if kinescope_ids:
            return kinescope_ids
        return orderedSet(re.findall(
            r'video_id=([0-9a-fA-F-]{36})',
            ' '.join(traverse_obj(post, ('video_posters', ..., 'iframe_src', {str})) or [])))

    def _real_extract(self, url):
        video_id, project_slug = self._match_valid_url(url).group('id', 'project')
        webpage = self._download_webpage(url, video_id)
        page_props = traverse_obj(
            self._search_nextjs_data(webpage, video_id),
            ('props', 'pageProps', {dict})) or {}
        post = traverse_obj(page_props, ('post', {dict}))
        if not post:
            raise ExtractorError('Unable to extract post data', expected=True)
        if post.get('available') is False or page_props.get('available') is False:
            self.raise_login_required(
                'This post is only available to Sponsr subscribers', method='password')

        kinescope_ids = self._kinescope_ids(page_props, post)
        if not kinescope_ids:
            raise ExtractorError('No video found in this post', expected=True)

        project = traverse_obj(page_props, ('project', {dict})) or {}
        channel_id = traverse_obj(project, ('project_url', {str})) or project_slug
        channel = traverse_obj(project, ('project_title', {str}))
        channel_url = f'https://sponsr.ru/{channel_id}' if channel_id else None
        info = {
            **traverse_obj(post, {
                'title': ('title', {str}),
                'timestamp': ('date', {parse_iso8601}),
                'view_count': ('views', {int_or_none}),
                'like_count': ('cnt_likes', {int_or_none}),
                'comment_count': ('cnt_comments', {int_or_none}),
                'tags': ('tags', ..., 'tag', 'tag_name', {str}),
            }),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': urljoin(
                traverse_obj(page_props, ('mediaURL', {url_or_none})),
                traverse_obj(post, ('image', {str}))),
            'channel': channel,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'uploader': channel,
            'uploader_id': channel_id,
            'uploader_url': channel_url,
        }

        entries = []
        for kinescope_id in kinescope_ids:
            kinescope = self._extract_kinescope(kinescope_id, video_id, url)
            entry = {
                **info,
                **kinescope,
                'id': kinescope_id if len(kinescope_ids) > 1 else video_id,
            }
            if info.get('thumbnail'):
                entry['thumbnail'] = info['thumbnail']
            if not entry.get('duration'):
                entry['duration'] = int_or_none(post.get('duration_video')) or None
            entries.append(entry)

        if len(entries) > 1:
            return self.playlist_result(entries, video_id, info.get('title'))
        return entries[0]
