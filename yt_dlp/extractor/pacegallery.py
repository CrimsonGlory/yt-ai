from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    extract_attributes,
    get_elements_html_by_class,
    orderedSet,
)


class PaceGalleryIE(InfoExtractor):
    IE_NAME = 'pacegallery'
    IE_DESC = 'Pace Gallery'
    _VALID_URL = r'https?://(?:www\.)?pacegallery\.com/(?:artists|events|exhibitions|journal|press)/(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'https://www.pacegallery.com/journal/inside-mika-tajima-37-dimensions-in-los-angeles/',
        'md5': 'd0bd6c97303a6dc7258590aca2426bc6',
        'info_dict': {
            'id': 'BMuAM-m-Hps',
            'ext': 'mp4',
            'title': 'Inside Mika Tajima’s “37 Dimensions” in Los Angeles',
            'description': 'md5:5c069cffdfce2fd0f1cb6761a6a9a487',
            'media_type': 'video',
            'uploader': 'Pace Gallery',
            'uploader_id': '@pacegalleries',
            'uploader_url': 'https://www.youtube.com/@pacegalleries',
            'channel': 'Pace Gallery',
            'channel_id': 'UCaHuA8TlLkcWpGPsNA7tuTw',
            'channel_url': 'https://www.youtube.com/channel/UCaHuA8TlLkcWpGPsNA7tuTw',
            'channel_follower_count': int,
            'comment_count': int,
            'view_count': int,
            'like_count': int,
            'age_limit': 0,
            'duration': 207,
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Education'],
            'tags': [],
            'timestamp': 1784029535,
            'upload_date': '20260714',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
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
        'url': 'https://www.pacegallery.com/journal/our-artists-in-venice-2026/',
        'info_dict': {
            'id': 'our-artists-in-venice-2026',
            'title': 'Our Artists in Venice 2026 | Pace Gallery',
            'description': 'md5:a48bd4ebd2818208c68d73a1f9e08bf1',
        },
        'playlist_mincount': 3,
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.pacegallery.com/exhibitions/paulo-monteiro-undefined-inclusions/',
        'only_matching': True,
    }, {
        'url': 'https://www.pacegallery.com/exhibitions/matthew-day-jackson-against-nature/',
        'only_matching': True,
    }, {
        'url': 'https://www.pacegallery.com/journal/a-conversation-on-paul-thek/',
        'only_matching': True,
    }]

    def _extract_youtube_ids(self, webpage):
        ids = []
        for html in get_elements_html_by_class('youtube-video', webpage):
            video_id = extract_attributes(html).get('data-id')
            if video_id and YoutubeIE.suitable(video_id):
                ids.append(video_id)
        return orderedSet(ids)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        youtube_ids = self._extract_youtube_ids(webpage)
        if not youtube_ids:
            raise ExtractorError('No video found', expected=True)

        entries = [
            self.url_result(
                f'https://www.youtube.com/watch?v={youtube_id}',
                YoutubeIE, youtube_id)
            for youtube_id in youtube_ids
        ]
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, display_id, self._og_search_title(webpage),
            self._og_search_description(webpage))
