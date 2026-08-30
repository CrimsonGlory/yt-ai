import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    clean_podcast_url,
    format_field,
    int_or_none,
    parse_iso8601,
    parse_qs,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class CastboxIE(InfoExtractor):
    IE_NAME = 'castbox'
    IE_DESC = 'Castbox'
    _VALID_URL = r'''(?x)
        https?://(?:www\.|d\.)?castbox\.fm/
        (?:
            (?:
                episode/[^/?#]*-id
                |app/castbox/player/id\d+/id
                |ep/
            )(?P<id>\d+)
            |x/(?P<short_id>[\w-]+)
            |dynamic-link/redirect
        )
    '''
    _TESTS = [{
        'url': 'https://castbox.fm/episode/Why-Your-Brain-Is-Strongest-After-You-Nut-id5598686-id950985541',
        'md5': 'baecee54b22ad5735511af9282f0b571',
        'info_dict': {
            'id': '950985541',
            'ext': 'mp3',
            'title': 'Why Your Brain Is Strongest After You Nut',
            'description': 'md5:0df233d1d4ed1c817bea88beeedb96f8',
            'thumbnail': r're:https://s3\.castbox\.fm/.+\.jpg',
            'duration': 780,
            'timestamp': 1780153200,
            'upload_date': '20260530',
            'filesize': 9208487,
            'series': 'HealthyGamerGG',
            'series_id': '5598686',
            'channel': 'HealthyGamerGG',
            'channel_id': '5598686',
            'channel_url': 'https://castbox.fm/channel/id5598686',
            'creators': ['Dr.K'],
            'episode': 'Why Your Brain Is Strongest After You Nut',
            'categories': ['Mental Health', 'Health & Fitness', 'Society & Culture'],
            'language': 'en-us',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://castbox.fm/episode/Why-Your-Brain-Is-Strongest-After-You-Nut-id5598686-id950985541?country=us',
        'only_matching': True,
    }, {
        'url': 'https://castbox.fm/app/castbox/player/id5598686/id950985541',
        'only_matching': True,
    }, {
        'url': 'https://castbox.fm/ep/951737553',
        'only_matching': True,
    }, {
        'url': 'https://castbox.fm/x/3NaXQ',
        'only_matching': True,
    }, {
        'url': 'https://d.castbox.fm/dynamic-link/redirect?link=https%3A%2F%2Fcastbox.fm%2Fep%2F951737553&v=v1&appid=castbox',
        'only_matching': True,
    }]

    def _parse_episode_id(self, url):
        if not url:
            return None
        for candidate in (url, *traverse_obj(parse_qs(url), ('link', ...), default=())):
            ids = re.findall(r'(?:/ep/|[-/]id)(\d+)', candidate)
            if ids:
                return ids[-1]

    def _real_extract(self, url):
        episode_id = self._parse_episode_id(url)
        if not episode_id:
            display_id = self._match_valid_url(url).group('short_id') or 'episode'
            webpage, urlh = self._download_webpage_handle(
                url, display_id, note='Resolving episode URL')
            episode_id = self._parse_episode_id(urlh.url) or self._parse_episode_id(
                self._og_search_property('url', webpage, default=''))
        if not episode_id:
            raise ExtractorError('Unable to extract episode ID', expected=True)

        data = traverse_obj(self._download_json(
            'https://everest.castbox.fm/data/episode/v4', episode_id,
            query={'eid': episode_id}), ('data', {dict}, {require('episode data')}))

        media_url = traverse_obj(data, (
            ('url', ('urls', ...)), {url_or_none}, {clean_podcast_url}, any))
        if not media_url:
            if data.get('private'):
                self.raise_login_required('This episode is private')
            raise ExtractorError('Unable to extract episode media URL', expected=True)

        return {
            'id': str_or_none(data.get('eid')) or episode_id,
            'url': media_url,
            'vcodec': 'none' if not data.get('video') else None,
            **traverse_obj(data, {
                'title': ('title', {str}),
                'description': ('description', {clean_html}),
                'thumbnail': (('big_cover_url', 'cover_url', 'small_cover_url'), {url_or_none}, any),
                'duration': ('duration', {int_or_none(scale=1000)}),
                'timestamp': ('release_date', {parse_iso8601}),
                'filesize': ('size', {int_or_none}),
                'view_count': ('play_count', {int_or_none}),
                'like_count': ('like_count', {int_or_none}),
                'comment_count': ('comment_count', {int_or_none}),
                'creators': ('author', {str}, filter, all, filter),
                'episode': ('title', {str}),
                'series': ('channel', 'title', {str}),
                'series_id': ('cid', {int_or_none}, {str_or_none}),
                'channel': ('channel', 'title', {str}),
                'channel_id': ('cid', {int_or_none}, {str_or_none}),
                'channel_url': ('cid', {int_or_none}, {str_or_none}, {
                    format_field(template='https://castbox.fm/channel/id%s')}),
                'categories': ('channel', 'keywords', ..., {str}, all, filter),
                'language': ('channel', 'language', {str}),
            }),
        }
