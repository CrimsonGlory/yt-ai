from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    traverse_obj,
)


class CtsNewsIE(InfoExtractor):
    IE_DESC = '華視新聞'
    _VALID_URL = r'https?://news\.cts\.com\.tw/[a-z]+/[a-z]+/\d+/(?P<id>\d+)\.html'
    _TESTS = [{
        # Article video is hosted on YouTube
        'url': 'https://news.cts.com.tw/cts/money/201501/201501291578003.html',
        'md5': '3d78249510be24bccf77fba8686b9f24',
        'info_dict': {
            'id': 'OVbfO7d0_hQ',
            'ext': 'mp4',
            'title': 'iPhone6熱銷 蘋果財報亮眼',
            'description': 'md5:f395d4f485487bb0f992ed2c4b07aa7d',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'timestamp': 1422514034,
            'upload_date': '20150129',
            'uploader': '華視新聞 CH52',
            'uploader_id': '@CtsTw',
            'uploader_url': 'https://www.youtube.com/@CtsTw',
            'channel': '華視新聞 CH52',
            'channel_id': 'UCDCJyLpbfgeVE9iZiEam-Kg',
            'channel_url': 'https://www.youtube.com/channel/UCDCJyLpbfgeVE9iZiEam-Kg',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'duration': 50,
            'view_count': int,
            'age_limit': 0,
            'availability': 'public',
            'live_status': 'not_live',
            'playable_in_embed': True,
            'media_type': 'video',
            'categories': ['News & Politics'],
            'tags': ['華視', '新聞', 'iPhone6 IPHONE 蘋果 蘋概股'],
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
        'url': 'http://news.cts.com.tw/cts/international/201501/201501291578109.html',
        'skip': 'Native CTSPlayer videos are no longer available',
        'md5': 'a9875cb790252b08431186d741beaabe',
        'info_dict': {
            'id': '201501291578109',
            'ext': 'mp4',
            'title': '以色列.真主黨交火 3人死亡 - 華視新聞網',
            'description': '以色列和黎巴嫩真主黨，爆發五年最嚴重衝突，雙方砲轟交火，兩名以軍死亡，還有一名西班牙籍的聯合國維和人員也不幸罹難。大陸陝西、河南、安徽、江蘇和湖北五個省份出現大暴雪，嚴重影響陸空交通，不過九華山卻出現...',
            'timestamp': 1422528540,
            'upload_date': '20150129',
        },
    }, {
        'url': 'http://news.cts.com.tw/cts/international/201309/201309031304098.html',
        'skip': 'Native CTSPlayer videos are no longer available',
        'md5': '3aee7e0df7cdff94e43581f54c22619e',
        'info_dict': {
            'id': '201309031304098',
            'ext': 'mp4',
            'title': '韓國31歲童顏男 貌如十多歲小孩 - 華視新聞網',
            'description': '越有年紀的人，越希望看起來年輕一點，而南韓卻有一位31歲的男子，看起來像是11、12歲的小孩，身...',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1378205880,
            'upload_date': '20130903',
        },
    }]

    def _real_extract(self, url):
        news_id = self._match_id(url)
        article = self._download_json(
            f'https://www.cts.com.tw/api/news/{news_id}', news_id)
        youtube_id = traverse_obj(article, ('data', 'article', 'youtubeId', {str}))
        if not youtube_id:
            raise ExtractorError('This news article does not contain a video', expected=True)

        return self.url_result(youtube_id, YoutubeIE, youtube_id)
