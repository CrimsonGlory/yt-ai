import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    merge_dicts,
    orderedSet,
    strip_or_none,
    url_or_none,
    urljoin,
)


class PerverzijaIE(InfoExtractor):
    IE_DESC = 'Perverzija'
    _VALID_URL = (
        r'https?://(?:www\.)?tube\.perverzija\.com/'
        r'(?!(?:studio(?:s)?|stars?|tags?|featured-scenes|vr|full-movie|'
        r'page|search|author|feed|comments|your-favourite-videos|'
        r'wp-(?:json|content|admin|includes))(?:/|$|[?#]))'
        r'(?P<id>[^/?#]+)/?(?:[?#]|$)'
    )
    _XTREME_RE = (
        r'https?://(?P<host>[\w.-]+\.xtremestream\.(?:xyz|co|cc))/'
        r'player/index\.php\?data=(?P<data>[0-9a-fA-F]+)'
    )
    _TESTS = [
        {
            'url': 'https://tube.perverzija.com/fakehuboriginals-tru-kait-the-fertility-clinic/',
            'md5': 'ef5385863d41e25186ad165da1cd6d42',
            'info_dict': {
                'id': 'fakehuboriginals-tru-kait-the-fertility-clinic',
                'ext': 'mp4',
                'title': 'FakeHubOriginals – Tru Kait – The Fertility Clinic',
                'description': 'md5:53165f2376f6845a350a36d7d115b408',
                'thumbnail': r're:https://tube\.perverzija\.com/wp-content/uploads/.+\.(?:jpe?g|png)',
                'duration': 1451,
                'timestamp': 1659733316,
                'upload_date': '20220805',
                'uploader': 'Perverzija.com',
                'age_limit': 18,
            },
            'params': {'fixup': 'never'},
        },
        {
            'url': 'https://www.tube.perverzija.com/fakehuboriginals-tru-kait-the-fertility-clinic/',
            'only_matching': True,
        },
        {
            'url': 'https://tube.perverzija.com/missax-liz-jordan-shes-downstairs/',
            'only_matching': True,
        },
    ]

    def _extract_xtremestream(self, webpage, video_id, referer):
        matches = list(re.finditer(self._XTREME_RE, webpage))
        if not matches:
            return [], {}

        data = matches[0].group('data')
        hosts = orderedSet(m.group('host') for m in matches)
        xs_host = self._search_regex(
            r'data-xtremestream=(["\'])(?P<host>[^"\']+)\1', webpage, 'xtremestream host', default=None, group='host',
        )
        if xs_host:
            hosts.append(xs_host if '.' in xs_host else f'{xs_host}.xtremestream.xyz')

        for host in hosts:
            player_url = f'https://{host}/player/index.php?data={data}'
            player = self._download_webpage(
                player_url,
                video_id,
                note=f'Downloading XtremeStream player ({host})',
                errnote=False,
                fatal=False,
                headers={'Referer': referer},
            )
            if not player:
                continue
            loader = self._search_regex(r'm3u8_loader_url\s*=\s*`([^`]+)`', player, 'm3u8 loader', default=None)
            xs_id = self._search_regex(r'var\s+video_id\s*=\s*`([^`]+)`', player, 'xtremestream id', default=data)
            hls_candidates = []
            if loader:
                hls_candidates.append(urljoin(player_url, loader) + xs_id)
            hls_candidates.append(f'https://{host}/player/xs1.php?data={data}')
            headers = {'Referer': player_url}
            for hls_url in orderedSet(hls_candidates):
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                    hls_url, video_id, 'mp4', m3u8_id='hls', headers=headers, fatal=False,
                )
                if formats:
                    for fmt in formats:
                        fmt.setdefault('http_headers', {}).update(headers)
                    return formats, subtitles
        return [], {}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        formats, subtitles = self._extract_xtremestream(webpage, video_id, url)
        if not formats:
            raise ExtractorError('No video sources found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)

        title = strip_or_none(
            self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None),
        ) or self._og_search_title(webpage, default=None)
        if title:
            title = re.sub(r'^\s*Watch\s+', '', title)
            title = re.sub(r'\s*\|\s*Perverzija\.com\s*$', '', title).strip() or title

        return merge_dicts(
            json_ld,
            {
                'id': video_id,
                'title': title,
                'description': self._og_search_description(webpage, default=None),
                'thumbnail': url_or_none(self._og_search_thumbnail(webpage, default=None)),
                'age_limit': 18,
                'formats': formats,
                'subtitles': subtitles,
            },
        )
