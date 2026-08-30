import base64
import re
import urllib.parse

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import determine_ext, parse_qs, url_or_none
from ..utils.traversal import traverse_obj


class StreamsterIE(InfoExtractor):
    IE_DESC = 'streamster.tv'
    _VALID_URL = r'https?://(?:www\.)?streamster\.tv/events/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _YT_ID_RE = r'''(?x)
        (?:
            (?:www\.)?youtu\.be/|
            (?:www\.)?youtube(?:-nocookie)?\.com/(?:embed/|shorts/|live/|v/|watch\?(?:[^#]*?[&;])?v=)
        )
        (?P<id>[\w-]{11})
    '''
    _TESTS = [
        {
            # HTML5 MediaElement source with the non-standard video/youtube MIME type
            'url': 'https://streamster.tv/events/tischtennis-mixed-team-aut-pol/',
            'md5': '94c080940edb57e220de8d5ca84694af',
            'info_dict': {
                'id': 'Hz_k9w2CZvA',
                'ext': 'mp4',
                'title': 'Tischtennis 02.09.2025',
                'description': '',
                'duration': 10106,
                'uploader': 'Streamster',
                'uploader_id': '@streamster-homeofsports',
                'uploader_url': 'https://www.youtube.com/@streamster-homeofsports',
                'channel': 'Streamster',
                'channel_id': 'UCBadIe8-oZ5oARgzpAmL3jg',
                'channel_url': 'https://www.youtube.com/channel/UCBadIe8-oZ5oARgzpAmL3jg',
                'channel_follower_count': int,
                'view_count': int,
                'age_limit': 0,
                'timestamp': 1756835474,
                'upload_date': '20250902',
                'thumbnail': r're:https?://i\.ytimg\.com/.+',
                'categories': ['Sports'],
                'tags': [],
                'playable_in_embed': True,
                'availability': 'unlisted',
                'live_status': 'not_live',
                'media_type': 'video',
            },
            'add_ie': ['Youtube'],
            'params': {
                'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
            },
            'expected_warnings': [
                'Remote component challenge solver script',
                'No supported JavaScript runtime',
                'n challenge solving failed',
            ],
        },
        {
            # Custom player iframe with base64 videodata
            'url': 'https://streamster.tv/events/volleyball-openplus-baden-2026-d2/',
            'info_dict': {
                'id': 'npGzn29bnIo',
                'ext': 'mp4',
                'title': 'Center Court',
                'description': 'OPEN PLUS Baden Tag 2, 23.08.2026',
                'duration': 29162,
                'uploader': 'Streamster',
                'uploader_id': '@streamster-homeofsports',
                'uploader_url': 'https://www.youtube.com/@streamster-homeofsports',
                'channel': 'Streamster',
                'channel_id': 'UCBadIe8-oZ5oARgzpAmL3jg',
                'channel_url': 'https://www.youtube.com/channel/UCBadIe8-oZ5oARgzpAmL3jg',
                'channel_follower_count': int,
                'view_count': int,
                'age_limit': 0,
                'timestamp': 1785146735,
                'release_timestamp': 1787468121,
                'upload_date': '20260727',
                'release_date': '20260823',
                'thumbnail': r're:https?://i\.ytimg\.com/.+',
                'categories': ['Sports'],
                'tags': [],
                'playable_in_embed': True,
                'availability': 'unlisted',
                'live_status': 'was_live',
                'media_type': 'livestream',
            },
            'add_ie': ['Youtube'],
            'params': {'skip_download': True},
            'expected_warnings': [
                'Remote component challenge solver script',
                'No supported JavaScript runtime',
                'n challenge solving failed',
            ],
        },
        {
            'url': 'https://streamster.tv/events/racketista-ep31/',
            'only_matching': True,
        },
    ]

    def _decode_player_videodata(self, encoded, video_id):
        raw = urllib.parse.unquote(encoded or '')
        padded = raw + '=' * (-len(raw) % 4)
        try:
            decoded = base64.b64decode(padded).decode()
        except (ValueError, TypeError):
            return None
        return self._parse_json(decoded, video_id, fatal=False)

    def _extract_media_url(self, webpage, video_id):
        media_url = self._html_search_regex(
            r'<source[^>]+\bsrc=["\']([^"\']+)["\']', webpage, 'video source', default=None, flags=re.DOTALL,
        )
        if media_url:
            return media_url

        iframe_src = self._html_search_regex(
            r'<iframe[^>]+\bsrc=["\']([^"\']*videodata=[^"\']+)["\']', webpage, 'player iframe', default=None,
        )
        encoded = traverse_obj(parse_qs(iframe_src), ('videodata', 0, {str}))
        if encoded:
            data = self._decode_player_videodata(encoded, video_id)
            media_url = traverse_obj(data, ('videosrc', {url_or_none}))
            if media_url:
                return media_url

        yt_id = self._search_regex(self._YT_ID_RE, webpage, 'youtube id', default=None, group='id')
        if yt_id:
            return f'https://www.youtube.com/watch?v={yt_id}'
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        media_url = self._extract_media_url(webpage, video_id)
        if not media_url:
            self.raise_no_formats('No video source found', expected=True, video_id=video_id)

        yt_id = self._search_regex(self._YT_ID_RE, media_url, 'youtube id', default=None, group='id')
        if yt_id:
            return self.url_result(f'https://www.youtube.com/watch?v={yt_id}', YoutubeIE, yt_id)

        title = (
            self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or video_id
        )
        info = {
            'id': video_id,
            'display_id': video_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
        }
        if YoutubeIE.suitable(media_url):
            return self.url_result(media_url, YoutubeIE, video_title=title)

        ext = determine_ext(media_url)
        if ext == 'm3u8':
            info['formats'] = self._extract_m3u8_formats(media_url, video_id, 'mp4', m3u8_id='hls')
            return info
        return {
            **info,
            'url': media_url,
        }
