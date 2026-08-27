from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ClubicIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?clubic\.com/video(?:/(?:shorts|(?:[^/?#]+/)*video[^/?#]*-(?P<id>\d+)\.html))?/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://www.clubic.com/video?v=M3AtXq8Ooro',
        'md5': 'c75c53f7695e6f32c720ecd8906e4b09',
        'info_dict': {
            'id': 'M3AtXq8Ooro',
            'ext': 'mp4',
            'title': "L'iPhone 20 serait tout en verre",
            'description': "L'iPhone 20 serait tout en verre\n\n#iphone #apple #iphone20",
            'thumbnail': r're:https?://i\.ytimg\.com/vi/.+',
            'timestamp': 1787680846,
            'upload_date': '20260825',
            'uploader': 'Clubic',
            'uploader_id': '@Clubic',
            'uploader_url': 'https://www.youtube.com/@Clubic',
            'channel': 'Clubic',
            'channel_id': 'UCIorGsaWVmlkpNsngTQPDAg',
            'channel_url': 'https://www.youtube.com/channel/UCIorGsaWVmlkpNsngTQPDAg',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'tags': [],
            'duration': 56,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'categories': ['Science & Technology'],
            'age_limit': 0,
            'availability': 'public',
            'live_status': 'not_live',
            'playable_in_embed': True,
            'media_type': 'short',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
        ],
    }, {
        'url': 'http://www.clubic.com/video/clubic-week/video-clubic-week-2-0-le-fbi-se-lance-dans-la-photo-d-identite-448474.html',
        'skip': 'Old M6Web player videos are gone',
        'md5': '1592b694ba586036efac1776b0b43cd3',
        'info_dict': {
            'id': '448474',
            'ext': 'mp4',
            'title': 'Clubic Week 2.0 : le FBI se lance dans la photo d\u0092identité',
            'description': 're:Gueule de bois chez Nokia. Le constructeur a indiqué cette.*',
            'thumbnail': r're:^http://img\.clubic\.com/.*\.jpg$',
        },
    }, {
        'url': 'http://www.clubic.com/video/video-clubic-week-2-0-apple-iphone-6s-et-plus-mais-surtout-le-pencil-469792.html',
        'only_matching': True,
    }, {
        'url': 'https://www.clubic.com/video',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        legacy_id = self._match_valid_url(url).group('id')
        if legacy_id:
            raise ExtractorError('This video is no longer available', expected=True)

        requested_id = self._search_regex(
            r'[?&](?:v|id)=([\w-]{11})(?:[&#]|$)', url, 'youtube id', default=None)

        data = self._download_json(
            'https://www.clubic.com/video/shorts', requested_id or 'shorts',
            note='Downloading Clubic shorts feed')
        items = traverse_obj(data, ('items', ..., {dict})) or []
        item = next((
            entry for entry in items if entry.get('id') == requested_id
        ), None) if requested_id else (items[0] if items else None)
        if requested_id and not item:
            item = {'id': requested_id}

        youtube_id = item.get('id') if item else None
        if not youtube_id:
            raise ExtractorError('No Clubic videos found', expected=True)

        return self.url_result(
            item.get('url') or f'https://www.youtube.com/watch?v={youtube_id}',
            YoutubeIE, youtube_id, item.get('title'), url_transparent=True,
            description=item.get('description'),
            thumbnail=url_or_none(item.get('thumbnailUrl')),
            timestamp=parse_iso8601(item.get('publishedAt')))
