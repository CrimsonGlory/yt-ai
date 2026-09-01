import re

from .common import InfoExtractor
from .txxx import TxxxIE
from ..utils import (
    ExtractorError,
    urljoin,
)


class PornzogIE(InfoExtractor):
    IE_DESC = 'pornzog.com'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?pornzog\.com/
        (?:video/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?/?|
           embed\.php\?(?:[^#]*&)?id=(?P<embed_id>\d+))
    '''
    _EMBED_HOST_MAP = {
        'videotxxx.com': 'txxx.com',
        'vid-vx.com': 'vxxx.com',
    }
    _TESTS = [{
        'url': 'https://pornzog.com/video/11952345/adina-arbour-cumshot-compilation-with-8-cumshots/',
        'md5': 'be1440a41de3802531b92c9414281509',
        'info_dict': {
            'id': '4811680',
            'display_id': '4811680',
            'ext': 'mp4',
            'title': 'Adina Arbour Cumshot Compilation with 8 cumshots',
            'uploader': 'ashley301418',
            'duration': 244,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'age_limit': 18,
            'thumbnail': r're:https?://.*',
        },
        'add_ie': [TxxxIE.ie_key()],
    }, {
        'url': 'https://pornzog.com/video/27423219/french-alt-babe-takes-double-vaginal-penetration/',
        'only_matching': True,
    }, {
        'url': 'https://www.pornzog.com/embed.php?id=27423219',
        'only_matching': True,
    }, {
        'url': 'https://pornzog.com/video/27421348/sa-premiere-fois-avec-deux-mecs-un-max-de-plaisir/',
        'only_matching': True,
    }]

    def _canonical_txxx_url(self, embed_url):
        mobj = re.search(
            r'https?://(?:www\.)?(?P<host>[\w.-]+)/(?:embed[-/]|videos?[-/])(?P<id>\d+)',
            embed_url)
        if not mobj:
            return None
        host = self._EMBED_HOST_MAP.get(mobj.group('host'), mobj.group('host'))
        if host not in TxxxIE._DOMAINS:
            return None
        return f'https://{host}/embed/{mobj.group("id")}/'

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id') or mobj.group('embed_id')
        webpage = self._download_webpage(url, video_id)

        embed_url = None
        for iframe in re.findall(r'<iframe[^>]+src=["\']([^"\']+)', webpage):
            iframe = urljoin(url, iframe)
            if 'pornzog.com' in iframe:
                continue
            embed_url = iframe
            break
        if not embed_url:
            raise ExtractorError('Unable to extract player iframe', expected=True)

        canonical = self._canonical_txxx_url(embed_url)
        if canonical:
            return self.url_result(canonical, TxxxIE)
        return self.url_result(embed_url)
