from .common import InfoExtractor
from ..utils import (
    determine_ext,
    unescapeHTML,
)


class CJSWIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cjsw\.com/program/(?P<program>[^/]+)/episode/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://cjsw.com/program/the-sugar-bowl/episode/20260825',
        'md5': '0c031099a0a83c48b376e8fbb9b510a6',
        'info_dict': {
            'id': '1d9b9229-e7cb-472f-ab43-6ea53a83b24a',
            'ext': 'mp3',
            'title': 'The Sugar Bowl – Episode August 25, 2026',
            'description': "Rest in peace to the queen of country, and America's sweetheart Dolly Parton!",
            'series': 'The Sugar Bowl',
            'episode_id': '20260825',
        },
    }, {
        'url': 'http://cjsw.com/program/freshly-squeezed/episode/20170620',
        'skip': 'audio gone',
        'md5': 'cee14d40f1e9433632c56e3d14977120',
        'info_dict': {
            'id': '91d9f016-a2e7-46c5-8dcb-7cbcd7437c41',
            'ext': 'mp3',
            'title': 'Freshly Squeezed – Episode June 20, 2017',
            'description': 'md5:c967d63366c3898a80d0c7b0ff337202',
            'series': 'Freshly Squeezed',
            'episode_id': '20170620',
        },
    }, {
        # no description
        'url': 'http://cjsw.com/program/road-pops/episode/20170707/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        program, episode_id = mobj.group('program', 'id')
        audio_id = f'{program}/{episode_id}'

        webpage = self._download_webpage(url, episode_id)

        title = unescapeHTML(self._search_regex(
            (r'<h1[^>]+class=["\']episode-header__title["\'][^>]*>(?P<title>[^<]+)',
             r'data-audio-title=(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', group='title'))

        audio_url = self._search_regex(
            r'<button[^>]+data-audio-src=(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'audio url', group='url')

        audio_id = self._search_regex(
            r'/([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})\.mp3',
            audio_url, 'audio id', default=audio_id)

        formats = [{
            'url': audio_url,
            'ext': determine_ext(audio_url, 'mp3'),
            'vcodec': 'none',
        }]

        description = self._html_search_regex(
            r'<p>(?P<description>.+?)</p>', webpage, 'description',
            default=None)
        series = self._search_regex(
            r'data-showname=(["\'])(?P<name>(?:(?!\1).)+)\1', webpage,
            'series', default=program, group='name')

        return {
            'id': audio_id,
            'title': title,
            'description': description,
            'formats': formats,
            'series': series,
            'episode_id': episode_id,
        }
