import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
    parse_qs,
    remove_end,
    traverse_obj,
    unescapeHTML,
    unified_strdate,
    url_or_none,
)


class JavQuickIE(InfoExtractor):
    IE_NAME = 'javquick'
    IE_DESC = 'javquick.com'
    _VALID_URL = r'https?://(?:www\.)?javquick\.com/movie/(?P<id>[^/?#]+)(?:/(?P<display_id>[^/?#]+))?'
    _TESTS = [
        {
            'url': 'https://javquick.com/movie/POUUCrXo/jufe-163-old-man-s-gonzo-document-soggy-thickly-fluid-body-fluid-sweaty-sexual-intercourse-sakiyo-kiyone',
            'md5': 'fc749f47a09c7979b64a182c4c9fb96e',
            'info_dict': {
                'id': 'POUUCrXo',
                'ext': 'mp4',
                'display_id': 'jufe-163-old-man-s-gonzo-document-soggy-thickly-fluid-body-fluid-sweaty-sexual-intercourse-sakiyo-kiyone',
                'title': "JUFE-163 Old Man's Gonzo Document Soggy Thickly Fluid Body Fluid Sweaty Sexual Intercourse Sakiyo Kiyone",
                'description': 'md5:1c4e65c4f05a1aced659e28ab54b6955',
                'thumbnail': r're:https?://ie2\.javquick\.com/media/.+',
                'release_date': '20200413',
                'upload_date': '20250331',
                'cast': ['Seion Sakura'],
                'categories': ['Creampie', 'Huge Butt', 'POV', 'Solowork', 'Sweat', 'Tall'],
                'age_limit': 18,
            },
        },
        {
            'url': 'https://javquick.com/movie/POUUCrXo/jufe-163-old-man-s-gonzo-document-soggy-thickly-fluid-body-fluid-sweaty-sexual-intercourse-sakiyo-kiyone?type=HD&p=2',
            'only_matching': True,
        },
        {
            'url': 'https://javquick.com/movie/POUUCrXo',
            'only_matching': True,
        },
        {
            'url': 'https://www.javquick.com/movie/aRYFZYCk/oyc-134-amateur-men-and-women-observe-monitoring-av-brother-sister-s-brother-sister-love-thorough-verification-when-my-brother-hears-from-my-sister-my-first-experience-or-erogenous-zone-which-i-usually-do-not-speak-absolutely-prize-money-if-i-can-answer-i-will-give-you-a-question-that-gradually-becomes-extreme-and-my-brother-also-erects-unexpectedly-thoughtlessly-to-my-sister-s-answer',
            'only_matching': True,
        },
    ]
    _HEADERS = {'Referer': 'https://javquick.com/'}

    def _page_url(self, url, **query):
        parsed = urllib.parse.urlparse(url)
        qs = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        qs.update({key: str(value) for key, value in query.items()})
        return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(qs)))

    def _resolve_watch_url(self, webpage, video_id):
        token = self._html_search_regex(r'<video[^>]+data-id="([^"]+)"', webpage, 'watch token')
        payload = (
            self._download_webpage(
                'https://javquick.com/watch',
                video_id,
                'Resolving video URL',
                query={'token': token},
                headers=self._HEADERS,
            )
            or ''
        ).strip()
        if payload in ('re', 'r'):
            raise ExtractorError('reCAPTCHA required to resolve video URL', expected=True)
        return url_or_none(payload)

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        qs = parse_qs(url)
        quality = (traverse_obj(qs, ('type', 0)) or 'HD').upper()
        part = int_or_none(traverse_obj(qs, ('p', 0))) or 1

        video_url = self._resolve_watch_url(webpage, video_id)
        if not video_url and quality != 'HD':
            self.to_screen('Encrypted stream; falling back to HD')
            webpage = self._download_webpage(self._page_url(url, type='HD', p=part), video_id, 'Downloading HD webpage')
            quality = 'HD'
            video_url = self._resolve_watch_url(webpage, video_id)

        if not video_url:
            raise ExtractorError('No direct video URL (encrypted MSE stream is not supported)', expected=True)

        title = remove_end(
            self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default='') or '', '| JAV Quick',
        ).strip()
        title = unescapeHTML(title) or self._html_extract_title(webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, default=None),
            'thumbnail': url_or_none(
                self._search_regex(
                    r'<figure[^>]*>.*?<img[^>]+data-srcset="([^"]+)"',
                    webpage,
                    'thumbnail',
                    default=None,
                    flags=re.DOTALL,
                ),
            ),
            'release_date': unified_strdate(
                self._search_regex(
                    r'title="Release Date"></i>\s*<span[^>]*>\s*([\d/]+)', webpage, 'release date', default=None,
                ),
            ),
            'upload_date': unified_strdate(
                self._search_regex(
                    r'title="Publish Date"></i>\s*<span[^>]*>\s*([\d/]+)', webpage, 'publish date', default=None,
                ),
            ),
            'cast': orderedSet(re.findall(r'href="/stars/[^"]+"[^>]*>\s*([^<]+)', webpage)) or None,
            'categories': orderedSet(re.findall(r'href="/genres/[^"]+"[^>]*>\s*([^<]+)', webpage)) or None,
            'age_limit': 18,
            'formats': [
                {
                    'url': video_url,
                    'ext': 'mp4',
                    'format_id': quality.lower(),
                    'http_headers': self._HEADERS,
                    # Un-ranged GET is capped at ~3 MiB; Range requests serve the full file.
                    'downloader_options': {'http_chunk_size': 10 << 20},
                },
            ],
        }
