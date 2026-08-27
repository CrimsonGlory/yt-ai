from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    parse_duration,
    str_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class LaracastsBaseIE(InfoExtractor):
    def _get_prop_data(self, url, display_id):
        webpage = self._download_webpage(url, display_id)
        return traverse_obj(
            self._search_json(
                r'<script[^>]+\bdata-page="app"[^>]*>', webpage, 'page data',
                display_id, end_pattern='</script>'),
            'props')

    def _episode_meta(self, episode):
        return traverse_obj(episode, {
            'id': ('id', {int}, {str_or_none}),
            'title': ('title', {clean_html}),
            'season_number': ('chapter', {int_or_none}),
            'episode_number': ('position', {int_or_none}),
            'description': ('body', {clean_html}),
            'thumbnail': ('largeThumbnail', {url_or_none}),
            'duration': ('length', {int_or_none}),
            'upload_date': ('dateSegments', 'published', {unified_strdate}),
            'uploader': ('author', 'username', {str}),
        })

    def _extract_episode(self, episode):
        video_id = str(episode['id'])
        playback_url = traverse_obj(episode, ('cloudflarePlayback', 'src', {url_or_none}))
        if not playback_url:
            self.raise_login_required('This video is only available for subscribers.')

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            playback_url, video_id, 'mp4', m3u8_id='hls')
        for caption in traverse_obj(episode, (
            'cloudflarePlayback', 'captions', lambda _, v: url_or_none(v['src']),
        )):
            subtitles.setdefault(caption.get('language') or 'en', []).append({
                'url': caption['src'],
                'name': caption.get('label'),
            })
        return {
            **self._episode_meta(episode),
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        }


class LaracastsIE(LaracastsBaseIE):
    IE_NAME = 'laracasts'
    _VALID_URL = r'https?://(?:www\.)?laracasts\.com/series/(?P<id>[\w-]+/episodes/\d+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://laracasts.com/series/30-days-to-learn-laravel-11/episodes/1',
        'md5': '725fa1eb96c59aff8d9bb3a8d6160baf',
        'info_dict': {
            'id': '3118',
            'title': 'Hello, Laravel',
            'ext': 'mp4',
            'duration': 519,
            'upload_date': '20240312',
            'thumbnail': 'https://laracasts.s3.amazonaws.com/videos/thumbnails/youtube/30-days-to-learn-laravel-11-1.png',
            'description': 'md5:ddd658bb241975871d236555657e1dd1',
            'season_number': 1,
            'season': 'Season 1',
            'episode_number': 1,
            'episode': 'Episode 1',
            'uploader': 'JeffreyWay',
        },
        # HLS --test only fetches the fMP4 init fragment (~1KB), below the default 10KB check
        'file_minsize': None,
        'params': {
            'format': 'b[height=720]/b',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        return self._extract_episode(self._get_prop_data(url, display_id)['lesson'])


class LaracastsPlaylistIE(LaracastsBaseIE):
    IE_NAME = 'laracasts:series'
    _VALID_URL = r'https?://(?:www\.)?laracasts\.com/series/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://laracasts.com/series/30-days-to-learn-laravel-11',
        'info_dict': {
            'title': '30 Days to Learn Laravel',
            'id': '210',
            'thumbnail': 'https://laracasts.s3.amazonaws.com/series/thumbnails/social-cards/30-days-to-learn-laravel-11.png',
            'duration': 30600.0,
            'modified_date': '20240509',
            'description': 'md5:27c260a1668a450984e8f901579912dd',
            'categories': ['Frameworks'],
            'tags': ['Laravel'],
            'display_id': '30-days-to-learn-laravel-11',
        },
        'playlist_count': 30,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        series = self._get_prop_data(url, display_id)['series']

        metadata = {
            'display_id': display_id,
            **traverse_obj(series, {
                'title': ('title', {str}),
                'id': ('id', {int}, {str_or_none}),
                'description': ('body', {clean_html}),
                'thumbnail': (('large_thumbnail', 'thumbnail'), {url_or_none}, any),
                'duration': ('runTime', {parse_duration}),
                'categories': ('taxonomy', 'name', {str}, all, filter),
                'tags': ('topics', ..., 'name', {str}),
                'modified_date': (('lastUpdated', ('dates', 'lastUpdated')), {unified_strdate}, any),
            }),
        }

        entries = []
        for episode in traverse_obj(series, (
            'chapters', ..., 'episodes',
            lambda _, v: traverse_obj(v, ('cloudflarePlayback', 'src', {url_or_none})),
        )):
            entries.append(self.url_result(
                f'https://laracasts.com/series/{display_id}/episodes/{episode["position"]}',
                LaracastsIE, **self._episode_meta(episode)))

        return self.playlist_result(entries, **metadata)
