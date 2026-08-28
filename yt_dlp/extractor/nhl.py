from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import ExtractorError


class NHLIE(InfoExtractor):
    IE_NAME = 'nhl.com'
    _VALID_URL = (
        r'https?://(?:www\.)?nhl\.com/(?:[^/]+/)*video(?:/topic/[^/]+)?/(?P<id>[^/?#]*\d+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?(?:nhl|wch2016)\.com/(?:[^/]+/)*c-(?P<id>\d+)',
    )
    _TESTS = [{
        'url': 'https://www.nhl.com/video/32-in-32-philadelphia-flyers-6403590907112',
        'md5': '8a956e6b03436f606f7d097d6284986e',
        'info_dict': {
            'id': '6403590907112',
            'ext': 'mp4',
            'title': '32 in 32: Philadelphia Flyers',
            'description': 'Inside look at the Philadelphia Flyers ahead of the 2026-27 season',
            'uploader_id': '6415718365001',
            'duration': 95.812,
            'timestamp': 1786977820,
            'upload_date': '20260817',
            'thumbnail': r're:https?://.+\.jpg',
            'tags': ['taxonomy/2026-27', 'taxonomy/32-in-32', 'taxonomy/nhl-created', 'taxonomy/nhl'],
        },
        'params': {'format': 'b[protocol=https]'},
    }, {
        # type=video
        'url': 'https://www.nhl.com/video/anisimov-cleans-up-mess/t-277752844/c-43663503',
        'skip': 'old bamcontent API is gone',
        'md5': '0f7b9a8f986fb4b4eeeece9a56416eaf',
        'info_dict': {
            'id': '43663503',
            'ext': 'mp4',
            'title': 'Anisimov cleans up mess',
            'description': 'md5:a02354acdfe900e940ce40706939ca63',
            'timestamp': 1461288600,
            'upload_date': '20160422',
        },
    }, {
        # type=article
        'url': 'https://www.nhl.com/news/dennis-wideman-suspended/c-278258934',
        'skip': 'old bamcontent API is gone',
        'md5': '1f39f4ea74c1394dea110699a25b366c',
        'info_dict': {
            'id': '40784403',
            'ext': 'mp4',
            'title': 'Wideman suspended by NHL',
            'description': 'Flames defenseman Dennis Wideman was banned 20 games for violation of Rule 40 (Physical Abuse of Officials)',
            'upload_date': '20160204',
            'timestamp': 1454544904,
        },
    }, {
        # Some m3u8 URLs are invalid (https://github.com/ytdl-org/youtube-dl/issues/10713)
        'url': 'https://www.nhl.com/predators/video/poile-laviolette-on-subban-trade/t-277437416/c-44315003',
        'skip': 'old bamcontent API is gone',
        'md5': '50b2bb47f405121484dda3ccbea25459',
        'info_dict': {
            'id': '44315003',
            'ext': 'mp4',
            'title': 'Poile, Laviolette on Subban trade',
            'description': 'General manager David Poile and head coach Peter Laviolette share their thoughts on acquiring P.K. Subban from Montreal (06/29/16)',
            'timestamp': 1467242866,
            'upload_date': '20160629',
        },
    }, {
        'url': 'https://www.nhl.com/video/topic/puck-personality/puck-personality-free-ticket-to-space-6353234264112',
        'only_matching': True,
    }, {
        'url': 'https://www.nhl.com/predators/video/media-availability-ross-colton-6401146595112',
        'only_matching': True,
    }, {
        'url': 'https://www.wch2016.com/video/caneur-best-of-game-2-micd-up/t-281230378/c-44983703',
        'only_matching': True,
    }, {
        'url': 'https://www.wch2016.com/news/3-stars-team-europe-vs-team-canada/c-282195068',
        'only_matching': True,
    }]
    _BRIGHTCOVE_URL_TMPL = 'https://players.brightcove.net/%s/%s_default/index.html?videoId=%s'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        brightcove_url = self._search_regex(
            r'(https?://players\.brightcove\.net/\d+/[\w]+/index\.html\?videoId=\d+)',
            webpage, 'brightcove URL', default=None)
        if not brightcove_url:
            video_id = self._search_regex(
                r'brightcoveVideoId["\']?\s*[:=]\s*["\'](\d+)',
                webpage, 'brightcove id', default=None)
            if video_id:
                account_id = self._search_regex(
                    r'brightcoveAccount["\']?\s*[:=]\s*["\'](\d+)',
                    webpage, 'brightcove account', default='6415718365001')
                player_id = self._search_regex(
                    r'brightcovePlayer["\']?\s*[:=]\s*["\']([^"\']+)',
                    webpage, 'brightcove player', default='default')
                brightcove_url = self._BRIGHTCOVE_URL_TMPL % (account_id, player_id, video_id)
        if not brightcove_url:
            raise ExtractorError('This NHL video is no longer available', expected=True)

        return self.url_result(brightcove_url, BrightcoveNewIE)
