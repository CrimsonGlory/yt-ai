import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    merge_dicts,
    remove_end,
    str_to_int,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TokyoMotionIE(InfoExtractor):
    IE_NAME = 'tokyomotion'
    IE_DESC = 'TOKYO Motion'
    _VALID_URL = r'https?://(?:www\.)?tokyomotion\.net/(?:video/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?|embed/(?P<embed_id>[0-9a-f]+))'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?tokyomotion\.net/embed/[0-9a-f]+)']
    _TESTS = [
        {
            'url': 'https://www.tokyomotion.net/video/6002672/',
            'md5': '89d605d59fc9b0077caa9aaa33b4ab87',
            'info_dict': {
                'id': '6002672',
                'ext': 'mp4',
                'display_id': '金メダリストは白人のペニスをしゃぶる',
                'title': '金メダリストは白人のペニスをしゃぶる',
                'description': 'Gold medalist sucks white cock.',
                'thumbnail': r're:https?://cdn\.tokyo-motion\.net/media/videos/tmb\d+/6002672/default\.jpg',
                'duration': 162.75,
                'view_count': int,
                'like_count': int,
                'dislike_count': int,
                'uploader': 'anonymous',
                'tags': ['kingレイナ', 'フェラ', 'onlyfans'],
                'age_limit': 18,
            },
        },
        {
            'url': 'https://www.tokyomotion.net/video/6002672/金メダリストは白人のペニスをしゃぶる',
            'only_matching': True,
        },
        {
            'url': 'https://www.tokyomotion.net/embed/6cd0d3ec33e4857923e0',
            'only_matching': True,
        },
        {
            'url': 'https://tokyomotion.net/video/6887876/amateur-threesome-at-a-wild-party',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id, display_id, embed_id = self._match_valid_url(url).group('id', 'display_id', 'embed_id')
        display_id = display_id or video_id or embed_id
        webpage = self._download_webpage(url, display_id)

        if embed_id:
            video_url = url_or_none(traverse_obj(
                self._search_json(
                    r'<script[^>]+id="fplayer"[^>]+data-layout=\'',
                    webpage, 'player layout', embed_id, default={}),
                ('logo', 'clickUrl')))
            if video_url and '/video/' in video_url:
                return self.url_result(video_url, ie=self.ie_key())

        if not video_id:
            video_id = self._search_regex(
                (r'var\s+video_id\s*=\s*["\'](\d+)',
                 r'(?:/|\\/)video(?:/|\\/)(\d+)',
                 r'/tmb\d+/(\d+)/'),
                webpage, 'video id', default=embed_id)

        if not display_id or display_id in (video_id, embed_id):
            display_id = unescapeHTML(self._search_regex(
                rf'(?:/|\\/)video(?:/|\\/){re.escape(video_id)}(?:/|\\/)([^/?#"\'\\]+)',
                self._og_search_url(webpage, default='') or webpage,
                'display id', default=display_id))

        if 'This is a private video' in webpage:
            self.raise_login_required('This is a private video')

        media = self._parse_html5_media_entries(url, webpage, video_id) or []
        info = media[0] if media else {}
        formats = info.get('formats') or []
        if not formats and not info.get('url'):
            raise ExtractorError('No video formats found', expected=True)

        quality_map = {'hd': 1, 'sd': -1}
        for fmt in formats:
            src = fmt.get('url') or ''
            qid = self._search_regex(r'/vsrc/(hd|sd)/', src, 'quality', default=None)
            if not qid:
                qid = (fmt.get('format_id') or '').lower() or None
            if qid in quality_map:
                fmt['format_id'] = qid
                fmt.setdefault('quality', quality_map[qid])

        title = remove_end(
            self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage, default=None)
            or display_id,
            ' - TOKYO Motion')
        tags = [
            t.strip() for t in (self._html_search_meta('keywords', webpage, default='') or '').split(',') if t.strip()
        ]

        return merge_dicts(
            info,
            {
                'id': video_id,
                'display_id': display_id,
                'title': title,
                'description': self._og_search_description(webpage, default=None),
                'thumbnail': self._og_search_thumbnail(webpage, default=None),
                'duration': float_or_none(self._html_search_meta('video:duration', webpage, default=None)),
                'view_count': str_to_int(
                    self._search_regex(
                        r'class="[^"]*big-views[^"]*"[^>]*>.*?([\d,]+)</span>\s*views',
                        webpage,
                        'view count',
                        default=None,
                        flags=re.DOTALL,
                    ),
                ),
                'like_count': int_or_none(
                    self._html_search_regex(r'id="video_likes"[^>]*>([^<]+)', webpage, 'like count', default=None),
                ),
                'dislike_count': int_or_none(
                    self._html_search_regex(r'id="video_dislikes"[^>]*>([^<]+)', webpage, 'dislike count', default=None),
                ),
                'uploader': self._html_search_regex(
                    r'class="[^"]*user-container[^"]*"[^>]*>\s*<a href="/user/([^"/]+)"',
                    webpage,
                    'uploader',
                    default=None,
                ),
                'uploader_id': self._search_regex(
                    r'class="[^"]*user-container[^"]*"[^>]*>\s*<a[^>]*>\s*<img[^>]+/users/(\d+)\.',
                    webpage,
                    'uploader id',
                    default=None,
                ),
                'tags': tags or None,
                'age_limit': 18,
                'formats': formats,
            },
        )
