from .common import InfoExtractor
from .dailymotion import DailymotionIE
from ..utils import (
    ExtractorError,
    urljoin,
)


class JeuxVideoIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://.*?\.jeuxvideo\.com/.*/(?P<id>[^/?#]+)\.htm'

    _TESTS = [{
        'url': 'http://www.jeuxvideo.com/reportages-videos-jeux/0004/00046170/tearaway-playstation-vita-gc-2013-tearaway-nous-presente-ses-papiers-d-identite-00115182.htm',
        'md5': '6beb93037b15afacb0bf4c63c5e09c91',
        'info_dict': {
            'id': 'x89k839',
            'ext': 'mp4',
            'title': 'Tearaway : GC 2013 : Tearaway nous présente ses papiers d\'identité',
            'description': '',
            'thumbnail': r're:https://s\d+\.dmcdn\.net/v/.+',
            'duration': 252,
            'timestamp': 1648736904,
            'upload_date': '20220331',
            'uploader': 'JeuxVideo.com',
            'uploader_id': 'x198m7x',
            'view_count': int,
            'like_count': int,
            'age_limit': 0,
            'tags': [],
        },
        'add_ie': ['Dailymotion'],
    }, {
        'url': 'https://www.jeuxvideo.com/videos/2097535/star-wars-galactic-racer-une-premiere-prise-en-main-pleine-de-promesses.htm',
        'only_matching': True,
    }, {
        'url': 'http://www.jeuxvideo.com/videos/chroniques/434220/l-histoire-du-jeu-video-la-saturn.htm',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)

        config_path = self._html_search_regex(
            r'data-src-video=(["\'])(?P<url>/contenu/medias/video(?:-config|\.php)\?.*?)\1',
            webpage, 'config URL', default=None, group='url')
        if not config_path:
            config_path = self._html_search_regex(
                r'data-src(?:set-video)?=(["\'])(?P<url>/contenu/medias/video(?:-config|\.php)\?.*?)\1',
                webpage, 'config URL', group='url')
        config_url = urljoin('https://www.jeuxvideo.com', config_path)

        video_id = self._search_regex(r'[?&]id=(\d+)', config_url, 'video ID')
        config = self._download_json(
            config_url, video_id, 'Downloading JSON config', impersonate=True)

        dm_id = (config.get('options') or {}).get('video') or (config.get('dataGa4') or {}).get('video_id')
        if config.get('isDailymotion') or dm_id:
            if not dm_id:
                raise ExtractorError('Unable to extract Dailymotion video ID', expected=True)
            return self.url_result(
                f'https://www.dailymotion.com/video/{dm_id}',
                ie=DailymotionIE, video_id=dm_id)

        formats = [{
            'url': source['file'],
            'format_id': source['label'],
            'resolution': source['label'],
        } for source in reversed(config['sources'])]

        return {
            'id': video_id,
            'title': self._html_search_meta('name', webpage) or self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': config.get('image'),
        }
