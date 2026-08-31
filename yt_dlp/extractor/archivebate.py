import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    determine_ext,
    parse_count,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class ArchivebateIE(InfoExtractor):
    IE_DESC = 'archivebate.com'
    _VALID_URL = r'https?://(?:www\.)?archivebate\.com/(?:watch|embed)/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://www.archivebate.com/watch/16436003',
            'md5': 'cf4137b63710fd61fb63296ddb464758',
            'info_dict': {
                'id': '16436003',
                'ext': 'mp4',
                'title': 'golov176 Chaturbate webcam recordings, Archivebate',
                'description': 'golov176 Chaturbate show on 2026-08-31 12:52:42 - Stripchat archive, Camsoda archive, TikTok archive, Chaturbate archive, Instagram archive, Facebook archive, Onlyfans archive, CherryTV archive. Watch your favourite camgirls for free. Cam Videos and Camgirls from Chaturbate, Camsoda, Stripchat, Tiktok, Instagram, CherryTV, Facebook, Onlyfans etc',
                'thumbnail': r're:https?://cdn\.freefile\.io/thumbnails/.+\.jpg',
                'timestamp': 1788180762,
                'upload_date': '20260831',
                'uploader': 'golov176',
                'uploader_url': 'https://www.archivebate.com/profile/golov176',
                'view_count': int,
                'age_limit': 18,
            },
        },
        {
            'url': 'https://www.archivebate.com/embed/14539088',
            'only_matching': True,
        },
        {
            'url': 'https://archivebate.com/watch/14539088',
            'only_matching': True,
        },
    ]

    @staticmethod
    def _absolutize(url):
        if url and url.startswith('//'):
            url = f'https:{url}'
        return url_or_none(url)

    def _extract_mixdrop_formats(self, mixdrop_url, video_id):
        mixdrop_url = self._absolutize(mixdrop_url)
        mixdrop_url = re.sub(r'/(?:f)/', '/e/', mixdrop_url)
        webpage, urlh = self._download_webpage_handle(mixdrop_url, video_id, 'Downloading Mixdrop embed')
        packed = self._search_regex(r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default=None)
        decoded = decode_packed_codes(packed) if packed else webpage
        video_url = self._absolutize(
            self._search_regex(r'MDCore\.wurl\s*=\s*"([^"]+)"', decoded, 'Mixdrop video URL', default=None),
        )
        if not video_url:
            video_url = self._absolutize(
                self._search_regex(r'(//[\w.-]*mxcontent\.net/[^"\']+)', decoded, 'Mixdrop video URL'),
            )
        if determine_ext(video_url, 'mp4') == 'm3u8':
            return self._extract_m3u8_formats(video_url, video_id, 'mp4', m3u8_id='hls', headers={'Referer': urlh.url})
        return [
            {
                'url': video_url,
                'ext': 'mp4',
                'format_id': 'http',
                'http_headers': {'Referer': urlh.url},
            },
        ]

    def _extract_media(self, webpage, video_id):
        formats = []
        mixdrop_url = self._search_regex(
            r'<iframe[^>]+src=["\']((?:https?:)?//(?:www\.)?(?:mixdrop|miixdrop)\.[^"\']+)["\']',
            webpage,
            'Mixdrop iframe',
            default=None,
        )
        if not mixdrop_url:
            mixdrop_url = self._search_regex(
                r'<input[^>]+name=["\']fid["\'][^>]+value=["\']((?:https?:)?//(?:www\.)?(?:mixdrop|miixdrop)\.[^"\']+)["\']',
                webpage,
                'Mixdrop file URL',
                default=None,
            )
        if mixdrop_url:
            formats.extend(self._extract_mixdrop_formats(mixdrop_url, video_id))

        m3u8_url = url_or_none(
            self._search_regex(
                r'<source[^>]+src=["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', webpage, 'm3u8 URL', default=None,
            ),
        )
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://www.archivebate.com/watch/{video_id}', video_id)

        formats = self._extract_media(webpage, video_id)
        if not formats:
            embed = self._download_webpage(
                f'https://www.archivebate.com/embed/{video_id}', video_id, 'Downloading embed page', fatal=False,
            )
            if embed:
                formats = self._extract_media(embed, video_id)

        if not formats:
            if 'This video has been deleted' in webpage:
                raise ExtractorError('This video has been deleted', expected=True)
            raise ExtractorError('Unable to extract video URL')

        uploader = self._search_regex(
            r'href="https?://(?:www\.)?archivebate\.com/profile/([^"/]+)"', webpage, 'uploader', default=None,
        )
        description = self._og_search_description(webpage, default=None)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage, default=None) or video_id,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'timestamp': unified_timestamp(
                self._search_regex(
                    r'show on (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', description or '', 'timestamp', default=None,
                ),
            ),
            'uploader': uploader,
            'uploader_url': urljoin('https://www.archivebate.com/profile/', uploader) if uploader else None,
            'view_count': parse_count(self._search_regex(r'([\d,.]+)\s*views', webpage, 'view count', default=None)),
            'age_limit': 18,
            'formats': formats,
        }
