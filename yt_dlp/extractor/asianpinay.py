import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    merge_dicts,
    orderedSet,
    parse_duration,
    strip_or_none,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class AsianPinayIE(InfoExtractor):
    IE_DESC = 'AsianPinay'
    _VALID_URL = (
        r'https?://(?:www\.)?asianpinay\.cc/'
        r'(?!(?:categor(?:y|ies)|tags?|page|search|author|feed|comments|'
        r'wp-(?:json|content|admin|includes))(?:/|$|[?#]))'
        r'(?P<id>[^/?#]+)/?(?:[?#]|$)'
    )
    _XTREME_RE = (
        r'https?://(?P<host>[\w.-]+\.xtremestream\.(?:xyz|co|cc))/'
        r'player/index\.php\?data=(?P<data>[0-9a-fA-F]+)'
    )
    _TESTS = [
        {
            'url': 'https://asianpinay.cc/lumiban-sa-klase-para-magkantotan-2/',
            'md5': 'e0a9eecc989799c1eda26f13b8ec9f74',
            'info_dict': {
                'id': 'lumiban-sa-klase-para-magkantotan-2',
                'ext': 'mp4',
                'title': 'Lumiban sa klase para magkantotan',
                'description': 'Lumiban sa klase para magkantotan',
                'thumbnail': r're:https://asianpinay\.cc/wp-content/uploads/.+\.(?:jpe?g|png)',
                'duration': 594,
                'timestamp': 1685019686,
                'upload_date': '20230525',
                'uploader': 'Nami_',
                'age_limit': 18,
            },
            'params': {'fixup': 'never'},
        },
        {
            'url': 'https://www.asianpinay.cc/lumiban-sa-klase-para-magkantotan-2/',
            'only_matching': True,
        },
        {
            'url': 'https://asianpinay.cc/city-girl-2026-tbonx-full-movie-1080p/',
            'only_matching': True,
        },
    ]

    def _extract_embed_url(self, webpage):
        return url_or_none(self._html_search_meta('embedURL', webpage, default=None)) or url_or_none(
            self._search_regex(r'<iframe[^>]+src=["\']?(https?://[^"\'\s>]+)', webpage, 'embed URL', default=None),
        )

    def _extract_xtremestream(self, webpage, embed_url, video_id, referer):
        mobj = re.search(self._XTREME_RE, embed_url or '') or re.search(self._XTREME_RE, webpage)
        if not mobj:
            return [], {}

        data = mobj.group('data')
        hosts = orderedSet(
            (
                mobj.group('host'),
                *re.findall(r'https?://([\w.-]+\.xtremestream\.(?:xyz|co|cc))', webpage),
            ),
        )

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
        embed_url = self._extract_embed_url(webpage)

        formats, subtitles = self._extract_xtremestream(webpage, embed_url, video_id, url)
        if not formats and embed_url:
            ext = determine_ext(embed_url, default_ext=None)
            if ext == 'm3u8':
                headers = {'Referer': url}
                formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                    embed_url, video_id, 'mp4', m3u8_id='hls', headers=headers, fatal=False,
                )
                for fmt in formats:
                    fmt.setdefault('http_headers', {}).update(headers)
            elif ext in ('mp4', 'webm', 'mov'):
                formats = [
                    {
                        'url': embed_url,
                        'ext': ext,
                        'http_headers': {'Referer': url},
                    },
                ]

        if not formats:
            raise ExtractorError('No video sources found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)

        title = strip_or_none(
            self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None),
        ) or self._og_search_title(webpage, default=None)
        if title:
            title = re.sub(r'\s*-\s*AsianPinay\s*$', '', title).strip() or title

        return merge_dicts(
            json_ld,
            {
                'id': video_id,
                'title': title,
                'description': self._og_search_description(webpage, default=None),
                'thumbnail': (
                    url_or_none(self._html_search_meta('thumbnailUrl', webpage, default=None))
                    or self._og_search_thumbnail(webpage, default=None)
                ),
                'duration': parse_duration(self._html_search_meta('duration', webpage, default=None)),
                'timestamp': unified_timestamp(self._html_search_meta('uploadDate', webpage, default=None)),
                'uploader': strip_or_none(self._html_search_meta('author', webpage, default=None)),
                'age_limit': 18,
                'formats': formats,
                'subtitles': subtitles,
            },
        )
