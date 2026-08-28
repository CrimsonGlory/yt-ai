import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_resolution,
    remove_end,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PornoVoisinesIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?pornovoisines\.com/videos/show/(?P<id>[\da-fA-F]+)/(?P<display_id>[^/?#]+)'

    _TESTS = [{
        'url': 'http://www.pornovoisines.com/videos/show/32698/irogenia-31ans-se-sentait-prete-a-passer-un-grand-cap-dans-sa-sexualite',
        'md5': 'df36eb3401dabaac54f031839bf7da56',
        'info_dict': {
            'id': '32698',
            'display_id': 'irogenia-31ans-se-sentait-prete-a-passer-un-grand-cap-dans-sa-sexualite',
            'ext': 'mp4',
            'title': 'Irogenia, 31ans, se sentait prête à passer un grand cap dans sa sexualité...',
            'description': 'md5:0a1c54508fcc62d9c12021cc28933d12',
            'thumbnail': r're:https?://.*',
            'upload_date': '20260821',
            'timestamp': 1787284800,
            'duration': 2504,
            'view_count': int,
            'categories': list,
            'age_limit': 18,
            'subtitles': {
                'fr': [{'ext': 'vtt'}],
            },
        },
    }, {
        'url': 'https://www.pornovoisines.com/videos/show/6a686495d0d62268d9052bf5/jade-decouvre-la-soumission-et-prend-son-pied',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        info = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        trailer_url = url_or_none(info.pop('url', None))
        info.pop('ext', None)

        formats = []
        pack_url = self._search_regex(
            r'''pack-url=(["'])(?P<url>https?://[^"']+)\1''',
            webpage, 'pack url', group='url', default=None)
        pack = {}
        if pack_url:
            pack = self._download_json(pack_url, video_id, 'Downloading player pack')

        for item in traverse_obj(pack, ('sources', 'mp4', lambda _, v: url_or_none(v.get('file')))):
            label = str_or_none(item.get('label'))
            formats.append({
                'url': item['file'],
                'format_id': label,
                'ext': 'mp4',
                **parse_resolution(label),
            })
        if not formats:
            hls_url = traverse_obj(pack, ('sources', 'hls', {url_or_none}))
            if hls_url:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
        if not formats:
            mpd_url = traverse_obj(pack, ('sources', 'dash', {url_or_none}))
            if mpd_url:
                formats.extend(self._extract_mpd_formats(
                    mpd_url, video_id, mpd_id='dash', fatal=False))

        if not formats and trailer_url:
            formats.append({
                'url': trailer_url,
                'ext': 'mp4',
                'format_id': 'trailer',
            })
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        vtt = traverse_obj(pack, ('vtt', {url_or_none}))
        categories = traverse_obj(
            list(self._yield_json_ld(webpage, video_id, default=[])),
            (..., '@graph', ..., 'keywords', ..., {str}))
        if not categories:
            categories = [c.strip() for c in re.findall(
                r'<li class="content-detail__tag">\s*<a[^>]+href="/categorie/[^"]+"[^>]*>([^<]+)',
                webpage) if c.strip()]
        view_count = int_or_none(re.sub(r'\D', '', self._search_regex(
            r'([\d\s\u00a0\u202f]+)\s*vues', webpage, 'view count', default='') or '') or None)

        return {
            **info,
            'id': video_id,
            'display_id': display_id,
            'title': info.get('title') or remove_end(
                self._og_search_title(webpage), ' | Pornovoisines'),
            'description': info.get('description') or self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage) or traverse_obj(
                info, ('thumbnails', 0, 'url', {url_or_none})),
            'formats': formats,
            'subtitles': {'fr': [{'url': vtt, 'ext': 'vtt'}]} if vtt else None,
            'categories': categories or None,
            'view_count': view_count,
            'age_limit': 18,
        }
