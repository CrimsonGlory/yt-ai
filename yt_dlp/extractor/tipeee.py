import re

from .common import InfoExtractor
from .vimeo import VimeoIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    orderedSet,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TipeeeIE(InfoExtractor):
    IE_NAME = 'tipeee'
    IE_DESC = 'Tipeee'
    _VALID_URL = r'https?://(?:(?:www|en|fr|de|es|it)\.)?tipeee\.(?:com|fr)/(?P<project>[\w-]+)/news/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://fr.tipeee.com/french-wargame-studio/news/204867',
            'md5': 'dba0df16719ded115c6a979dc88e1011',
            'info_dict': {
                'id': 'egwrk-AsMKA',
                'ext': 'mp4',
                'title': 'Warhammer Age Of Sigmar - Lecture & Analyse Nighthaunt V4',
                'description': 'md5:21b9a2fe98c5a6c16115cbc81cf36777',
                'media_type': 'video',
                'uploader': 'French Wargame Studio',
                'uploader_id': '@FrenchWargameStudio',
                'uploader_url': 'https://www.youtube.com/@FrenchWargameStudio',
                'channel': 'French Wargame Studio',
                'channel_id': 'UC4u5SwkHYET53JMLA2ImLTA',
                'channel_url': 'https://www.youtube.com/channel/UC4u5SwkHYET53JMLA2ImLTA',
                'channel_is_verified': True,
                'channel_follower_count': int,
                'comment_count': int,
                'view_count': int,
                'like_count': int,
                'age_limit': 0,
                'duration': 4760,
                'thumbnail': r're:https?://i\.ytimg\.com/.+',
                'chapters': 'count:34',
                'categories': ['Entertainment'],
                'tags': 'count:57',
                'timestamp': 1723885229,
                'upload_date': '20240817',
                'playable_in_embed': True,
                'availability': 'public',
                'live_status': 'not_live',
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
            # Original request URL; post is reserved for supporters
            'url': 'https://fr.tipeee.com/french-wargame-studio/news/174045',
            'only_matching': True,
        },
        {
            'url': 'https://tipeee.fr/french-wargame-studio/news/204867',
            'only_matching': True,
        },
        {
            'url': 'https://en.tipeee.com/french-wargame-studio/news/204867',
            'only_matching': True,
        },
    ]
    _API_BASE = 'https://api.tipeee.com/v2.0'
    _YOUTUBE_ID_RE = r'(?:youtube(?:-nocookie)?\.com/(?:embed|shorts|live)/|youtube(?:-nocookie)?\.com/watch\?(?:[^#]*?&)?v=|youtu\.be/)(?P<id>[\w-]{11})'
    _VIMEO_ID_RE = r'(?:player\.)?vimeo\.com/(?:video/|channels/[^/?#]+/)?(?P<id>\d+)'

    def _normalize_embed_url(self, embed_url):
        embed_url = url_or_none(unescapeHTML(embed_url))
        if not embed_url:
            return
        youtube_id = self._search_regex(self._YOUTUBE_ID_RE, embed_url, 'youtube id', default=None, group='id')
        if youtube_id:
            return f'https://www.youtube.com/watch?v={youtube_id}'
        vimeo_id = self._search_regex(self._VIMEO_ID_RE, embed_url, 'vimeo id', default=None, group='id')
        if vimeo_id:
            vimeo_hash = self._search_regex(r'[?&]h=([0-9a-f]+)', embed_url, 'vimeo hash', default=None)
            if vimeo_hash:
                return f'https://player.vimeo.com/video/{vimeo_id}?h={vimeo_hash}'
            return f'https://vimeo.com/{vimeo_id}'
        return embed_url

    def _extract_news_video_urls(self, news):
        candidates = list(
            traverse_obj(
                news,
                (
                    'contentv2',
                    'translations',
                    ...,
                    'components',
                    lambda _, v: v.get('name') == 'tipeee-video',
                    'model',
                    ('url', 'iframe'),
                    {self._normalize_embed_url},
                ),
            ),
        )
        html = unescapeHTML(
            '\n'.join(
                traverse_obj(
                    news,
                    (
                        ('content', {str}),
                        ('contentv2', 'translations', ..., 'html', {str}),
                    ),
                ),
            ),
        )
        if html:
            for pattern in (self._YOUTUBE_ID_RE, self._VIMEO_ID_RE):
                for match in re.finditer(rf'https?://(?:www\.)?{pattern}[^\s"\'<>]*', html):
                    candidates.append(self._normalize_embed_url(match.group(0)))
        return orderedSet(filter(None, candidates))

    def _real_extract(self, url):
        project, news_id = self._match_valid_url(url).group('project', 'id')
        news = self._download_json(f'{self._API_BASE}/projects/{project}/news/{news_id}', news_id)

        embed_urls = self._extract_news_video_urls(news)
        if not embed_urls:
            if news.get('private'):
                self.raise_login_required('This Tipeee news post is reserved for supporters', method='any')
            raise ExtractorError('No video found', expected=True)

        entries = []
        for embed_url in embed_urls:
            if YoutubeIE.suitable(embed_url):
                entries.append(self.url_result(embed_url, YoutubeIE))
            elif VimeoIE.suitable(embed_url):
                entries.append(self.url_result(embed_url, VimeoIE))
            else:
                entries.append(self.url_result(embed_url))

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, news_id, traverse_obj(news, ('name', {str})))
