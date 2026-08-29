from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    url_or_none,
)


class WeiqiTVIE(InfoExtractor):
    IE_DESC = 'WQTV'
    _VALID_URL = r'https?://(?:www\.)?weiqitv\.com/(?:index/video_play\?videoId=|(?P<live>l(?:ive)?/)|v/)(?P<id>[A-Za-z0-9]+)'
    _TESTS = [{
        'url': 'http://www.weiqitv.com/v/197087678784296',
        'info_dict': {
            'id': '197087678784296',
            'ext': 'mp4',
            'title': '孟泰龄精品课第四课',
            'thumbnail': r're:https?://s0\.weiqitv\.com/resources/.+',
        },
        'skip': 'login required',
    }, {
        'url': 'http://www.weiqitv.com/l/179397515384792',
        'info_dict': {
            'id': '179397515384792',
            'ext': 'mp4',
            'title': '你和大师的距离只差两节课',
            'live_status': 'is_live',
        },
        'skip': 'live stream offline',
    }, {
        'url': 'http://www.weiqitv.com/live/179397515384792',
        'only_matching': True,
    }, {
        'url': 'http://www.weiqitv.com/index/video_play?videoId=53c744f09874f0e76a8b46f3',
        'skip': 'video gone',
        'md5': '26450599afd64c513bc77030ad15db44',
        'info_dict': {
            'id': '53c744f09874f0e76a8b46f3',
            'ext': 'mp4',
            'title': '2013年度盘点',
        },
    }, {
        'url': 'http://www.weiqitv.com/index/video_play?videoId=567379a2d4c36cca518b4569',
        'skip': 'video gone',
        'info_dict': {
            'id': '567379a2d4c36cca518b4569',
            'ext': 'mp4',
            'title': '民国围棋史',
        },
    }, {
        'url': 'http://www.weiqitv.com/index/video_play?videoId=5430220a9874f088658b4567',
        'skip': 'video gone',
        'info_dict': {
            'id': '5430220a9874f088658b4567',
            'ext': 'mp4',
            'title': '二路托过的手段和运用',
        },
    }]

    def _real_extract(self, url):
        # Site HTTPS certificate is expired; pages are served over HTTP.
        url = url.replace('https://', 'http://', 1)
        mobj = self._match_valid_url(url)
        video_id, is_live = mobj.group('id'), bool(mobj.group('live'))
        webpage = self._download_webpage(url, video_id)

        if 'mg-404' in webpage or '系统打挂了' in webpage:
            raise ExtractorError('This video is no longer available', expected=True)

        title = self._html_search_regex(
            r'<h1 class="mg-(?:video|live)-title">\s*([^<]+)',
            webpage, 'title', default=None)
        thumbnail = url_or_none(self._search_regex(
            r'(?:_vc\s*=\s*"|<video[^>]+poster=")(https?://[^"]+)',
            webpage, 'thumbnail', default=None))

        if is_live:
            hls_url = url_or_none(self._search_regex(
                r"var\s+_lyxu\s*=\s*'([^']+)'", webpage, 'live hls url', default=None))
            if not hls_url:
                if '请先登录' in webpage:
                    self.raise_login_required()
                raise ExtractorError('Unable to extract live stream URL', expected=True)
            formats = self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', live=True, fatal=False)
            if not formats:
                raise ExtractorError('Live stream is offline', expected=True)
            return {
                'id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'formats': formats,
                'is_live': True,
            }

        video_url = url_or_none(self._search_regex(
            r'_vu\s*=\s*(["\'])(?P<url>https?://.+?)\1',
            webpage, 'video url', default=None, group='url'))
        if not video_url:
            if '请先登录' in webpage or 'mg-video-play-login-btn' in webpage:
                self.raise_login_required()
            raise ExtractorError('Unable to extract video URL', expected=True)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': determine_ext(video_url, 'mp4'),
            'thumbnail': thumbnail,
        }
