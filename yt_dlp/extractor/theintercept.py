from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TheInterceptIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?theintercept\.com/(?:fieldofvision/|(?:\d{4}/\d{2}/\d{2}/))(?P<id>[^/?#]+)'
    _TESTS = [{
        # Current video articles embed YouTube in FeaturedImageHero
        'url': 'https://theintercept.com/2025/09/03/ice-la-immigrants-activists-teacher-union-del-barrio/',
        'md5': '481349799d62e5cc5854931e07c86b3c',
        'info_dict': {
            'id': 'e9lRq9nfevs',
            'ext': 'mp4',
            'title': 'A City Fights Back: How LA Defends Itself From ICE',
            'description': 'md5:ce72fbab7eea54544473707d866645d4',
            'duration': 608,
            'uploader': 'The Intercept',
            'uploader_id': '@TheInterceptFLM',
            'uploader_url': 'https://www.youtube.com/@TheInterceptFLM',
            'channel': 'The Intercept',
            'channel_id': 'UCv002AUCZaPNwiADqwchijg',
            'channel_url': 'https://www.youtube.com/channel/UCv002AUCZaPNwiADqwchijg',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1756893671,
            'upload_date': '20250903',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['News & Politics'],
            'tags': [],
            'heatmap': 'count:100',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
        ],
    }, {
        'url': 'https://theintercept.com/fieldofvision/thisisacoup-episode-four-surrender-or-die/',
        'skip': 'video gone',
        'md5': '145f28b41d44aab2f87c0a4ac8ec95bd',
        'info_dict': {
            'id': '46214',
            'ext': 'mp4',
            'title': '#ThisIsACoup – Episode Four: Surrender or Die',
            'description': 'md5:74dd27f0e2fbd50817829f97eaa33140',
            'timestamp': 1450429239,
            'upload_date': '20151218',
            'comment_count': int,
        },
    }, {
        'url': 'https://theintercept.com/2022/12/14/doug-ducey-border-wall-protest/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        store_tree = self._search_regex(
            r'initialStoreTree\s*=\s*(?P<json_data>{.+})', webpage,
            'initialStoreTree', default=None)
        if store_tree:
            json_data = self._parse_json(store_tree, display_id)
            for post in traverse_obj(json_data, ('resources', 'posts', ...)):
                if traverse_obj(post, 'slug') == display_id and post.get('fov_videoid'):
                    return {
                        '_type': 'url_transparent',
                        'url': 'jwplatform:{}'.format(post['fov_videoid']),
                        'id': str(post['ID']),
                        'display_id': display_id,
                        'title': post.get('title'),
                        'description': post.get('excerpt'),
                        'timestamp': parse_iso8601(post.get('date')),
                        'comment_count': int_or_none(post.get('comments_number')),
                    }

        youtube_id = self._search_regex(
            r'(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)(?P<id>[\w-]{11})',
            webpage, 'youtube id', default=None, group='id')
        if youtube_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id)

        vimeo_id = self._search_regex(
            r'(?:player\.)?vimeo\.com/(?:video/)?(?P<id>\d+)',
            webpage, 'vimeo id', default=None, group='id')
        if vimeo_id:
            return self.url_result(f'https://vimeo.com/{vimeo_id}', 'Vimeo', vimeo_id)

        entries = self._parse_html5_media_entries(url, webpage, display_id) or []
        for entry in entries:
            media_url = url_or_none(entry.get('url')) or traverse_obj(
                entry, ('formats', 0, 'url', {url_or_none}))
            if not media_url:
                continue
            entry.update({
                'id': display_id,
                'display_id': display_id,
                'title': self._og_search_title(webpage) or display_id,
                'description': self._og_search_description(webpage),
                'thumbnail': entry.get('thumbnail') or self._og_search_thumbnail(webpage),
                'timestamp': parse_iso8601(self._html_search_meta(
                    'article:published_time', webpage, default=None)),
            })
            if not entry.get('formats') and not entry.get('url'):
                entry['url'] = media_url
            return entry

        mp4_url = url_or_none(unescapeHTML(self._search_regex(
            r'(https?://(?:www\.)?theintercept\.com/wp-content/uploads/[^"\'<> ]+\.mp4)',
            webpage, 'mp4 url', default=None)))
        if mp4_url:
            return {
                'id': display_id,
                'display_id': display_id,
                'url': mp4_url,
                'title': self._og_search_title(webpage) or display_id,
                'description': self._og_search_description(webpage),
                'thumbnail': self._og_search_thumbnail(webpage),
                'timestamp': parse_iso8601(self._html_search_meta(
                    'article:published_time', webpage, default=None)),
            }

        raise ExtractorError('Unable to find video', expected=True)
