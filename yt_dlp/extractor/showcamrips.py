import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    orderedSet,
    parse_duration,
    unified_strdate,
    urljoin,
)


class ShowcamripsIE(InfoExtractor):
    IE_NAME = 'showcamrips'
    IE_DESC = 'showcamrips.com'
    _VALID_URL = r'https?://(?:www\.)?showcamrips\.com/show-cam-sex-movies/(?P<id>\d+)(?:-[^/?#]+)?(?:\.html)?'
    _TESTS = [{
        'url': 'https://www.showcamrips.com/show-cam-sex-movies/2235904-rooxxyy-chaturbate-webcam-rip-20261112-040533.html',
        'md5': '7d2a8dfc5af406aae13672d2b3620edc',
        'info_dict': {
            'id': '2235904',
            'ext': 'mp4',
            'title': 'Rooxxyy_ Couple Chaturbate: Webcam Show web cam Showcamrips 2026.11.12 -> 00:35:36',
            'thumbnail': 'https://www.showpicmoi.com/img/2235904.jpg',
            'uploader': 'rooxxyy_',
            'uploader_url': 'https://www.showcamrips.com/model/en/rooxxyy_/',
            'upload_date': '20261112',
            'duration': 2136,
            'age_limit': 18,
            'categories': ['Couple'],
            'tags': ['Chaturbate'],
        },
    }, {
        'url': 'https://www.showcamrips.com/show-cam-sex-movies/633200-leilatinytraveler-stripchat-webcam-rip-20240327-090824.html',
        'skip': 'video gone',
        'md5': '674ec03168fdff98f1255128e4d81764',
        'info_dict': {
            'id': '633200',
            'ext': 'mp4',
            'title': 'Leilatinytraveler Couple Stripchat: Webcam Show web cam Showcamrips 2024.03.27 -> 00:19:34',
            'thumbnail': 'https://www.showpicmoi.com/img/633200.jpg',
            'uploader': 'leilatinytraveler',
            'uploader_url': 'https://www.showcamrips.com/model/en/leilatinytraveler/',
            'upload_date': '20240327',
            'duration': 1174,
            'age_limit': 18,
            'categories': ['Couple'],
            'tags': ['Stripchat'],
        },
    }, {
        'url': 'https://showcamrips.com/show-cam-sex-movies/2117460-seleneflame-chaturbate-webcam-rip-20260830-032411.html',
        'only_matching': True,
    }, {
        'url': 'https://www.showcamrips.com/show-cam-sex-movies/2117460',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        headers = {'Referer': url}

        player = self._download_webpage(
            urljoin(url, f'/play.php?idd={video_id}'), video_id,
            'Downloading player', headers=headers)

        formats = []
        for entry in self._parse_html5_media_entries(url, player, video_id) or []:
            formats.extend(entry.get('formats') or [])
        for video_url in orderedSet(re.findall(
                r'''(?x)(?:video\.src\s*=\s*|<video[^>]+\bsrc=)["'](https?://[^"']+)''', player)):
            ext = determine_ext(video_url, default_ext='')
            if ext in ('php', 'js', 'html', 'mp6') or 'ads-click' in video_url or 'livecamstreamrip.com' in video_url:
                continue
            formats.append({
                'url': video_url,
                'ext': ext if ext in ('mp4', 'webm', 'm3u8') else 'mp4',
                'quality': 1 if ext == 'mp4' else -2,
            })
        if not formats:
            raise ExtractorError('No video source found', expected=True)
        for f in formats:
            f.setdefault('http_headers', headers)

        meta = self._search_regex(
            r'<span class="tl">(.*?)</span>', webpage, 'metadata', default='', flags=re.DOTALL)
        model = self._html_search_regex(
            r'/model/en/[^"]+"[^>]*>([^<]+)', meta, 'model', default=None)
        category = self._html_search_regex(
            r'/cat/en/[^"]+"[^>]*>([^<]+)', meta, 'category', default=None)
        site = self._html_search_regex(
            r'/site/en/[^"]+"[^>]*>([^<]+)', meta, 'site', default=None)
        date_str = self._html_search_regex(
            r'<h3>Date:\s*([^<]+)</h3>', webpage, 'upload date', default=None)

        return {
            'id': video_id,
            'title': self._html_extract_title(webpage) or video_id,
            'thumbnail': f'https://www.showpicmoi.com/img/{video_id}.jpg',
            'uploader': model,
            'uploader_url': urljoin(url, f'/model/en/{model}/') if model else None,
            'upload_date': unified_strdate((date_str or '').replace('.', '-')),
            'duration': parse_duration(self._html_search_regex(
                r'<h3>Duration\s*:\s*([^<]+)</h3>', webpage, 'duration', default=None)),
            'age_limit': 18,
            'categories': [category] if category else None,
            'tags': [site] if site else None,
            'formats': formats,
            'http_headers': headers,
        }
