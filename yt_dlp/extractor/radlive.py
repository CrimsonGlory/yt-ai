import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    format_field,
    traverse_obj,
    try_get,
    unified_timestamp,
    url_or_none,
)


class RadLiveIE(InfoExtractor):
    IE_NAME = 'radlive'
    _UUID_RE = r'[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12}'
    _VALID_URL = r'https?://(?:www\.)?rad\.live/(?:content|watch)/(?P<content_type>feature|episode)/(?P<id>[^/?#]+)'
    _GRAPHQL_URL = 'https://content.mhq.12core.net/graphql'
    _TESTS = [
        {
            'url': 'https://rad.live/content/feature/dc5acfbc-761b-4bec-9564-df999905116a',
            'skip': 'video gone',
            'md5': '6219d5d31d52de87d21c9cf5b7cb27ff',
            'info_dict': {
                'id': 'dc5acfbc-761b-4bec-9564-df999905116a',
                'ext': 'mp4',
                'title': 'Deathpact - Digital Mirage 2 [Full Set]',
                'language': 'en',
                'thumbnail': 'https://static.12core.net/cb65ae077a079c68380e38f387fbc438.png',
                'description': '',
                'release_timestamp': 1600185600.0,
                'channel': 'Proximity',
                'channel_id': '9ce6dd01-70a4-4d59-afb6-d01f807cd009',
                'channel_url': 'https://rad.live/content/channel/9ce6dd01-70a4-4d59-afb6-d01f807cd009',
            },
        },
        {
            'url': 'https://rad.live/content/episode/bbcf66ec-0d02-4ca0-8dc0-4213eb2429bf',
            'skip': 'video gone',
            'md5': '40b2175f347592125d93e9a344080125',
            'info_dict': {
                'id': 'bbcf66ec-0d02-4ca0-8dc0-4213eb2429bf',
                'ext': 'mp4',
                'title': 'E01: Bad Jokes 1',
                'language': 'en',
                'thumbnail': 'https://lsp.littlstar.com/channels/WHISTLE/BAD_JOKES/SEASON_1/BAD_JOKES_101/poster.jpg',
                'description': 'Bad Jokes - Champions, Adam Pally, Super Troopers, Team Edge and 2Hype',
                'episode': 'E01: Bad Jokes 1',
                'episode_number': 1,
                'episode_id': '336',
            },
        },
        {
            'url': 'https://rad.live/watch/feature/after-us-alligator-official-music-video-7dygQB',
            'md5': '2daceb1a5ec1cd6e96f68a5ca4c53f35',
            'info_dict': {
                'id': 'de1cef55-4ec9-4a56-8f56-2d3e43813186',
                'ext': 'mp4',
                'display_id': 'after-us-alligator-official-music-video-7dygQB',
                'title': 'After Us - "Alligator" (Official Music Video)',
                'description': "\"Alligator'\" by After Us (featuring Elijah Finn and Kellison Porter.)\nFrom the album 'Say It Like You Mean It', out September 4th,.",
                'language': 'en',
                'thumbnail': 'https://12core-tus-ingestion.s3.amazonaws.com/8ff5f96c554832ed551f4bce3cd709c3',
                'duration': 254.933323,
                'release_timestamp': 1785507988,
                'release_date': '20260731',
                'channel': 'Rawkhaus TV',
                'channel_id': '257d3254-4b84-401c-94ca-406acfa864cd',
                'channel_url': 'https://rad.live/content/channel/257d3254-4b84-401c-94ca-406acfa864cd',
            },
        },
        {
            'url': 'https://rad.live/watch/feature/de1cef55-4ec9-4a56-8f56-2d3e43813186',
            'only_matching': True,
        },
        {
            'url': 'https://rad.live/content/feature/de1cef55-4ec9-4a56-8f56-2d3e43813186',
            'only_matching': True,
        },
    ]

    def _call_graphql(self, query, video_id, lrn):
        return self._download_json(
            self._GRAPHQL_URL,
            video_id,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(
                {
                    'query': query,
                    'variables': {'lrn': lrn},
                },
            ).encode(),
        )

    def _download_content(self, content_type, video_id):
        extra = {
            'feature': '    associated_channels { lrn name }\n',
            'episode': '    number\n',
        }.get(content_type, '')
        query = (
            'query ($lrn: ID!) {\n'
            f'  {content_type}(id: $lrn) {{\n'
            '    id\n'
            '    lrn\n'
            '    title\n'
            '    summary\n'
            '    acl\n'
            '    created_at\n'
            '    assets\n'
            '    structured_data\n'
            f'{extra}'
            '  }\n'
            '}'
        )
        graphql = self._call_graphql(query, video_id, f'lrn:12core:media:content:{content_type}:{video_id}')
        return traverse_obj(graphql, ('data', content_type))

    def _real_extract(self, url):
        content_type, display_id = self._match_valid_url(url).group('content_type', 'id')
        video_id = display_id
        if not re.fullmatch(self._UUID_RE, video_id, re.I):
            webpage = self._download_webpage(url, display_id)
            video_id = self._search_regex(
                rf'lrn:12core:media:content:{re.escape(content_type)}:({self._UUID_RE})',
                webpage,
                'video id',
                flags=re.I,
            )

        video_info = self._download_content(content_type, video_id)
        if not video_info:
            raise ExtractorError('Unable to extract video info, make sure the URL is valid')

        video_url = traverse_obj(video_info, ('assets', 'videos', ..., 'url', {url_or_none}), get_all=False)
        if not video_url:
            if video_info.get('acl') not in (None, 'public'):
                self.raise_login_required()
            raise ExtractorError('No video available', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(video_url, video_id)

        data = video_info.get('structured_data') or {}
        channel = traverse_obj(video_info, ('associated_channels', 0), default={}) or {}
        channel_id = (channel.get('lrn') or '').rsplit(':', 1)[-1] or None

        result = {
            'id': video_id,
            'display_id': display_id,
            'title': video_info['title'],
            'formats': formats,
            'subtitles': subtitles,
            'language': traverse_obj(data, ('potentialAction', 'target', 'inLanguage')),
            'thumbnail': traverse_obj(
                video_info,
                ('structured_data', 'image', 'contentUrl', {url_or_none}),
                ('assets', 'images', ..., 'url', {url_or_none}),
                get_all=False,
            ),
            'description': video_info.get('summary') or data.get('description'),
            'duration': float_or_none(traverse_obj(video_info, ('assets', 'videos', 0, 'duration'))),
            'release_timestamp': unified_timestamp(video_info.get('created_at')),
            'channel': channel.get('name'),
            'channel_id': channel_id,
            'channel_url': format_field(channel_id, None, 'https://rad.live/content/channel/%s'),
        }
        if content_type == 'episode':
            result.update(
                {
                    # TODO: Get season number when downloading single episode
                    'episode': video_info.get('title'),
                    'episode_number': video_info.get('number'),
                    'episode_id': video_info.get('id'),
                },
            )

        return result


class RadLiveSeasonIE(RadLiveIE):  # XXX: Do not subclass from concrete IE
    IE_NAME = 'radlive:season'
    _VALID_URL = r'https?://(?:www\.)?rad\.live/content/season/(?P<id>[a-f0-9-]+)'
    _TESTS = [
        {
            'url': 'https://rad.live/content/season/08a290f7-c9ef-4e22-9105-c255995a2e75',
            'skip': 'video gone',
            'md5': '40b2175f347592125d93e9a344080125',
            'info_dict': {
                'id': '08a290f7-c9ef-4e22-9105-c255995a2e75',
                'title': 'Bad Jokes - Season 1',
            },
            'playlist_mincount': 5,
        },
    ]

    @classmethod
    def suitable(cls, url):
        return False if RadLiveIE.suitable(url) else super().suitable(url)

    def _real_extract(self, url):
        season_id = self._match_id(url)
        webpage = self._download_webpage(url, season_id)

        content_info = json.loads(
            self._search_regex(
                r'<script[^>]*type=([\'"])application/json\1[^>]*>(?P<json>{.+?})</script>',
                webpage,
                'video info',
                group='json',
            ),
        )['props']['pageProps']['initialContentData']
        video_info = content_info['season']

        entries = [
            {
                '_type': 'url_transparent',
                'id': episode['structured_data']['url'].split('/')[-1],
                'url': episode['structured_data']['url'],
                'series': try_get(content_info, lambda x: x['series']['title']),
                'season': video_info['title'],
                'season_number': video_info.get('number'),
                'season_id': video_info.get('id'),
                'ie_key': RadLiveIE.ie_key(),
            }
            for episode in video_info['episodes']
        ]

        return self.playlist_result(entries, season_id, video_info.get('title'))


class RadLiveChannelIE(RadLiveIE):  # XXX: Do not subclass from concrete IE
    IE_NAME = 'radlive:channel'
    _VALID_URL = r'https?://(?:www\.)?rad\.live/content/channel/(?P<id>[a-f0-9-]+)'
    _TESTS = [
        {
            'url': 'https://rad.live/content/channel/5c4d8df4-6fa0-413c-81e3-873479b49274',
            'md5': '625156a08b7f2b0b849f234e664457ac',
            'info_dict': {
                'id': '5c4d8df4-6fa0-413c-81e3-873479b49274',
                'title': 'Whistle Sports',
            },
            'playlist_mincount': 6,
        },
    ]

    _QUERY = '''
query WebChannelListing ($lrn: ID!) {
  channel (id:$lrn) {
    name
    features {
      structured_data
    }
  }
}'''

    @classmethod
    def suitable(cls, url):
        return False if RadLiveIE.suitable(url) else super().suitable(url)

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        graphql = self._call_graphql(self._QUERY, channel_id, f'lrn:12core:media:content:channel:{channel_id}')

        data = traverse_obj(graphql, ('data', 'channel'))
        if not data:
            raise ExtractorError('Unable to extract video info, make sure the URL is valid')

        entries = [
            {
                '_type': 'url_transparent',
                'url': feature['structured_data']['url'],
                'ie_key': RadLiveIE.ie_key(),
            }
            for feature in data['features']
        ]

        return self.playlist_result(entries, channel_id, data.get('name'))
