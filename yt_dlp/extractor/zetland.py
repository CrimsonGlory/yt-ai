from .common import InfoExtractor
from ..utils import (
    int_or_none,
    merge_dicts,
    unified_timestamp,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class ZetlandDKArticleIE(InfoExtractor):
    _VALID_URL = r'https?://www\.zetland\.dk/\w+/(?P<id>(?P<story_id>\w{8})-(?P<uploader_id>\w{8})-(?:\w{5}))'
    _TESTS = [{
        'url': 'https://www.zetland.dk/historie/sO9aq2MY-a81VP3BY-66e69?utm_source=instagram&utm_medium=linkibio&utm_campaign=artikel',
        'md5': '4f1a802aaf86c296d63bd53a027c4be7',
        'info_dict': {
            'id': 'sO9aq2MY-a81VP3BY-66e69',
            'ext': 'opus',
            'title': 'Afsnit 1: “Det føltes som en kidnapning.” ',
            'description': 'md5:9619d426772c133f5abb26db27f26a01',
            'uploader': 'Helle Fuusager',
            'uploader_id': 'a81VP3BY',
            'uploader_url': 'https://www.zetland.dk/journalist/a81VP3BY',
            'thumbnail': r're:https://zetland\.imgix\.net/2aafe500-b14e-11ee-bf83-65d5e1283a57/Zetland_Image_1\.jpg',
            'series_id': '62d54630-e87b-4ab1-a255-8de58dbe1b14',
            'duration': 1596,
            'timestamp': 1705377592,
            'upload_date': '20240116',
            'release_timestamp': 1705377592,
            'release_date': '20240116',
            'modified_date': '20250121',
            'modified_timestamp': 1737476961,
        },
    }]

    def _extract_story_data(self, webpage, display_id):
        flight_chunk = traverse_obj(self._search_json(
            r'<script[^>]*>self\.__next_f\.push\(', webpage, 'next.js flight data',
            display_id, contains_pattern=r'\[(?s:.+)\]', end_pattern=r'\)\s*</script>',
            fatal=False), (1, {str}))
        story_data = self._search_json(
            r'"storyServer"\s*:', flight_chunk or '', 'story data', display_id, fatal=False)
        if story_data:
            return story_data
        return traverse_obj(
            self._search_nextjs_data(webpage, display_id, default={}),
            ('props', 'pageProps', 'initialState', 'consume', 'story', 'story', {dict})) or {}

    def _real_extract(self, url):
        display_id, uploader_id = self._match_valid_url(url).group('id', 'uploader_id')
        webpage = self._download_webpage(url, display_id)
        story_data = self._extract_story_data(webpage, display_id)

        formats = []
        for audio_url in traverse_obj(story_data, ('story_content', 'meta', 'audioFiles', ..., {url_or_none})):
            formats.append({
                'url': audio_url,
                'vcodec': 'none',
            })
        if not formats:
            self.raise_no_formats('No audio found', expected=True, video_id=display_id)

        return merge_dicts({
            'id': display_id,
            'formats': formats,
            'uploader_id': uploader_id,
        }, traverse_obj(story_data, {
            'title': ((('story_content', 'content', 'title'), 'title'), {str}),
            'uploader': ('sharer', 'name'),
            'uploader_id': ('sharer', 'sharer_id'),
            'uploader_url': ('authors', 0, 'links', 'share_url', {url_or_none}),
            'description': ('story_content', 'content', 'socialDescription'),
            'series_id': ('story_content', 'meta', 'seriesId'),
            'duration': ('audio_length', {int_or_none}),
            'release_timestamp': ('published_at', {unified_timestamp}),
            'modified_timestamp': ('revised_at', {unified_timestamp}),
            'thumbnail': ('cover_image', 'image', 'url', {lambda x: urljoin('https://zetland.imgix.net/', x)}),
        }, get_all=False), {
            'title': self._html_search_meta(['title', 'og:title', 'twitter:title'], webpage),
            'description': self._html_search_meta(['description', 'og:description', 'twitter:description'], webpage),
            'thumbnail': self._html_search_meta(['og:image', 'twitter:image'], webpage),
            'uploader': self._html_search_meta(['author'], webpage),
            'release_timestamp': unified_timestamp(self._html_search_meta(['article:published_time'], webpage)),
        }, self._search_json_ld(webpage, display_id, fatal=False))
