from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    unified_timestamp,
    urljoin,
)
from ..utils.traversal import traverse_obj


class MySpassIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?myspass\.de/(?:[^/?#]+/)*(?:(?:\d+-)+)?(?P<id>\d+)/?(?:$|[?#])'
    _MEDIA_BASE = 'https://1754936693.rsc.cdn77.org'
    _IMAGE_BASE = 'https://1403103913.rsc.cdn77.org'
    _TESTS = [{
        'url': 'https://www.myspass.de/clips/tv-total/puffi-verwoehnt-die-frauen/1-4763',
        'md5': '45653f1c72b68374b26884f9410db833',
        'info_dict': {
            'id': '4763',
            'ext': 'mp4',
            'title': 'Puffi verwöhnt die Frauen',
            'description': 'Happy internationalen Frauentag! Heute hat sich Puffi mal eine ganz besonderere Aufgabe gestellt: Die Damenwelt gerecht zu huldigen. Ob ihm das gelingt? Eva und Regina scheinen überzeugt!',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 564,
            'series': 'TV total',
        },
    }, {
        'url': 'https://www.myspass.de/folge/stromberg/stromberg-staffel-1/der-letzte-tag/2-1-38',
        'only_matching': True,
    }, {
        'url': 'http://www.myspass.de/myspass/shows/tvshows/absolute-mehrheit/Absolute-Mehrheit-vom-17022013-Die-Highlights-Teil-2--/11741/',
        'skip': 'video gone',
        'md5': '0b49f4844a068f8b33f4b7c88405862b',
        'info_dict': {
            'id': '11741',
            'ext': 'mp4',
            'description': 'md5:9f0db5044c8fe73f528a390498f7ce9b',
            'title': '17.02.2013 - Die Highlights, Teil 2',
            'thumbnail': r're:.*\.jpg',
            'duration': 323.0,
            'episode': '17.02.2013 - Die Highlights, Teil 2',
            'season_id': '544',
            'episode_number': 1,
            'series': 'Absolute Mehrheit',
            'season_number': 2,
            'season': 'Season 2',
        },
    }, {
        'url': 'https://www.myspass.de/shows/tvshows/tv-total/Novak-Puffovic-bei-bester-Laune--/44996/',
        'skip': 'video gone',
        'md5': 'eb28b7c5e254192046e86ebaf7deac8f',
        'info_dict': {
            'id': '44996',
            'ext': 'mp4',
            'description': 'md5:74c7f886e00834417f1e427ab0da6121',
            'title': 'Novak Puffovic bei bester Laune',
            'thumbnail': r're:.*\.jpg',
            'episode_number': 8,
            'episode': 'Novak Puffovic bei bester Laune',
            'series': 'TV total',
            'season': 'Season 19',
            'season_id': '987',
            'duration': 2941.0,
            'season_number': 19,
        },
    }, {
        'url': 'https://www.myspass.de/channels/tv-total-raabigramm/17033/20831/',
        'skip': 'video gone',
        'md5': '7b293a6b9f3a7acdd29304c8d0dbb7cc',
        'info_dict': {
            'id': '20831',
            'ext': 'mp4',
            'description': 'Gefühle pur: Schaut euch die ungeschnittene Version von Stefans Liebesbeweis an die Moderationsgrazie von Welt, Verona Feldbusch, an.',
            'title': 'Raabigramm Verona Feldbusch',
            'thumbnail': r're:.*\.jpg',
            'episode_number': 6,
            'episode': 'Raabigramm Verona Feldbusch',
            'series': 'TV total',
            'season': 'Season 1',
            'season_id': '34',
            'duration': 105.0,
            'season_number': 1,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video = traverse_obj(
            self._search_nextjs_data(webpage, video_id),
            ('props', 'pageProps', 'videoData', {dict}))
        if not video:
            raise ExtractorError('Unable to extract video data', expected=True)

        video_id = str(video.get('id') or video_id)
        media_path = video.get('videoUrl')
        if not media_path:
            raise ExtractorError('Unable to extract video URL', expected=True)
        media_url = urljoin(self._MEDIA_BASE, media_path)
        ext = determine_ext(media_url)
        if ext == 'm3u8':
            formats = self._extract_m3u8_formats(media_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats = [{'url': media_url, 'ext': ext or 'mp4'}]

        broadcast_date = video.get('broadcastDate')
        if broadcast_date in ('1970-01-01', '0000-00-00'):
            broadcast_date = None

        return {
            'id': video_id,
            'formats': formats,
            'title': video.get('name'),
            'description': video.get('description'),
            'thumbnail': urljoin(self._IMAGE_BASE, video['imageUrl']) if video.get('imageUrl') else None,
            'duration': int_or_none(video.get('playLength')),
            'series': video.get('formatName'),
            'timestamp': unified_timestamp(broadcast_date),
        }
