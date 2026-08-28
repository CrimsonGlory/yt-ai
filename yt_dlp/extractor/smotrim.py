import functools
import re

from .common import InfoExtractor
from ..utils import (
    OnDemandPagedList,
    clean_html,
    determine_ext,
    extract_attributes,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import (
    find_element,
    find_elements,
    traverse_obj,
)


class SmotrimBaseIE(InfoExtractor):
    _BASE_URL = 'https://smotrim.ru'
    _PLAYER_API_URL = 'https://player-api.smotrim.ru/api/v1'
    _UUID_CHANNEL_MAP_URL = 'https://player.smotrim.ru/uuid_channel_map.json'
    _GEO_BYPASS = False
    _GEO_COUNTRIES = ['RU']

    def _extract_from_smotrim_api(self, typ, item_id):
        if typ == 'audio-live':
            typ = 'channel'
        elif typ == 'live' and not re.fullmatch(r'\d+', item_id):
            channel_id = traverse_obj(
                self._download_json(
                    self._UUID_CHANNEL_MAP_URL, item_id, 'Downloading channel map', fatal=False),
                (lambda _, v: isinstance(v, dict) and str(v.get('UUID', '')).lower() == item_id.lower(),
                 'CHANNEL_ID', {str_or_none}, any))
            if channel_id:
                typ, item_id = 'channel', channel_id

        data = self._download_json(
            f'{self._PLAYER_API_URL}/{typ}/{item_id}', item_id,
            headers={'Referer': 'https://player.smotrim.ru/'})
        if traverse_obj(data, 'status') != 'OK':
            if notice := traverse_obj(data, ('notice', {clean_html})):
                self.raise_geo_restricted(notice, countries=self._GEO_COUNTRIES)
            self.raise_no_formats(
                f'Smotrim API returned {traverse_obj(data, "status")}',
                expected=True, video_id=item_id)

        media = traverse_obj(data, ('data', {dict})) or {}
        if traverse_obj(data, ('auth', 'code', {int_or_none})) not in (None, 0):
            self.raise_login_required()

        video_id = traverse_obj(media, (('publicId', 'id'), {str_or_none}, any)) or item_id
        media_type = traverse_obj(media, ('type', {str}))
        m3u8_url = traverse_obj(media, ('streams', 'm3u8', {url_or_none}))
        mp3_url = traverse_obj(media, ('streams', 'mp3', {url_or_none}))
        http_url = traverse_obj(media, ('streams', 'http', {url_or_none}))
        if not (m3u8_url or mp3_url or http_url):
            if traverse_obj(media, 'exclusiveContent'):
                self.raise_login_required()
            if notice := traverse_obj(data, ('notice', {clean_html})):
                self.raise_geo_restricted(notice, countries=self._GEO_COUNTRIES)
            self.raise_no_formats('No media streams available', expected=True, video_id=video_id)

        title = traverse_obj(media, ((
            ('fragment', 'title'), ('episode', 'title'), 'title',
        ), {clean_html}, filter, any))
        if not title and media_type == 'trailer':
            title = 'Трейлер'

        if typ in ('video', 'audio'):
            webpage_url = f'{self._BASE_URL}/{typ}/{video_id}'
        else:
            webpage_url = traverse_obj(media, ('shareLink', {url_or_none})) or urljoin(
                self._BASE_URL, f'/channel/{video_id}')

        common = {
            'id': video_id,
            'title': title,
            'age_limit': traverse_obj(media, ('ageRestriction', {int_or_none})),
            'duration': traverse_obj(media, ('duration', {int_or_none})),
            'is_live': typ in ('channel', 'live'),
            'thumbnail': traverse_obj(media, (
                (('fragment', 'splash'), ('episode', 'splash'), ('brand', 'poster'), 'splash'),
                ('large', 'medium', 'small'), {url_or_none}, any)),
            'timestamp': traverse_obj(media, ('episode', 'airDate', {parse_iso8601})),
            'series': traverse_obj(media, ('brand', 'title', {clean_html})),
            'series_id': traverse_obj(media, ('brand', 'id', {str_or_none})),
            'season': traverse_obj(media, ('episode', 'season', 'title', {clean_html}, filter)),
            'webpage_url': webpage_url,
        }
        if typ == 'channel':
            common['channel_id'] = traverse_obj(media, ('id', {str_or_none}))

        if mp3_url and not m3u8_url:
            return {
                'url': mp3_url,
                'ext': determine_ext(mp3_url, 'mp3'),
                'vcodec': 'none',
                **common,
            }

        formats, subtitles = [], {}
        if m3u8_url:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=not http_url)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if http_url:
            formats.append({
                'format_id': 'http',
                'url': http_url,
            })
        for sub in traverse_obj(media, ('subtitles', ..., {dict})):
            sub_url = traverse_obj(sub, ('vtt', {url_or_none}))
            if not sub_url:
                continue
            self._merge_subtitles({
                traverse_obj(sub, ('code', {str})) or 'ru': [{
                    'url': sub_url,
                    'name': traverse_obj(sub, ('title', {str})),
                    'ext': 'vtt',
                }],
            }, target=subtitles)

        return {
            'formats': formats,
            'subtitles': subtitles,
            **common,
        }


