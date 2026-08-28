from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    clean_html,
    parse_duration,
    parse_iso8601,
    update_url,
    url_or_none,
)
from ..utils.traversal import require, subs_list_to_dict, traverse_obj


class StarTrekIE(InfoExtractor):
    IE_NAME = 'startrek'
    IE_DESC = 'STAR TREK'
    _VALID_URL = r'https?://(?:www\.)?startrek\.com(?:/en-[a-z]{2})?/videos/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.startrek.com/en-un/videos/official-trailer-star-trek-lower-decks-season-4',
        'md5': 'ffd7e9d03033d4483ea1923c5f80f433',
        'info_dict': {
            'id': 'official-trailer-star-trek-lower-decks-season-4',
            'ext': 'mp4',
            'title': 'Official Trailer | Star Trek: Lower Decks - Season 4',
            'alt_title': 'md5:dd7e3191aaaf9e95db16fc3abd5ef68b',
            'categories': ['TRAILERS'],
            'description': 'md5:563d7856ddab99bee7a5e50f45531757',
            'duration': 102,
            'release_date': '20230722',
            'release_timestamp': 1690033200,
            'series': 'Star Trek: Lower Decks',
            'series_id': 'star-trek-lower-decks',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
        },
    }, {
        'url': 'https://www.startrek.com/en-ca/videos/my-first-contact-senator-cory-booker',
        'md5': 'e3dac0f1e164457e4a8c9e2b400dc763',
        'info_dict': {
            'id': 'my-first-contact-senator-cory-booker',
            'ext': 'mp4',
            'title': 'My First Contact: Senator Cory Booker',
            'alt_title': 'md5:fe74a8bdb0afab421c6e159a7680db4d',
            'categories': ['MY FIRST CONTACT'],
            'description': 'md5:a3992ab3b3e0395925d71156bbc018ce',
            'duration': 78,
            'release_date': '20250401',
            'release_timestamp': 1743512400,
            'series_id': 'star-trek-the-original-series',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
        },
    }, {
        'url': 'https://www.startrek.com/videos/official-trailer-star-trek-lower-decks-season-4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        nextjs_data = self._search_nextjs_v13_data(webpage, video_id)
        video_data = traverse_obj(nextjs_data, (
            ..., 'video', 'data', {dict}, any, {require('video data')}))
        if youtube_id := video_data.get('youtube_video_id'):
            return self.url_result(youtube_id, YoutubeIE)

        series_id = traverse_obj(video_data, (
            'series_and_movies', ..., 'series_or_movie', 'slug', {str}, any))

        return {
            'id': video_id,
            'series': traverse_obj(nextjs_data, (
                ..., 'data', 'header', 'tab3', 'slices', ..., 'items',
                lambda _, v: traverse_obj(v, ('link', 'slug')) == series_id,
                'link_copy', {str}, any)),
            'series_id': series_id,
            **traverse_obj(video_data, {
                'title': ('title', ..., 'text', {clean_html}, any),
                'alt_title': ('subhead', ..., 'text', {clean_html}, any),
                'categories': ('category', 'data', 'category_name', {str.upper}, filter, all),
                'description': ('slices', ..., 'primary', 'content', ..., 'text', {clean_html}, any),
                'duration': ('duration', {parse_duration}),
                'release_timestamp': ('published', {parse_iso8601}),
                'subtitles': ({'url': 'legacy_subtitle_file'}, all, {subs_list_to_dict(lang='en')}),
                'thumbnail': ('poster_frame', 'url', {url_or_none}, {update_url(query=None)}),
                'url': ('legacy_video_url', {url_or_none}),
            }),
        }
