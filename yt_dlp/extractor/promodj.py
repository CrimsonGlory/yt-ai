import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    parse_duration,
    unified_timestamp,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class PromoDJIE(InfoExtractor):
    IE_NAME = 'promodj'
    IE_DESC = 'PromoDJ'
    _VALID_URL = (
        r'https?://(?:www\.)?promodj\.com/'
        r'(?:embed|(?P<user>[^/?#]+)/(?:remixes|tracks|mixes|lives|videos|podcasts))'
        r'/(?P<id>\d+)'
    )
    _TESTS = [
        {
            'url': 'https://promodj.com/371571061297/remixes/7766033/Dj_Mpeg_Alex_Namo_Namah_VEDICORE_Remix',
            'md5': 'd4e37dcc59df24aa7af28b24358777c0',
            'info_dict': {
                'id': '7766033',
                'ext': 'mp3',
                'title': 'Dj Mpeg Alex - Namo Namah (VEDICORE, Remix)',
                'description': r're:(?s).+',
                'thumbnail': r're:https://cdn\.promodj\.com/.+',
                'duration': 207.804,
                'timestamp': int,
                'upload_date': '20250705',
                'uploader': 'DJ MPEG ALEX',
                'uploader_id': '371571061297',
                'uploader_url': 'https://promodj.com/371571061297',
                'view_count': int,
                'genres': ['Vocal Trance'],
                'vcodec': 'none',
            },
        },
        {
            'url': 'https://promodj.com/embed/7766033/cover.big?play=1',
            'only_matching': True,
        },
        {
            'url': 'https://promodj.com/371571061297/tracks/7836713/Dj_Mpeg_Alex_V_drugih_mirah_voice_Keshava_Priya',
            'only_matching': True,
        },
        {
            'url': 'https://promodj.com/371571061297/mixes/7860088/Dj_Mpeg_Alex_RasaTrance_mini_mix_2026',
            'only_matching': True,
        },
        {
            'url': 'https://promodj.com/gurchin2012/videos/7960735/Strelki_Na_vecherinke_DJ_YuG_REMIX',
            'only_matching': True,
        },
    ]

    def _resolve_returnurl(self, media_url, video_id):
        if not media_url or 'returnurl=1' not in media_url:
            return media_url
        redirect = self._download_webpage(media_url, video_id, note='Resolving media URL', fatal=False)
        return self._search_regex(r'(?m)^URL=(https?://\S+)', redirect or '', 'resolved media URL', default=media_url)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        user = self._match_valid_url(url).group('user')
        webpage = self._download_webpage(url, video_id)

        player = (
            self._search_json(r',\s*(?=\{"(?:no_preroll|video)")', webpage, 'player data', video_id, default=None) or {}
        )

        formats = []
        duration = None
        for src in traverse_obj(player, ('sources', ..., {dict})):
            src_url = url_or_none(src.get('URL'))
            if not src_url:
                continue
            src_url = urljoin(url, src_url)
            ext = determine_ext(src_url, 'mp3')
            duration = duration or float_or_none(src.get('length'))
            formats.append(
                {
                    'url': src_url,
                    'format_id': 'prelisten',
                    'ext': ext,
                    'vcodec': 'none',
                    'acodec': ext if ext != 'unknown_video' else None,
                    'filesize': int_or_none(src.get('size')),
                    'quality': 0,
                },
            )

        download_url = urljoin(
            url,
            url_or_none(player.get('downloadURL'))
            or url_or_none(
                self._search_regex(
                    r'<a[^>]+id="download_flasher"[^>]+href="([^"]+)"',
                    webpage,
                    'download URL',
                    default=None,
                ),
            ),
        )
        if download_url:
            ext = determine_ext(download_url, 'mp3')
            is_audio = ext in ('mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a')
            # Audio prelisten is the same 320 kbps file as the download button and
            # is what the on-page player uses. Prefer it; keep download for video.
            if not is_audio or not formats:
                formats.append(
                    {
                        'url': download_url,
                        'format_id': 'download',
                        'ext': ext,
                        'vcodec': 'none' if is_audio else None,
                        'acodec': ext if is_audio else None,
                        'quality': 1,
                    },
                )

        if player.get('video'):
            config = player.get('config')
            if isinstance(config, str):
                config = self._parse_json(config, video_id, fatal=False) or {}
            items = traverse_obj(config, ('playlist', 'item'))
            if isinstance(items, dict):
                items = [items]
            for item in items or []:
                play_url = self._resolve_returnurl(traverse_obj(item, ('play', '@url', {url_or_none})), video_id)
                if not play_url:
                    continue
                duration = duration or traverse_obj(item, ('play', '@duration', {float_or_none(scale=1000)}))
                formats.append(
                    {
                        'url': play_url,
                        'format_id': 'h264',
                        'ext': determine_ext(play_url, 'mp4'),
                        'width': int_or_none(player.get('width')),
                        'height': int_or_none(player.get('height')),
                    },
                )

        if not formats:
            stream = self._html_search_meta('twitter:player:stream', webpage, default=None)
            if url_or_none(stream) and determine_ext(stream) not in (None, 'unknown_video'):
                formats.append(
                    {
                        'url': stream,
                        'format_id': 'stream',
                        'ext': determine_ext(stream),
                    },
                )

        if not formats:
            self.raise_no_formats('No public media URL found', expected=True, video_id=video_id)

        if not user:
            user = self._search_regex(
                r'https?://(?:www\.)?promodj\.com/([^/?#]+)/',
                traverse_obj(player, ('titleURL', {str})) or '',
                'user',
                default=None,
            )

        title = (
            traverse_obj(player, ('title', {str}))
            or self._html_search_regex(r'<span[^>]+class="file_title"[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._og_search_title(webpage)
        )
        duration = (
            duration
            or float_or_none(self._og_search_property('video:duration', webpage, default=None))
            or parse_duration(self._html_search_regex(r'<b>Duration:</b>\s*([^<]+)', webpage, 'duration', default=None))
        )

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': duration,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': (
                traverse_obj(player, ('coverURL', ('2000', '1200', '600'), {url_or_none}, any))
                or self._og_search_thumbnail(webpage, default=None)
            ),
            'timestamp': unified_timestamp(
                self._html_search_regex(r'<b>Publication:</b>\s*([^<]+)', webpage, 'publication date', default=None),
            ),
            'uploader': self._html_search_regex(r'<a[^>]+class="user"[^>]*>([^<]+)', webpage, 'uploader', default=None),
            'uploader_id': user,
            'uploader_url': f'https://promodj.com/{user}' if user else None,
            'view_count': int_or_none(
                (self._html_search_regex(r'<b>Listens:</b>\s*([\d\s\xa0]+)', webpage, 'listens', default=None) or '')
                .replace(' ', '')
                .replace('\xa0', ''),
            ),
            'genres': (
                re.findall(
                    r'<a[^>]+>([^<]+)</a>',
                    self._search_regex(
                        r'<b>Styles:</b>\s*<span class="styles">(.+?)</span>',
                        webpage,
                        'styles',
                        default='',
                    ),
                )
                or None
            ),
        }
