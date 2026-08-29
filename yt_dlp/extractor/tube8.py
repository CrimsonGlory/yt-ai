import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    merge_dicts,
    traverse_obj,
    url_or_none,
)


class Tube8IE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?tube8\.com/(?:(?:[^/]+/)+(?P<display_id>[^/]+)/|(?:porn-video|embed)/)(?P<id>\d+)'
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>(?:https?:)?//(?:www\.)?tube8\.com/embed/(?:(?:[^/]+/)+\d+|\d+))']
    _TESTS = [{
        'url': 'https://www.tube8.com/porn-video/198851031/',
        'md5': '19f92f3b8efe801aa06784995c380d7c',
        'info_dict': {
            'id': '198851031',
            'ext': 'mp4',
            'title': 'Hard Anal Fuck and Creampie',
            'thumbnail': r're:https://.+\.jpg',
            'duration': 206,
            'uploader': 'MilkysWays',
            'timestamp': 1761348978,
            'upload_date': '20251024',
            'view_count': int,
            'age_limit': 18,
        },
        'params': {
            'format': 'best[protocol=https]',
        },
    }, {
        'url': 'http://www.tube8.com/teen/kasia-music-video/229795/',
        'md5': '65e20c48e6abff62ed0c3965fff13a39',
        'info_dict': {
            'id': '229795',
            'display_id': 'kasia-music-video',
            'ext': 'mp4',
            'description': 'hot teen Kasia grinding',
            'uploader': 'unknown',
            'title': 'Kasia music video',
            'age_limit': 18,
            'duration': 230,
            'categories': ['Teen'],
            'tags': ['dancing'],
        },
        'skip': 'video gone',
    }, {
        'url': 'http://www.tube8.com/shemale/teen/blonde-cd-gets-kidnapped-by-two-blacks-and-punished-for-being-a-slutty-girl/19569151/',
        'only_matching': True,
    }, {
        'url': 'https://www.tube8.com/embed/198851031/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        self._set_cookie('.tube8.com', 'age_verified', '1')
        webpage = self._download_webpage(
            f'https://www.tube8.com/porn-video/{video_id}/', video_id)

        watchable = self._search_regex(
            r'''(<div\s[^>]*\bid\s*=\s*('|")?watch-container(?(2)\2|(?!-)\b)[^>]*>)''',
            webpage, 'watchability', default=None)
        if not watchable:
            msg = re.split(r'\s{2}', clean_html(get_element_by_id('mainContent', webpage)) or '')[0]
            raise ExtractorError(
                f'{self.IE_NAME} says: {msg}' if msg else 'Video unavailable', expected=True)

        player_vars = self._search_json(r'\bplayervars\s*:', webpage, 'player vars', video_id)
        definitions = player_vars['mediaDefinitions']

        def get_format_data(data, stream_type):
            info_url = traverse_obj(data, (lambda _, v: v['format'] == stream_type, 'videoUrl', {url_or_none}, any))
            if not info_url:
                return []
            return traverse_obj(
                self._download_json(info_url, video_id, f'Downloading {stream_type} info JSON', fatal=False),
                lambda _, v: v['format'] == stream_type and url_or_none(v['videoUrl']))

        formats = []
        # Try to extract only the actual master m3u8 first, avoiding the duplicate single resolution "master" m3u8s
        for hls_url in traverse_obj(get_format_data(definitions, 'hls'), (
                lambda _, v: not isinstance(v['defaultQuality'], bool), 'videoUrl'), (..., 'videoUrl')):
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', fatal=False, m3u8_id='hls'))

        for definition in get_format_data(definitions, 'mp4'):
            f = traverse_obj(definition, {
                'url': 'videoUrl',
                'filesize': ('videoSize', {int_or_none}),
            })
            height = int_or_none(definition.get('quality'))
            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', definition['videoUrl'])
            if mobj:
                if not height:
                    height = int(mobj.group('height'))
                bitrate = int(mobj.group('bitrate'))
                f.update({
                    'format_id': f'{height}p-{bitrate}k',
                    'tbr': bitrate,
                })
            f['height'] = height
            formats.append(f)

        title = self._html_search_regex(
            r'(?s)<h1[^>]+class=["\']videoTitle[^>]+>(.+?)</h1>',
            webpage, 'title', default=None) or player_vars.get('video_title') or self._og_search_title(
            webpage, default=None)

        data = self._search_json_ld(webpage, video_id, expected_type='VideoObject', fatal=False)
        data.pop('url', None)

        result = merge_dicts(data, {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': player_vars.get('image_url'),
            'duration': int_or_none(player_vars.get('video_duration')),
            'uploader': clean_html(get_element_by_class('submitByLink', webpage)),
            'age_limit': self._rta_search(webpage) or 18,
            'formats': formats,
        })

        description = result.get('description')
        if description and description.startswith(f'Watch the hot porn video {result.get("title")}'):
            del result['description']

        return result
