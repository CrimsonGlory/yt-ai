from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class KankaNewsIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = (
        r'https?://(?:www\.|m\.)?kankanews\.com/a/\d+-\d+-\d+/(?P<id>\d+)\.shtml',
        r'https?://(?:www\.|m\.)?kankanews\.com/detail/(?P<id>[\w-]+)',
    )
    _TESTS = [{
        'url': 'https://www.kankanews.com/a/2022-11-08/00310276054.shtml?appid=1088227',
        'md5': '05e126513c74b1258d657452a6f4eef9',
        'info_dict': {
            'id': '4485057',
            'ext': 'mp4',
            'url': 'http://mediaplay.kksmg.com/2022/11/08/h264_450k_mp4_1a388ad771e0e4cc28b0da44d245054e_ncm.mp4',
            'title': '视频｜第23个中国记者节，我们在进博切蛋糕',
            'display_id': '00310276054',
            'description': 'md5:4bd4d3ac9654a0686f4b03178fc94ee2',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 33.4,
            'timestamp': 1667895544,
            'upload_date': '20221108',
            'uploader': '看呀STV',
        },
    }, {
        'url': 'https://www.kankanews.com/detail/PbwRzE9qow4',
        'only_matching': True,
    }, {
        'url': 'https://m.kankanews.com/detail/PbwRzE9qow4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        news = traverse_obj(
            self._search_nuxt_data(webpage, display_id),
            ('newsDetail', {dict}, {require('news detail')}))

        return {
            'display_id': display_id,
            **traverse_obj(news, {
                'id': ('video_info', 'id', {str_or_none}),
                'url': ('video_info', 'play_url', {url_or_none}, {require('video URL')}),
                'title': ((('share_info', 'title'), 'title'), {str}, any),
                'description': ('summary', {str}),
                'thumbnail': ((('video_info', 'cover'), 'cover'), {url_or_none}, any),
                'duration': ('video_info', 'duration', {float_or_none(scale=1000)}),
                'timestamp': ('publish_time', {int_or_none}),
                'uploader': ('kankan_info', 'name', {str}),
            }),
        }
