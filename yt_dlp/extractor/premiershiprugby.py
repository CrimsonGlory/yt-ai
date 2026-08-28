from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PremiershipRugbyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?premiershiprugby\.com/(?:watch|video)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.premiershiprugby.com/watch/highlights-bath-rugby-v-exeter-chiefs-play-offs',
        'md5': 'af9e3480994adab0afad9fd398d5d085',
        'info_dict': {
            'id': '_S7B9ViBE-M',
            'ext': 'mp4',
            'title': 'Bath Rugby v Exeter Chiefs | EXTENDED HIGHLIGHTS | Gallagher PREM Rugby Play-Offs',
            'description': 'md5:8fee39b02f9e268e4fc208b8996d965f',
            'duration': 607,
            'uploader': 'PREM Rugby',
            'uploader_id': '@PREM-Rugby',
            'uploader_url': 'https://www.youtube.com/@PREM-Rugby',
            'channel': 'PREM Rugby',
            'channel_id': 'UCLbW1klIl3T1XCp8hHYZGMw',
            'channel_url': 'https://www.youtube.com/channel/UCLbW1klIl3T1XCp8hHYZGMw',
            'channel_follower_count': int,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1781522186,
            'upload_date': '20260615',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Sports'],
            'tags': 'count:23',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
        },
        'add_ie': ['Youtube'],
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
        ],
    }, {
        'url': 'https://www.premiershiprugby.com/video/highlights-bath-rugby-v-exeter-chiefs-play-offs',
        'only_matching': True,
    }, {
        'url': 'https://www.premiershiprugby.com/watch/full-match-harlequins-v-newcastle-falcons',
        'skip': 'video gone',
        'info_dict': {
            'id': '0_mbkb7ldt',
            'title': 'Full Match: Harlequins v Newcastle Falcons',
            'ext': 'mp4',
            'thumbnail': 'https://open.http.mp.streamamg.com/p/3000914/sp/300091400/thumbnail/entry_id/0_mbkb7ldt//width/960/height/540/type/1/quality/75',
            'duration': 6093.0,
            'tags': ['video'],
            'categories': ['Full Match', 'Harlequins', 'Newcastle Falcons', 'gallaher premiership'],
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        json_data = self._download_json(
            f'https://article-cms-api.incrowdsports.com/v2/articles/slug/{display_id}',
            display_id, query={'clientId': 'PRL'})['data']['article']
        content = traverse_obj(json_data, ('heroMedia', 'content', {dict})) or {}

        video_url = url_or_none(content.get('link')) or url_or_none(content.get('videoLink'))
        if not video_url:
            raise ExtractorError('No video found', expected=True)
        if YoutubeIE.suitable(video_url):
            return self.url_result(video_url, YoutubeIE)

        video_url = video_url.replace('/protocol/http/', '/protocol/https/')
        formats, subs = self._extract_m3u8_formats_and_subtitles(
            video_url, display_id)

        return {
            'id': content.get('sourceSystemId') or display_id,
            'display_id': display_id,
            'title': traverse_obj(json_data, ('heroMedia', 'title')),
            'formats': formats,
            'subtitles': subs,
            'thumbnail': url_or_none(content.get('videoThumbnail')),
            'duration': int_or_none(traverse_obj(content, ('metadata', 'msDuration')), scale=1000),
            'tags': json_data.get('tags'),
            'categories': traverse_obj(json_data, ('categories', ..., 'text')),
        }
