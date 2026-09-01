import re

from .bunnycdn import BunnyCdnIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    parse_count,
    remove_end,
    unescapeHTML,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class BrandNewTubeIE(InfoExtractor):
    IE_NAME = 'brandnewtube'
    IE_DESC = 'BrandNewTube / OneVSP'
    _VALID_URL = r'https?://(?:www\.)?(?:brandnewtube|onevsp)\.com/watch/(?:[^/?#]+_)?(?P<id>[\w-]+)(?:\.html)?'
    _TESTS = [
        {
            'url': 'https://onevsp.com/watch/LAgMo5Cur7EkTJG',
            'md5': '50df8fe81836dce623e32d835fd1fdcb',
            'info_dict': {
                'id': 'LAgMo5Cur7EkTJG',
                'ext': 'mp4',
                'title': 'Introducing Team ONEVSP.COM - Phase One',
                'thumbnail': r're:https?://.+\.(?:jpg|png|gif)',
                'uploader': 'OneVspHub',
                'uploader_id': 'OneVspHub',
                'uploader_url': 'https://onevsp.com/channels/@OneVspHub',
                'channel': 'OneVspHub',
                'channel_id': 'OneVspHub',
                'channel_url': 'https://onevsp.com/channels/@OneVspHub',
                'view_count': int,
                'like_count': int,
            },
        },
        {
            'url': 'https://brandnewtube.com/watch/LAgMo5Cur7EkTJG',
            'only_matching': True,
        },
        {
            'url': 'https://brandnewtube.com/watch/it-039-s-time-to-be-terrified_SQO8773gPTABngN.html',
            'only_matching': True,
        },
        {
            'url': 'https://onevsp.com/watch/MQiTxetMho8',
            'only_matching': True,
        },
    ]

    @staticmethod
    def _media_url(src):
        src = url_or_none(src)
        if not src:
            return None
        # Some Livewire snapshots prefix the Bunny HLS URL with the old CDN host.
        nested = re.search(r'https?://[^/]+/(https?://.+)', src)
        if nested:
            src = nested.group(1)
        return url_or_none(src)

    def _player_data(self, webpage, video_id):
        for raw in re.findall(r'\bwire:snapshot="([^"]+)"', webpage):
            data = self._parse_json(unescapeHTML(raw), video_id, fatal=False)
            if traverse_obj(data, ('memo', 'name', {str})) == 'video-player':
                return traverse_obj(data, ('data', {dict})) or {}
        return {}

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = (
            self._html_search_regex(
                r'<div[^>]+class="single-video-title[^"]*"[^>]*>([^<]+)', webpage, 'title', default=None,
            )
            or remove_end(self._html_extract_title(webpage, default=''), ' - Onevsp')
            or None
        )
        uploader = self._html_search_regex(r'class="video-username"[^>]*>([^<]+)', webpage, 'uploader', default=None)
        channel_id = self._search_regex(r'/channels/@([^"/?#]+)', webpage, 'channel id', default=None)
        channel_url = urljoin(url, f'/channels/@{channel_id}') if channel_id else None

        info = {
            'id': video_id,
            'title': title,
            'thumbnail': url_or_none(
                self._search_regex(r'<video[^>]+data-poster=["\']([^"\']+)', webpage, 'thumbnail', default=None),
            ),
            'uploader': uploader,
            'uploader_id': channel_id,
            'uploader_url': channel_url,
            'channel': uploader,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'view_count': parse_count(
                self._html_search_regex(r'class="video-views"[^>]*>([^<]+)', webpage, 'view count', default=None),
            ),
            'like_count': parse_count(
                clean_html(
                    self._search_regex(
                        r'bi-hand-thumbs-up.*?</i>(.*?)</span>', webpage, 'like count', default=None, flags=re.DOTALL,
                    ),
                ),
            ),
        }

        formats = []
        for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
            formats.extend(entry.get('formats') or [])
            info['thumbnail'] = info.get('thumbnail') or entry.get('thumbnail')

        player = self._player_data(webpage, video_id)
        media_url = self._media_url(traverse_obj(player, ('url', {str})))
        embed_url = next(BunnyCdnIE._extract_embed_urls(url, webpage), None)
        if media_url and not any(f.get('url') == media_url for f in formats):
            ext = determine_ext(media_url)
            # Bunny HLS from the snapshot is referer-gated; use the iframe instead.
            if ext == 'm3u8' and not embed_url:
                formats.extend(self._extract_m3u8_formats(media_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            elif ext != 'm3u8':
                formats.append(
                    {
                        'url': media_url,
                        'ext': ext or 'mp4',
                    },
                )
        if not info.get('thumbnail'):
            info['thumbnail'] = traverse_obj(player, (('poster', 'gif'), {url_or_none}, any))

        if formats:
            return {
                **info,
                'formats': formats,
            }

        if embed_url:
            return self.url_result(embed_url, ie=BunnyCdnIE, url_transparent=True, display_id=video_id, **info)

        raise ExtractorError('No video source found', expected=True)
