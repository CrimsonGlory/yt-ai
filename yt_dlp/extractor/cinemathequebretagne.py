import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    get_element_by_class,
    int_or_none,
    orderedSet,
    parse_duration,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class CinemathequeBretagneIE(InfoExtractor):
    IE_NAME = 'cinemathequebretagne'
    IE_DESC = 'Cinémathèque de Bretagne'
    _VALID_URL = (
        r'https?://(?:www\.)?cinematheque-bretagne\.bzh/'
        r'voir-les-films(?:-[^/?#]+)?-\d+-(?P<id>[1-9]\d*)-\d+-\d+\.html')
    _TESTS = [{
        'url': 'https://www.cinematheque-bretagne.bzh/voir-les-films-presqu-île-de-crozon-la-426-4362-1-0.html',
        'md5': '76df56957f330a09b33ad22825163469',
        'info_dict': {
            'id': '4362',
            'ext': 'mp4',
            'title': "Presqu'île de Crozon (La)",
            'description': 'md5:1a6cd8dfd9c856201233cf64000aaa38',
            'duration': 902,
            'thumbnail': 'https://diazcdb.oembed.diazinteregio.org/thumb/v/4362.jpg',
            'creators': ['Ange VALLÉE'],
            'genres': ['Documentaire'],
            'release_year': 1952,
        },
    }, {
        'url': 'https://www.cinematheque-bretagne.bzh/voir-les-films-colosses-des-mers-426-51117-0-1.html',
        'only_matching': True,
    }, {
        'url': 'https://www.cinematheque-bretagne.bzh/voir-les-films-40-ans-de-la-cinematheque-de-bretagne-teaser-426-50581-0-1.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        embed_url = url_or_none(unescapeHTML(self._search_regex(
            r'<iframe[^>]+src=(["\'])(?P<url>https?://diazcdb\.oembed\.diazinteregio\.org/embed/\d+(?:(?!\1).)*)\1',
            webpage, 'Diaz embed URL', default=None, group='url')))
        if not embed_url:
            raise ExtractorError('No Diaz video embed found', expected=True)

        video_id = self._search_regex(
            r'/embed/(\d+)', embed_url, 'video id', default=display_id)
        embed_page = self._download_webpage(
            embed_url, video_id, note='Downloading Diaz embed page')

        formats, thumbnail = [], None
        for entry in self._parse_html5_media_entries(embed_url, embed_page, video_id) or []:
            formats.extend(entry.get('formats') or [])
            thumbnail = thumbnail or url_or_none(entry.get('thumbnail'))
        if not formats:
            video_url = urljoin(embed_url, f'/video/{video_id}.mp4')
            if video_url:
                formats = [{'url': video_url, 'ext': 'mp4'}]
        if not formats:
            raise ExtractorError('No video source found', expected=True)

        title = self._html_search_regex(
            r'<h1>([^<]+)<span>', webpage, 'title', default=None)
        if not title:
            og_title = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage)
            if og_title:
                title = og_title.split(' - Voir les films')[0] or og_title

        return {
            'id': video_id,
            'title': title,
            'description': clean_html(get_element_by_class('Resume', webpage)),
            'thumbnail': thumbnail or url_or_none(
                f'https://diazcdb.oembed.diazinteregio.org/thumb/v/{video_id}.jpg'),
            'duration': parse_duration(self._html_search_regex(
                r'class="diaduree"[^>]*>\s*<ul[^>]*>\s*<li>[^<]+</li>\s*<li>([^<]+)',
                webpage, 'duration', default=None, flags=re.DOTALL)),
            'release_year': int_or_none(self._html_search_regex(
                r'<div class="dateContribute">\s*<h2>(\d{4})',
                webpage, 'release year', default=None)),
            'creators': orderedSet(re.findall(r'director=Y[^>]*>([^<]+)', webpage)) or None,
            'genres': orderedSet(re.findall(
                r'class="diagenre_id"[^>]*>\s*<ul[^>]*>\s*<li>[^<]+</li>\s*<li>([^<]+)',
                webpage, flags=re.DOTALL)) or None,
            'formats': formats,
        }
