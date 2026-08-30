import urllib.parse

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class KuaishouIE(InfoExtractor):
    IE_DESC = '快手'
    _VALID_URL = (
        r'https?://(?:www\.)?kuaishou\.com/(?:short-video|fw/photo|f)/(?P<id>[\w-]+)',
        r'https?://v\.kuaishou\.com/(?P<id>[\w-]+)',
        r'https?://m\.(?:kuaishou|gifshow)\.com/fw/photo/(?P<id>[\w-]+)',
        r'https?://live\.kuaishou\.com/u/[^/?#]+/(?P<id>[\w-]+)',
    )
    _MOBILE_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    _TESTS = [{
        'url': 'https://www.kuaishou.com/short-video/3x5jvmsmmiahx3m',
        'md5': '96e3cc1b4219df7b7e8aecdb2270d9e1',
        'info_dict': {
            'id': '3x5jvmsmmiahx3m',
            'ext': 'mp4',
            'title': '明大招充能需要五点，而对面正好有五个人 #卡拉彼丘  #明 ',
            'description': '明大招充能需要五点，而对面正好有五个人 #卡拉彼丘  #明 ',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 218,
            'timestamp': 1696413372,
            'upload_date': '20231004',
            'uploader': '鱼夜',
            'uploader_id': '3xt4m66xxjt3qgq',
            'uploader_url': 'https://www.kuaishou.com/profile/3xt4m66xxjt3qgq',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
            'track': '鱼夜的作品原声',
            'artist': '鱼夜',
            'artists': ['鱼夜'],
        },
    }, {
        'url': 'https://www.kuaishou.com/f/X3t3Ee6o1L7gqHe',
        'only_matching': True,
    }, {
        'url': 'https://www.kuaishou.com/fw/photo/3x5jvmsmmiahx3m',
        'only_matching': True,
    }, {
        'url': 'https://m.gifshow.com/fw/photo/3x5jvmsmmiahx3m',
        'only_matching': True,
    }, {
        'url': 'https://v.kuaishou.com/GKTpYm',
        'only_matching': True,
    }, {
        'url': 'https://live.kuaishou.com/u/3xt4m66xxjt3qgq/3x5jvmsmmiahx3m',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if '/f/' in url or 'v.kuaishou.com/' in url:
            page_url = url
        else:
            page_url = f'https://m.gifshow.com/fw/photo/{video_id}'

        webpage, urlh = self._download_webpage_handle(
            page_url, video_id, headers=self._MOBILE_HEADERS)
        init_state = self._search_json(
            r'window\.INIT_STATE\s*=', webpage, 'init state', video_id)
        photo = None
        for entry in (init_state or {}).values():
            candidate = traverse_obj(entry, ('photo', {dict}))
            if traverse_obj(candidate, ('mainMvUrls', ..., 'url', {url_or_none})):
                photo = candidate
                break
        if not photo:
            self.raise_no_formats(
                'No public video found; it may be private, deleted, or a slideshow',
                expected=True, video_id=video_id)

        photo_id = traverse_obj(photo, (
            'share_info', {lambda s: dict(urllib.parse.parse_qsl(s)).get('photoId') if s else None},
        )) or self._search_regex(
            r'/(?:fw/photo|short-video)/([^/?#]+)', urlh.url, 'photo id', default=video_id)

        formats = []
        for i, media_url in enumerate(traverse_obj(photo, ('mainMvUrls', ..., 'url', {url_or_none}))):
            formats.append({
                'url': media_url,
                'format_id': f'http-{i}',
                'ext': 'mp4',
                'width': traverse_obj(photo, ('width', {int_or_none})),
                'height': traverse_obj(photo, ('height', {int_or_none})),
                'quality': 1 if not i else -1,
            })

        subtitles = {}
        for m3u8_url in traverse_obj(photo, (
            'manifest', 'adaptationSet', ..., 'representation', ...,
            (('url', {url_or_none}), ('backupUrl', ..., {url_or_none})),
        )):
            if determine_ext(m3u8_url) != 'm3u8':
                continue
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, photo_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            'id': photo_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(photo, {
                'title': ('caption', {str}),
                'description': ('caption', {str}),
                'duration': ('duration', {int_or_none(scale=1000)}),
                'timestamp': ('timestamp', {int_or_none(scale=1000)}),
                'uploader': ('userName', {str}),
                'uploader_id': ('userEid', {str}),
                'uploader_url': ('userEid', {lambda x: x and f'https://www.kuaishou.com/profile/{x}'}),
                'like_count': ('likeCount', {int_or_none}),
                'view_count': ('viewCount', {int_or_none}),
                'comment_count': ('commentCount', {int_or_none}),
                'repost_count': ('forwardCount', {int_or_none}),
                'thumbnail': ('coverUrls', 0, 'url', {url_or_none}),
                'track': ('soundTrack', 'name', {str}),
                'artist': ('soundTrack', 'artist', {str}),
            }),
        }
