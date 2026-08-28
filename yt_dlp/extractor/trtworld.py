from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    parse_duration,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TrtWorldIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?trtworld\.com/video/(?P<id>[0-9a-f]{8,24}|\d+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?trtworld\.com/video/[\w-]+/[\w-]+-(?P<id>\d+)',
    )

    _TESTS = [
        {
            'url': 'https://www.trtworld.com/video/fa9ff3d599e9',
            'md5': '46ba0dd1bda129555ad219aca044fffc',
            'info_dict': {
                'id': 'fa9ff3d599e9',
                'ext': 'mp4',
                'title': 'America’s newest media moguls: the Ellisons',
                'description': 'When billionaires with political ties control the news, and now even TikTok, how free is your feed, really?',
                'thumbnail': r're:https?://.+',
                'timestamp': 1763384031,
                'upload_date': '20251117',
                'duration': 258,
            },
        },
        {
            'url': 'https://www.trtworld.com/video/news/turkiye-switches-to-sustainable-tourism-16067690',
            'skip': 'video gone',
            'info_dict': {
                'id': '16067690',
                'ext': 'mp4',
                'title': 'Türkiye switches to sustainable tourism',
                'release_timestamp': 1701529569,
                'release_date': '20231202',
                'thumbnail': 'https://cdn-i.pr.trt.com.tr/trtworld/17647563_0-0-1920-1080.jpeg',
                'description': 'md5:0a975c04257fb529c8f99c7b76a2cf12',
            },
        },
        {
            'url': 'https://www.trtworld.com/video/one-offs/frames-from-anatolia-recreating-a-james-bond-scene-in-istanbuls-grand-bazaar-14541780',
            'skip': 'video gone',
            'info_dict': {
                'id': '14541780',
                'ext': 'mp4',
                'title': 'Frames From Anatolia: Recreating a ‘James Bond’ Scene in Istanbul’s Grand Bazaar',
                'release_timestamp': 1692440844,
                'release_date': '20230819',
                'thumbnail': 'https://cdn-i.pr.trt.com.tr/trtworld/16939810_0-0-1920-1080.jpeg',
                'description': 'md5:4050e21570cc3c40b6c9badae800a94f',
            },
        },
        {
            'url': 'https://www.trtworld.com/video/the-newsmakers/can-sudan-find-peace-amidst-failed-transition-to-democracy-12904760',
            'skip': 'video gone',
            'info_dict': {
                'id': '12904760',
                'ext': 'mp4',
                'title': 'Can Sudan find peace amidst failed transition to democracy?',
                'release_timestamp': 1681972747,
                'release_date': '20230420',
                'thumbnail': 'http://cdni0.trtworld.com/w768/q70/154214_NMYOUTUBETEMPLATE1_1681833018736.jpg',
            },
        },
        {
            'url': 'https://www.trtworld.com/video/africa-matters/locals-learning-to-cope-with-rising-tides-of-kenyas-great-lakes-16059545',
            'skip': 'video gone',
            'info_dict': {
                'id': 'zEns2dWl00w',
                'ext': 'mp4',
                'title': "Locals learning to cope with rising tides of Kenya's Great Lakes",
                'thumbnail': 'https://i.ytimg.com/vi/zEns2dWl00w/maxresdefault.jpg',
                'description': 'md5:3ad9d7c5234d752a4ead4340c79c6b8d',
                'channel_id': 'UC7fWeaHhqgM4Ry-RMpM2YYw',
                'channel_url': 'https://www.youtube.com/channel/UC7fWeaHhqgM4Ry-RMpM2YYw',
                'duration': 210,
                'view_count': int,
                'age_limit': 0,
                'webpage_url': 'https://www.youtube.com/watch?v=zEns2dWl00w',
                'categories': ['News & Politics'],
                'channel': 'TRT World',
                'channel_follower_count': int,
                'channel_is_verified': True,
                'uploader': 'TRT World',
                'uploader_id': '@trtworld',
                'uploader_url': 'https://www.youtube.com/@trtworld',
                'upload_date': '20231202',
                'availability': 'public',
                'comment_count': int,
                'playable_in_embed': True,
                'tags': [],
                'live_status': 'not_live',
                'like_count': int,
            },
        },
        {
            'url': 'https://trtworld.com/video/18273143',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        content = (
            traverse_obj(
                self._search_nextjs_v13_data(webpage, display_id),
                (..., 'content', {dict}, {lambda v: v if v.get('slug') == display_id else None}, any),
            )
            or {}
        )
        media = traverse_obj(content, ('media', 'media', {dict})) or {}

        youtube_url = None
        formats = []
        added = set()

        def add_media_url(media_url, **fmt):
            nonlocal youtube_url
            media_url = url_or_none(media_url)
            if not media_url or media_url in added:
                return
            if YoutubeIE.suitable(media_url):
                youtube_url = youtube_url or media_url
                return
            ext = determine_ext(media_url)
            if ext in ('json', 'html'):
                return
            added.add(media_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(media_url, display_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append(
                    {
                        'url': media_url,
                        'ext': 'mp4' if ext == 'unknown' else ext,
                        **fmt,
                    },
                )

        if media.get('mimeType') == 'video/youtube' or YoutubeIE.suitable(media.get('url') or ''):
            youtube_url = url_or_none(media.get('url'))
            if youtube_url:
                return self.url_result(youtube_url, YoutubeIE)

        for item in traverse_obj(media, ('playlistJson', 'items', ..., {dict})):
            add_media_url(
                item.get('src'),
                **traverse_obj(
                    item,
                    {
                        'format_id': ('label', {str}),
                        'width': ('width', {int_or_none}),
                        'height': ('height', {int_or_none}),
                    },
                ),
            )
        add_media_url(media.get('originalUrl'))
        add_media_url(media.get('url'))

        if not formats:
            add_media_url(self._og_search_video_url(webpage, default=None))
        if not formats:
            if youtube_url:
                return self.url_result(youtube_url, YoutubeIE)
            raise ExtractorError('No video found', expected=True)

        return {
            'id': display_id,
            'formats': formats,
            'duration': (
                traverse_obj(media, ('duration', {float_or_none}))
                or traverse_obj(content, ('duration', {parse_duration}))
            ),
            'thumbnail': traverse_obj(
                content,
                ('coverImage', 'media', 'originalUrl', {url_or_none}),
                ('coverImage', 'media', 'thumbnailUrl', {url_or_none}),
                ('media', 'media', 'thumbnailUrl', {url_or_none}),
            ),
            **traverse_obj(
                content,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}, filter),
                    'timestamp': ('publishedAt', {parse_iso8601}),
                },
            ),
        }
