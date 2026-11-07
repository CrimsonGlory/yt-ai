from .common import InfoExtractor
from ..utils import smuggle_url


class KickStarterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kickstarter\.com/projects/(?P<id>[^/]*)/.*'
    _TESTS = [{
        'url': 'https://www.kickstarter.com/projects/1404461844/intersection-the-story-of-josh-grant/description',
        'md5': '7a9b4ea663e25285834fc053b11b9365',
        'info_dict': {
            'id': '1404461844',
            'ext': 'mp4',
            'title': 'Intersection: The Story of Josh Grant by Kyle Cowling » Intersection: The Story of Josh Grant by Kyle Cowling',
            'description': (
                'A unique motocross documentary that examines the '
                'life and mind of one of sports most elite athletes: Josh Grant.'
            ),
            'thumbnail': r're:https://i\.kickstarter\.com/.+',
        },
        'params': {
            # HTML5 high/base sources; pin base so --test md5 stays stable
            'format': 'base/best',
        },
    }, {
        'note': 'Embedded video (not using the native kickstarter video service)',
        'url': 'https://www.kickstarter.com/projects/597507018/pebble-e-paper-watch-for-iphone-and-android/posts/659178',
        'skip': 'embedded video no longer present',
        'info_dict': {
            'id': '78704821',
            'ext': 'mp4',
            'uploader_id': 'pebble',
            'uploader': 'Pebble Technology',
            'title': 'Pebble iOS Notifications',
        },
        'add_ie': ['Vimeo'],
    }, {
        'url': 'https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html',
        'md5': '95d8a7a916550d5415290eb93b5a3927',
        'info_dict': {
            'id': '1420158244',
            'ext': 'mp4',
            'title': 'Power Drive 2000',
            'thumbnail': r're:https://i\.kickstarter\.com/.+',
        },
        'params': {
            'format': 'base/best',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        title = self._html_search_regex(
            r'<title>\s*(.*?)(?:\s*&mdash;\s*Kickstarter)?\s*</title>',
            webpage, 'title')
        thumbnail = self._og_search_thumbnail(webpage, default=None)
        if thumbnail is None:
            thumbnail = self._html_search_regex(
                r'<img[^>]+class="[^"]+\s*poster\s*[^"]+"[^>]+src="([^"]+)"',
                webpage, 'thumbnail image', fatal=False)

        formats = []
        video_url = self._search_regex(
            r'data-video-url="(.*?)"',
            webpage, 'video URL', default=None)
        if video_url:
            formats.append({'url': video_url, 'ext': 'mp4'})

        html5_entries = self._parse_html5_media_entries(url, webpage, video_id)
        if html5_entries:
            formats.extend(html5_entries[0].get('formats') or [])
            thumbnail = thumbnail or html5_entries[0].get('thumbnail')

        self._remove_duplicate_formats(formats)
        for f in formats:
            media_url = f.get('url') or ''
            if 'h264_high' in media_url:
                f['format_id'] = 'high'
                f['quality'] = 1
            elif 'h264_base' in media_url:
                f['format_id'] = 'base'
                f['quality'] = 0

        if not formats:
            # Third-party embeds (Vimeo, YouTube, etc.)
            return {
                '_type': 'url_transparent',
                'ie_key': 'Generic',
                'url': smuggle_url(url, {'to_generic': True}),
                'title': title,
            }

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': thumbnail,
            'impersonate': True,
        }
