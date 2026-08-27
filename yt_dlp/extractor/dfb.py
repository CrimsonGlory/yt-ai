from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import ExtractorError
from ..utils.traversal import traverse_obj


class DFBIE(InfoExtractor):
    IE_NAME = 'tv.dfb.de'
    _VALID_URL = (
        r'https?://tv\.dfb\.de/video/(?P<display_id>[^/]+)/(?P<id>\d+)',
        r'https?://(?:www\.)?dfb\.de/news/(?P<id>[^/?#]*video[^/?#]*)',
    )
    _TESTS = [{
        'url': 'https://www.dfb.de/news/video-ungeschlagen-durch-die-wm-qualifikation',
        'md5': '4b21d7a837aa8f5443d7e8fd711bce95',
        'info_dict': {
            'id': 'VzEMKMkWYN8',
            'ext': 'mp4',
            'title': 'UNBEATEN in the WC Qualifier! | Slovenia vs Germany 0-2 | Highlights | World Cup Qualifier',
            'description': 'md5:243f142976bbcd69fff0317719482741',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'timestamp': 1781033108,
            'upload_date': '20260609',
            'uploader': 'DFB',
            'uploader_id': '@DFB',
            'uploader_url': 'https://www.youtube.com/@DFB',
            'channel': 'DFB',
            'channel_id': 'UCfMo0xj-sbdzHuzxvKdu1hw',
            'channel_url': 'https://www.youtube.com/channel/UCfMo0xj-sbdzHuzxvKdu1hw',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'duration': 180,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'categories': ['Sports'],
            'tags': ['DFB', 'DFB TV', 'Deutscher Fußball-Bund', 'Fußball', 'prasnikar', 'martinez'],
            'age_limit': 0,
            'availability': 'public',
            'live_status': 'not_live',
            'playable_in_embed': False,
            'media_type': 'video',
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
        'url': 'http://tv.dfb.de/video/u-19-em-stimmen-zum-spiel-gegen-russland/11633/',
        'md5': 'ac0f98a52a330f700b4b3034ad240649',
        'info_dict': {
            'id': '11633',
            'display_id': 'u-19-em-stimmen-zum-spiel-gegen-russland',
            'ext': 'mp4',
            'title': 'U 19-EM: Stimmen zum Spiel gegen Russland',
            'upload_date': '20150714',
        },
        'skip': 'tv.dfb.de now redirects to www.dfb.de; old player API is gone',
    }, {
        'url': 'https://www.dfb.de/news/video-torspektakel-in-freiburg',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        if mobj.groupdict().get('display_id'):
            raise ExtractorError(
                'tv.dfb.de has been shut down; videos are now YouTube embeds on dfb.de news pages',
                expected=True)

        page = self._download_json(
            f'https://www.dfb.de/page-data/news/{video_id}/page-data.json', video_id)
        content_raw = traverse_obj(page, ('result', 'data', 'page', 'internal', 'content', {str}))
        if not content_raw:
            raise ExtractorError('Unable to extract page content')
        content = self._parse_json(content_raw, video_id)

        youtube_id = None
        for item in traverse_obj(content, ('content', 'body', ...)) or []:
            if isinstance(item, str):
                item = self._parse_json(item, video_id, fatal=False)
            youtube_id = traverse_obj(item, 'video_embed_id', {str})
            if youtube_id:
                break
        if not youtube_id:
            raise ExtractorError('This article does not contain a video', expected=True)

        return self.url_result(
            f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id)
