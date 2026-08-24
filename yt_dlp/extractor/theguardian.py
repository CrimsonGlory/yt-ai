import itertools

from .common import InfoExtractor
from ..utils import (
    clean_html,
    extract_attributes,
    get_element_by_class,
    get_element_html_by_class,
    get_elements_html_by_class,
    parse_qs,
    traverse_obj,
    unified_strdate,
    urljoin,
)


class TheGuardianPodcastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?theguardian\.com/\w+/audio/\d{4}/\w{3}/\d{1,2}/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.theguardian.com/news/audio/2023/nov/03/we-are-just-getting-started-the-plastic-eating-bacteria-that-could-change-the-world-podcast',
        'md5': 'd1771744681789b4cd7da2a08e487702',
        'info_dict': {
            'id': 'we-are-just-getting-started-the-plastic-eating-bacteria-that-could-change-the-world-podcast',
            'ext': 'mp3',
            'title': '‘We are just getting started’: the plastic-eating bacteria that could change the world – podcast',
            'description': 'md5:cfd3df2791d394d2ab62cd571d5207ee',
            'creator': 'Stephen Buranyi',
            'creators': ['Stephen Buranyi'],
            'thumbnail': r're:https?://.*',
            'release_date': '20231103',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.theguardian.com/news/audio/2023/oct/30/the-trials-of-robert-habeck-is-the-worlds-most-powerful-green-politician-doomed-to-fail-podcast',
        'md5': 'd1771744681789b4cd7da2a08e487702',
        'info_dict': {
            'id': 'the-trials-of-robert-habeck-is-the-worlds-most-powerful-green-politician-doomed-to-fail-podcast',
            'ext': 'mp3',
            'title': 'The trials of Robert Habeck: is the world’s most powerful green politician doomed to fail? – podcast',
            'description': 'md5:1b5cf6582d1771c6b7077784b5456994',
            'creator': 'Philip Oltermann',
            'creators': ['Philip Oltermann'],
            'thumbnail': r're:https?://.*',
            'release_date': '20231030',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.theguardian.com/football/audio/2023/nov/06/arsenal-feel-hard-done-by-and-luton-hold-liverpool-football-weekly',
        'md5': 'a2fcff6f8e060a95b1483295273dc35e',
        'info_dict': {
            'id': 'arsenal-feel-hard-done-by-and-luton-hold-liverpool-football-weekly',
            'ext': 'mp3',
            'title': 'Arsenal feel hard done by and Luton hold Liverpool – Football Weekly',
            'description': 'md5:286a9fbddaeb7c83cc65d1c4a5330b2a',
            'creator': 'Max Rushden',
            'creators': ['Max Rushden'],
            'thumbnail': r're:https?://.*',
            'release_date': '20231106',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.theguardian.com/politics/audio/2023/nov/02/the-covid-inquiry-politics-weekly-uk-podcast',
        'md5': '06a0f7e9701a80c8064a5d35690481ec',
        'info_dict': {
            'id': 'the-covid-inquiry-politics-weekly-uk-podcast',
            'ext': 'mp3',
            'title': 'The Covid inquiry | Politics Weekly UK - podcast',
            'description': 'md5:207c98859c14903582b17d25b014046e',
            'creator': 'Gaby Hinsliff',
            'creators': ['Gaby Hinsliff'],
            'thumbnail': r're:https?://.*',
            'release_date': '20231102',
        },
        'params': {'skip_download': True},
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_ld = self._search_json_ld(webpage, video_id, default={}) or {}
        audio_url = extract_attributes(get_element_html_by_class(
            'podcast__player', webpage) or '').get('data-source') or self._search_regex(
            r'(https?://audio\.guim\.co\.uk/[^"\'<> ]+\.mp3)', webpage, 'audio url', default=None)
        creator = (
            self._html_search_meta('author', webpage, default=None)
            or traverse_obj(json_ld, ('author', ..., 'name'), get_all=False)
            or traverse_obj(json_ld, ('author', 'name'))
            or self._search_regex(
                r'"@type"\s*:\s*"Person"\s*,\s*"name"\s*:\s*"([^"]+)"',
                webpage, 'author', default=None))
        return {
            'id': video_id,
            'title': self._og_search_title(webpage) or get_element_by_class('content__headline', webpage),
            'description': self._og_search_description(webpage),
            'creator': creator,
            'thumbnail': self._og_search_thumbnail(webpage),
            'release_date': unified_strdate(
                self._html_search_meta('article:published_time', webpage)
                or traverse_obj(json_ld, 'uploadDate', 'datePublished')),
            'url': audio_url,
        }


class TheGuardianPodcastPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?theguardian\.com/\w+/series/(?P<id>[\w-]+)(?:\?page=\d+)?'
    _TESTS = [{
        'url': 'https://www.theguardian.com/football/series/theguardianswomensfootballweekly',
        'skip': 'Series listing markup changed',
        'info_dict': {
            'id': 'theguardianswomensfootballweekly',
            'title': "The Guardian's Women's Football Weekly",
            'description': 'md5:e2cc021311e582d29935a73614a43f51',
        },
        'playlist_mincount': 69,
    }, {
        'url': 'https://www.theguardian.com/news/series/todayinfocus?page=2',
        'skip': 'Series listing markup changed',
        'info_dict': {
            'id': 'todayinfocus',
            'title': 'Today in Focus',
            'description': 'md5:0f097764fc0d359e0b6eb537be0387e2',
        },
        'playlist_mincount': 1261,
    }, {
        'url': 'https://www.theguardian.com/news/series/the-audio-long-read',
        'skip': 'Series listing markup changed',
        'info_dict': {
            'id': 'the-audio-long-read',
            'title': 'The Audio Long Read',
            'description': 'md5:5462994a27527309562b25b6defc4ef3',
        },
        'playlist_mincount': 996,
    }]

    def _entries(self, url, playlist_id):
        for page in itertools.count(1):
            webpage, urlh = self._download_webpage_handle(
                url, playlist_id, f'Downloading page {page}', query={'page': page})
            if 'page' not in parse_qs(urlh.url):
                break

            episodes = get_elements_html_by_class('fc-item--type-media', webpage)
            yield from traverse_obj(episodes, (..., {extract_attributes}, 'data-id'))

    def _real_extract(self, url):
        podcast_id = self._match_id(url)

        webpage = self._download_webpage(url, podcast_id)

        title = clean_html(get_element_by_class(
            'index-page-header__title', webpage) or get_element_by_class('flagship-audio__title', webpage))
        description = self._og_search_description(webpage, default=None) or self._html_search_meta(
            'description', webpage, default=None)

        return self.playlist_from_matches(
            self._entries(url, podcast_id), podcast_id, title, description=description,
            ie=TheGuardianPodcastIE, getter=urljoin('https://www.theguardian.com'))
