import json

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    mimetype2ext,
    qualities,
    traverse_obj,
    url_or_none,
)

_GRAPHQL_API = 'https://api.graphql.imdb.com/'
_GRAPHQL_HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.imdb.com',
    'Referer': 'https://www.imdb.com/',
}


class ImdbIE(InfoExtractor):
    IE_NAME = 'imdb'
    IE_DESC = 'Internet Movie Database trailers'
    _VALID_URL = r'https?://(?:www|m)\.imdb\.com/(?:video|title|list).*?[/-]vi(?P<id>\d+)'
    _GRAPHQL_QUERY = '''query VideoPlayback($id: ID!) {
        video(id: $id) {
            name { value }
            description { value }
            runtime { value }
            thumbnail { url }
            primaryTitle { titleText { text } }
            playbackURLs {
                displayName { value }
                videoMimeType
                url
            }
        }
    }'''

    _TESTS = [{
        'url': 'http://www.imdb.com/video/imdb/vi2524815897',
        'md5': '471594d511a4dee8d71cea96dd72b1ad',
        'info_dict': {
            'id': '2524815897',
            'ext': 'mp4',
            'title': 'No. 2',
            'description': 'md5:87bd0bdc61e351f21f20d2d7441cb4e7',
            'duration': 152,
            'thumbnail': r're:^https?://.+\.jpg',
        },
        'params': {'format': '720p'},
    }, {
        'url': 'https://www.imdb.com/video/vi3516832537',
        'md5': 'b594917779ace7e12be2dfbb2689c3e5',
        'info_dict': {
            'id': '3516832537',
            'ext': 'mp4',
            'title': 'Paul: U.S. Trailer #1',
            'description': 'md5:17fcc4fe11ec29b4399be9d4c5ef126c',
            'duration': 153,
            'thumbnail': r're:^https?://.+\.jpg',
        },
        'params': {'format': '1080p'},
    }, {
        'url': 'http://www.imdb.com/video/_/vi2524815897',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/title/tt1667889/?ref_=ext_shr_eml_vi#lb-vi2524815897',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/title/tt1667889/#lb-vi2524815897',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/videoplayer/vi1562949145',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/title/tt4218696/videoplayer/vi2608641561',
        'only_matching': True,
    }, {
        'url': 'https://www.imdb.com/list/ls009921623/videoplayer/vi260482329',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = traverse_obj(self._download_json(
            _GRAPHQL_API, video_id, 'Downloading GraphQL JSON',
            data=json.dumps({
                'query': self._GRAPHQL_QUERY,
                'operationName': 'VideoPlayback',
                'variables': {'id': f'vi{video_id}'},
            }).encode(),
            headers=_GRAPHQL_HEADERS), ('data', 'video')) or {}
        title = (traverse_obj(video_info, ('name', 'value'), ('primaryTitle', 'titleText', 'text'))
                 or f'vi{video_id}')
        data = video_info.get('playbackURLs') or []
        quality = qualities(('SD', '480p', '720p', '1080p'))
        formats, subtitles = [], {}
        for encoding in data:
            if not encoding or not isinstance(encoding, dict):
                continue
            video_url = url_or_none(encoding.get('url'))
            if not video_url:
                continue
            ext = (mimetype2ext(encoding.get('mimeType'))
                   or {'MP4': 'mp4', 'M3U8': 'm3u8'}.get(encoding.get('videoMimeType'))
                   or determine_ext(video_url))
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    preference=1, m3u8_id='hls', fatal=False)
                subtitles = self._merge_subtitles(subtitles, subs)
                formats.extend(fmts)
                continue
            format_id = traverse_obj(encoding, ('displayName', 'value'), 'definition')
            formats.append({
                'format_id': format_id,
                'url': video_url,
                'ext': ext,
                'quality': quality(format_id),
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': traverse_obj(video_info, ('description', 'value')),
            'thumbnail': traverse_obj(video_info, ('thumbnail', 'url', {url_or_none})),
            'duration': traverse_obj(video_info, ('runtime', 'value', {int_or_none})),
            'subtitles': subtitles,
        }


class ImdbListIE(InfoExtractor):
    IE_NAME = 'imdb:list'
    IE_DESC = 'Internet Movie Database lists'
    _VALID_URL = r'https?://(?:www\.)?imdb\.com/list/ls(?P<id>\d{9})(?!/videoplayer/vi\d+)'
    _GRAPHQL_QUERY = '''query VideoList($id: ID!) {
        list(id: $id) {
            name { originalText }
            description { originalText { plainText } }
            items(first: 250) {
                edges { node { item { ... on Video { id } } } }
            }
        }
    }'''
    _TEST = {
        'url': 'https://www.imdb.com/list/ls009921623/',
        'info_dict': {
            'id': '009921623',
            'title': 'The Bourne Legacy',
            'description': 'A list of trailers, clips, and more from The Bourne Legacy, starring Jeremy Renner and Rachel Weisz.',
        },
        'playlist_count': 8,
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)
        list_info = traverse_obj(self._download_json(
            _GRAPHQL_API, list_id, 'Downloading GraphQL JSON',
            data=json.dumps({
                'query': self._GRAPHQL_QUERY,
                'operationName': 'VideoList',
                'variables': {'id': f'ls{list_id}'},
            }).encode(),
            headers=_GRAPHQL_HEADERS), ('data', 'list')) or {}
        entries = [
            self.url_result(f'https://www.imdb.com/video/{video_id}', 'Imdb', video_id[2:])
            for video_id in traverse_obj(list_info, (
                'items', 'edges', ..., 'node', 'item', 'id', {str}))
            if video_id.startswith('vi')]
        return self.playlist_result(
            entries, list_id,
            traverse_obj(list_info, ('name', 'originalText')),
            traverse_obj(list_info, ('description', 'originalText', 'plainText')))