class SmotrimIE(SmotrimBaseIE):
    IE_NAME = 'smotrim'
    _VALID_URL = r'(?:https?:)?//(?:(?:player|www|embed)\.)?smotrim\.ru(?:/iframe)?/video(?:/id)?/(?P<id>\d+)'
    _EMBED_REGEX = [fr'<iframe\b[^>]+\bsrc=["\'](?P<url>{_VALID_URL})']
    _TESTS = [{
        'url': 'https://smotrim.ru/video/1539617',
        'info_dict': {
            'id': '1539617',
            'ext': 'mp4',
            'title': 'Урок №16',
            'age_limit': 12,
            'duration': 2631,
            'series': 'Полиглот. Китайский с нуля за 16 часов!',
            'series_id': '60562',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
            'timestamp': 1466771100,
            'upload_date': '20160624',
            'webpage_url': 'https://smotrim.ru/video/1539617',
        },
    }, {
        'url': 'https://player.smotrim.ru/iframe/video/id/2988590',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '2988590',
            'ext': 'mp4',
            'title': 'Трейлер',
            'duration': 30,
            'webpage_url': 'https://smotrim.ru/video/2988590',
        },
    }, {
        'url': 'https://player.smotrim.ru/iframe/video/id/1539617',
        'only_matching': True,
    }, {
        'url': 'https://embed.smotrim.ru/iframe/video/id/1539617',
        'only_matching': True,
    }]
    _WEBPAGE_TESTS = [{
        'url': 'https://smotrim.ru/article/2813445',
        'skip': 'No video embed on journal article page',
        'info_dict': {
            'id': '2431846',
            'ext': 'mp4',
            'title': 'Съёмки первой программы "Большие и маленькие"',
            'description': 'md5:446c9a5d334b995152a813946353f447',
            'duration': 240,
            'series': 'Новости культуры',
            'series_id': '19725',
            'tags': 'mincount:6',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
            'timestamp': 1656054443,
            'upload_date': '20220624',
            'view_count': int,
            'webpage_url': 'https://smotrim.ru/video/2431846',
        },
    }, {
        'url': 'https://www.vesti.ru/article/4642878',
        'skip': 'Generic embed scan fails on vesti.ru Nuxt page',
        'info_dict': {
            'id': '3007209',
            'ext': 'mp4',
            'title': 'Иностранные мессенджеры используют не только мошенники, но и вербовщики',
            'duration': 265,
            'series': 'Вести. Дежурная часть',
            'series_id': '5204',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
            'timestamp': 1754677800,
            'upload_date': '20250808',
            'webpage_url': 'https://smotrim.ru/video/3007209',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        return self._extract_from_smotrim_api('video', video_id)


class SmotrimAudioIE(SmotrimBaseIE):
    IE_NAME = 'smotrim:audio'
    _VALID_URL = r'https?://(?:(?:player|www|embed)\.)?smotrim\.ru(?:/iframe)?/audio(?:/id)?/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://smotrim.ru/audio/2573986',
        'md5': 'e28d94c20da524e242b2d00caef41a8e',
        'info_dict': {
            'id': '2573986',
            'ext': 'mp3',
            'title': 'Радиоспектакль',
            'age_limit': 12,
            'duration': 3072,
            'series': 'Морис Леблан. Арсен Люпен, джентльмен-грабитель',
            'series_id': '66461',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
            'timestamp': 1624884358,
            'upload_date': '20210628',
            'webpage_url': 'https://smotrim.ru/audio/2573986',
        },
    }, {
        'url': 'https://player.smotrim.ru/iframe/audio/id/2860468',
        'md5': '5a6bc1fa24c7142958be1ad9cfae58a8',
        'info_dict': {
            'id': '2860468',
            'ext': 'mp3',
            'title': 'Колобок и музыкальная игра "Терем-теремок"',
            'age_limit': 12,
            'duration': 1501,
            'series': 'Весёлый колобок',
            'series_id': '68880',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
            'timestamp': 1755925800,
            'upload_date': '20250823',
            'webpage_url': 'https://smotrim.ru/audio/2860468',
        },
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        return self._extract_from_smotrim_api('audio', audio_id)


class SmotrimLiveIE(SmotrimBaseIE):
    IE_NAME = 'smotrim:live'
    _VALID_URL = r'''(?x:
        (?:https?:)?//
            (?:(?:(?:test)?player|www|embed)\.)?
            (?:
                smotrim\.ru|
                vgtrk\.com
            )
            (?:/iframe)?/
            (?P<type>
                channel|
                (?:audio-)?live
            )
            (?:/u?id)?/(?P<id>[\da-f-]+)
    )'''
    _EMBED_REGEX = [fr'<iframe\b[^>]+\bsrc=["\'](?P<url>{_VALID_URL})']
    _TESTS = [{
        'url': 'https://smotrim.ru/channel/76',
        'info_dict': {
            'id': '76',
            'ext': 'mp4',
            'title': str,
            'channel_id': '76',
            'display_id': '76',
            'live_status': 'is_live',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
        },
        'params': {'skip_download': 'Livestream'},
    }, {
        # Radio
        'url': 'https://smotrim.ru/channel/81',
        'info_dict': {
            'id': '81',
            'ext': 'mp4',
            'title': str,
            'channel_id': '81',
            'live_status': 'is_live',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
        },
        'params': {'skip_download': 'Livestream'},
    }, {
        # Sometimes geo-restricted to Russia
        'url': 'https://player.smotrim.ru/iframe/live/uid/381308c7-a066-4c4f-9656-83e2e792a7b4',
        'info_dict': {
            'id': '4',
            'ext': 'mp4',
            'title': str,
            'channel_id': '4',
            'display_id': '381308c7-a066-4c4f-9656-83e2e792a7b4',
            'live_status': 'is_live',
            'thumbnail': r're:https?://cdn(?:-st\d+)?\.smotrim\.ru/.+\.(?:jpg|png)',
            'webpage_url': 'https://smotrim.ru/channel/4',
        },
        'params': {'skip_download': 'Livestream'},
    }, {
        'url': 'https://smotrim.ru/live/19201',
        'only_matching': True,
    }, {
        'url': 'https://player.smotrim.ru/iframe/audio-live/id/81',
        'only_matching': True,
    }, {
        'url': 'https://testplayer.vgtrk.com/iframe/live/id/19201',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        typ, display_id = self._match_valid_url(url).group('type', 'id')

        return {
            'display_id': display_id,
            **self._extract_from_smotrim_api(typ, display_id),
        }


class SmotrimPlaylistIE(SmotrimBaseIE):
    IE_NAME = 'smotrim:playlist'
    _PAGE_SIZE = 15
    _VALID_URL = r'https?://smotrim\.ru/(?P<type>brand|podcast)/(?P<id>\d+)/?(?P<season>[\w-]+)?'
    _TESTS = [{
        # Video
        'url': 'https://smotrim.ru/brand/64356',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '64356',
            'title': 'Большие и маленькие',
        },
        'playlist_mincount': 55,
    }, {
        # Video, season
        'url': 'https://smotrim.ru/brand/65293/3-sezon',
        'info_dict': {
            'id': '65293',
            'title': 'Сериал Спасская (3 сезон)',
            'season': '3 сезон',
        },
        'playlist_count': 16,
    }, {
        # Audio
        'url': 'https://smotrim.ru/brand/68880',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '68880',
            'title': 'Веселый колобок',
        },
        'playlist_mincount': 156,
    }, {
        # Podcast
        'url': 'https://smotrim.ru/podcast/8021',
        'skip': 'video gone',
        'info_dict': {
            'id': '8021',
            'title': 'Сила звука',
        },
        'playlist_mincount': 27,
    }]

    def _fetch_page(self, endpoint, key, playlist_id, page):
        page += 1
        items = self._download_json(
            f'{self._BASE_URL}/api/{endpoint}', playlist_id,
            f'Downloading page {page}', query={
                key: playlist_id,
                'limit': self._PAGE_SIZE,
                'page': page,
            },
        )

        for link in traverse_obj(items, ('contents', -1, 'list', ..., 'link', {str})):
            yield self.url_result(urljoin(self._BASE_URL, link))

    def _real_extract(self, url):
        playlist_type, playlist_id, season = self._match_valid_url(url).group('type', 'id', 'season')
        key = 'rubricId' if playlist_type == 'podcast' else 'brandId'
        webpage = self._download_webpage(url, playlist_id)
        playlist_title = traverse_obj(webpage, (
            {find_element(tag='h1')}, {clean_html}, filter,
        )) or self._html_search_meta(['og:title', 'twitter:title'], webpage, default=None)

        if season:
            return self.playlist_from_matches(traverse_obj(webpage, (
                {find_elements(tag='a', attr='href', value=r'/video/\d+', html=True, regex=True)},
                ..., {extract_attributes}, 'href', {str},
            )), playlist_id, playlist_title, season=traverse_obj(webpage, (
                {find_element(cls='seasons__item seasons__item--selected')}, {clean_html}, filter,
            )) or self._search_regex(
                r'\((\d+\s+сезон)\)', playlist_title or '', 'season', default=None,
            ), ie=SmotrimIE, getter=urljoin(self._BASE_URL))

        if traverse_obj(webpage, (
            {find_element(cls='brand-main-item__videos')}, {clean_html}, filter,
        )):
            endpoint = 'videos'
        else:
            endpoint = 'audios'

        return self.playlist_result(OnDemandPagedList(
            functools.partial(self._fetch_page, endpoint, key, playlist_id), self._PAGE_SIZE), playlist_id, playlist_title)
