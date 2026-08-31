import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    smuggle_url,
    urljoin,
)
from ..utils.traversal import traverse_obj


class ATPTourIE(InfoExtractor):
    IE_NAME = 'atptour'
    IE_DESC = 'ATP Tour'
    _VALID_URL = r'https?://(?:www\.)?atptour\.com/(?:[a-z]{2}/)?(?:video|news)/(?P<id>[^/?#]+)'
    _ACCOUNT_ID = '6057277721001'
    _PLAYER_ID = 'xO4H0ZXngd_default'
    _TESTS = [{
        'url': 'https://www.atptour.com/en/video/highlights-buse-eases-past-fery-to-clinch-winston-salem-2026-trophy',
        'md5': '2b8628e3fb434fec76f3c197b9e2216a',
        'info_dict': {
            'id': '6404280828112',
            'ext': 'mp4',
            'title': 'Highlights: Buse eases past Fery to clinch Winston-Salem 2026 trophy',
            'description': 'Watch Ignacio Buse cruise past Arthur Fery Saturday to win the Winston-Salem Open crown. Watch live & on-demand at tennistv.com.',
            'duration': 120.469,
            'timestamp': 1788038886,
            'upload_date': '20260829',
            'uploader_id': '6057277721001',
            'thumbnail': r're:https?://.+\.jpg',
            'tags': list,
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://www.atptour.com/en/video/highlights-svajda-earns-highestranked-win-of-career-vs-cerundolo-winstonsalem-2024',
        'only_matching': True,
    }, {
        'url': 'https://www.atptour.com/en/news/sinner-zverev-cincinnati-2024-sf',
        'only_matching': True,
    }, {
        'url': 'https://www.atptour.com/es/video/highlights-buse-eases-past-fery-to-clinch-winston-salem-2026-trophy',
        'only_matching': True,
    }]

    def _brightcove_result(self, video_id, url, account_id=None, player_id=None):
        account_id = account_id or self._ACCOUNT_ID
        player_id = player_id or self._PLAYER_ID
        if '_' not in player_id:
            player_id = f'{player_id}_default'
        return self.url_result(
            smuggle_url(
                f'https://players.brightcove.net/{account_id}/{player_id}/index.html?videoId={video_id}',
                {'referrer': url}),
            BrightcoveNewIE, video_id)

    def _extract_embedded_videos(self, webpage, url):
        entries, seen = [], set()

        for video_tag in re.finditer(r'<video(?:-js)?\b[^>]*>', webpage):
            attrs = extract_attributes(video_tag.group(0))
            video_id = attrs.get('data-video-id')
            if not video_id or not video_id.isdigit() or video_id in seen:
                continue
            seen.add(video_id)
            entries.append(self._brightcove_result(
                video_id, url, attrs.get('data-account'), attrs.get('data-player')))

        for mobj in re.finditer(
                r'(?:https?:)?//players\.brightcove\.net/(\d+)/([^/?#]+)/index\.html\?[^"\'>\s]*videoId=(\d+)',
                webpage):
            account_id, player_id, video_id = mobj.groups()
            if video_id in seen:
                continue
            seen.add(video_id)
            entries.append(self._brightcove_result(video_id, url, account_id, player_id))

        return entries

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)

        entries = self._extract_embedded_videos(webpage, url)
        if len(entries) == 1:
            return entries[0]
        if len(entries) > 1:
            return self.playlist_result(
                entries, display_id, self._og_search_title(webpage, default=None),
                self._og_search_description(webpage, default=None))

        endpoint = self._search_regex(
            (r'class="atp_featured-videos-endpoint"[^>]*\bvalue="([^"]+)"',
             r'(/[^"\']+/-/tour/videos/getcurrentrelatedvideos\?currentItem=\{?[0-9A-Fa-f-]{36}\}?)'),
            webpage, 'videos endpoint')
        data = self._download_json(urljoin(url, endpoint), display_id, impersonate=True)
        video = traverse_obj(data, (
            'content', lambda _, v: display_id in (v.get('url') or '') or display_id in (v.get('linkOverride') or ''), any),
            ('content', 0))
        video_id = traverse_obj(video, ('videoId', {str}))
        if not video_id:
            raise ExtractorError('Unable to extract Brightcove video', expected=True)

        return self._brightcove_result(
            video_id, url,
            traverse_obj(video, ('videoAccountId', {str})),
            traverse_obj(video, ('videoPlayerId', {str})))
