from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    parse_iso8601,
    traverse_obj,
    urljoin,
    variadic,
)


class NoicePodcastIE(InfoExtractor):
    _VALID_URL = r'https?://open\.noice\.id/content/(?P<id>[a-fA-F0-9-]+)'
    _API_BASE = 'https://api.beta.noice.id'
    _TESTS = [{
        'url': 'https://open.noice.id/content/7694bb04-ff0f-40fa-a60b-5b39f29584b2',
        'md5': '36088be258d98af8626d057c05354bd0',
        'info_dict': {
            'id': '7694bb04-ff0f-40fa-a60b-5b39f29584b2',
            'ext': 'mp4',
            'season': 'Season 1',
            'description': 'md5:58d1274e6857b6fbbecf47075885380d',
            'release_date': '20221115',
            'timestamp': 1668496642,
            'season_number': 1,
            'upload_date': '20221115',
            'release_timestamp': 1668496642,
            'title': 'Eps 1. Belajar dari Wishnutama: Kreatif Bukan Followers! (bersama Wishnutama)',
            'modified_date': '20260416',
            'categories': ['Bisnis'],
            'duration': 2619,
            'modified_timestamp': 1776303535,
            'thumbnail': 'https://images.noiceid.cc/catalog/content-1668496302560',
            'channel_id': '9dab1024-5b92-4265-ae1c-63da87359832',
            'like_count': int,
            'channel': 'Noice Space Talks',
            'comment_count': int,
            'dislike_count': int,
            'channel_follower_count': int,
        },
    }, {
        'url': 'https://open.noice.id/content/222134e4-99f2-456f-b8a2-b8be404bf063',
        'params': {'skip_download': True},
        'info_dict': {
            'id': '222134e4-99f2-456f-b8a2-b8be404bf063',
            'ext': 'm4a',
            'release_timestamp': 1653488220,
            'description': 'md5:35074f6190cef52b05dd133bb2ef460e',
            'upload_date': '20220525',
            'timestamp': 1653460637,
            'release_date': '20220525',
            'thumbnail': 'https://images.noiceid.cc/catalog/content-1653460337625',
            'title': 'Eps 1: Dijodohin Sama Anak Pak RT',
            'modified_timestamp': 1776303517,
            'season_number': 1,
            'modified_date': '20260416',
            'categories': ['Fiksi'],
            'duration': 1830,
            'season': 'Season 1',
            'channel_id': '60193f6b-d24d-4b23-913b-ceed5a731e74',
            'dislike_count': int,
            'like_count': int,
            'comment_count': int,
            'channel': 'Dear Jerome',
            'channel_follower_count': int,
        },
    }]

    def _progressive_url_from_hls(self, m3u8_url, video_id):
        """Return the underlying MP4 if an HLS playlist is a byte-range index of one file."""
        if not m3u8_url or determine_ext(m3u8_url) != 'm3u8':
            return None
        manifest = self._download_webpage(
            m3u8_url, video_id, note=False, fatal=False)
        if not manifest:
            return None
        segment_urls = []
        for line in manifest.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('#EXT-X-MAP:'):
                uri = self._search_regex(
                    r'URI="([^"]+)"', line, 'map uri', default=None)
                if uri:
                    segment_urls.append(urljoin(m3u8_url, uri))
                continue
            if line.startswith('#'):
                continue
            segment_urls.append(urljoin(m3u8_url, line))
        unique = dict.fromkeys(filter(None, segment_urls))
        if len(unique) == 1:
            return next(iter(unique))
        return None

    def _get_formats_and_subtitles(self, media_url, video_id):
        formats, subtitles = [], {}
        for url in variadic(media_url):
            ext = determine_ext(url)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    url, video_id, fatal=False)
                progressive_urls = {}
                for fmt in fmts:
                    m3u8_url = fmt.get('url')
                    if m3u8_url not in progressive_urls:
                        progressive_urls[m3u8_url] = self._progressive_url_from_hls(
                            m3u8_url, video_id)
                    progressive_url = progressive_urls[m3u8_url]
                    if progressive_url:
                        fmt['url'] = progressive_url
                        fmt['protocol'] = 'https'
                        fmt.pop('manifest_url', None)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append({
                    'url': url,
                    'ext': 'mp3',
                    'vcodec': 'none',
                    'acodec': 'mp3',
                })
        return formats, subtitles

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        page_props = traverse_obj(
            self._search_nextjs_data(webpage, display_id),
            ('props', 'pageProps', {dict})) or {}
        guest_token_response = page_props.get('guestTokenResponse')
        if isinstance(guest_token_response, str):
            guest_token_response = self._parse_json(
                guest_token_response, display_id)
        token = traverse_obj(
            guest_token_response, ('guestToken', {str}), ('accessToken', {str}))
        if not token:
            raise ExtractorError('Unable to extract guest token', expected=True)

        content = self._download_json(
            f'{self._API_BASE}/catalog-api/content/{display_id}',
            display_id, headers={'Authorization': f'Bearer {token}'})['data']

        media_url_list = traverse_obj(content, (('videoUrl', 'url', 'rawContentUrl'), ))
        formats, subtitles = self._get_formats_and_subtitles(media_url_list, display_id)

        return {
            'id': content.get('id') or display_id,
            'title': content.get('title') or self._html_search_meta('og:title', webpage),
            'formats': formats,
            'subtitles': subtitles,
            'description': (content.get('description') or clean_html(content.get('htmlDescription'))
                            or self._html_search_meta(['description', 'og:description'], webpage)),
            'thumbnail': content.get('image') or self._html_search_meta('og:image', webpage),
            'timestamp': parse_iso8601(content.get('createdAt')),
            'release_timestamp': parse_iso8601(content.get('publishedAt')),
            'modified_timestamp': parse_iso8601(
                content.get('updatedAt') or self._html_search_meta('og:updated_time', webpage)),
            'duration': int_or_none(content.get('duration')),
            'categories': traverse_obj(content, ('genres', ..., 'name', {str.strip})),
            'season': content.get('seasonName'),
            'season_number': int_or_none(content.get('seasonNumber')),
            'channel': traverse_obj(content, ('catalog', 'title')),
            'channel_id': traverse_obj(content, ('catalog', 'id'), 'catalogId'),
            **traverse_obj(content, ('meta', 'aggregations', {
                'like_count': 'likes',
                'dislike_count': 'dislikes',
                'comment_count': 'comments',
                'channel_follower_count': 'followers',
            })),
        }
