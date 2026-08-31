from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    smuggle_url,
)


class AFLIE(InfoExtractor):
    IE_NAME = 'afl'
    IE_DESC = 'Australian Football League'
    _VALID_URL = r'https?://(?:www\.)?afl\.com\.au/(?:[^/?#]+/)*video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.afl.com.au/video/1600035/lloydy-ranks-the-bottom-ten-teams-most-likely-to-rise-look-away-saints-fans',
        'md5': '61f237d9badd4988b9d4847c7552b6ed',
        'info_dict': {
            'id': '6404336128112',
            'ext': 'mp4',
            'title': 'Lloydy ranks the bottom ten teams most likely to rise, look away Saints fans',
            'description': 'Matthew Lloyd nominates out of the ten teams not playing in September who he thinks will bounce',
            'duration': 97.6,
            'timestamp': 1788140689,
            'upload_date': '20260831',
            'uploader_id': '6057984922001',
            'thumbnail': r're:https?://.+\.jpg',
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://www.afl.com.au/video/1600035',
        'only_matching': True,
    }, {
        'url': 'https://www.afl.com.au/aflw/video/1600030/w-daily-the-no2-seed-growth-from-the-dockers-strange-choices-at-the-pies',
        'only_matching': True,
    }]
    _ACCOUNT_ID = '6057984922001'
    _PLAYER_ID = 'pFcMhmjx5'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_tag = self._search_regex(
            r'(<video(?:-js)?\b[^>]*\bdata-video-id=["\']?\d+[^>]*>)',
            webpage, 'brightcove player', default=None)
        attrs = extract_attributes(video_tag) if video_tag else {}
        video_id = attrs.get('data-video-id')
        if video_id:
            account_id = attrs.get('data-account') or self._ACCOUNT_ID
            player_id = attrs.get('data-player') or self._PLAYER_ID
            embed = attrs.get('data-embed') or 'default'
            bc_url = f'https://players.brightcove.net/{account_id}/{player_id}_{embed}/index.html?videoId={video_id}'
        else:
            bc_url = BrightcoveNewIE._extract_url(self, webpage)
            video_id = display_id
        if not bc_url:
            raise ExtractorError('Unable to extract Brightcove video', expected=True)

        return self.url_result(
            smuggle_url(bc_url, {'referrer': url}), BrightcoveNewIE, video_id)
