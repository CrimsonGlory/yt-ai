import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class WimbledonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?wimbledon\.com/\w+/video/(?:media/)?(?P<id>[\w-]+)(?:\.html)?/?(?:$|[?#])'
    _GRAPHQL_API = 'https://www.wimbledon.com/graphql'
    # Public web client token from the site's GraphQL env (not user login)
    _GRAPHQL_AUTH = '77d2d900-b41b-4a6a-8700-b98f80bef920'
    _GRAPHQL_QUERY = '''
        query Video($contentId: String!) {
            video(contentId: $contentId) {
                abstract
                contentId
                date
                exclusive
                tags
                title
                sharingUrl
                body {
                    contentId
                    duration
                    hlsManifest
                    progressiveUrl
                    thumbnail
                }
                category { categoryName }
                images { url16x9large urlOriginal }
            }
        }'''
    _TESTS = [
        {
            'url': 'https://www.wimbledon.com/en_GB/video/play_of_the_day_d14_jannik_sinner',
            'md5': '7392b51e3f40c287e5fbc6fd9abd38b4',
            'info_dict': {
                'id': 'play_of_the_day_d14_jannik_sinner',
                'ext': 'mp4',
                'title': 'Play of the Day presented by Barclays: Jannik Sinner',
                'thumbnail': r're:https://content\.wimbledon\.com/is/image/',
                'duration': 50,
                'timestamp': 1783884840,
                'upload_date': '20260712',
                'categories': ['Play of the Day'],
            },
            # HLS --test only fetches the fMP4 init fragment (~1KB), below the default 10KB check
            'file_minsize': None,
        },
        {
            'url': 'https://www.wimbledon.com/en_GB/video/media/6330247525112.html',
            'skip': 'Old /video/media/ URLs redirect to the video index',
            'info_dict': {
                'id': '6330247525112',
                'ext': 'mp4',
                'timestamp': 1687972186,
                'description': '',
                'thumbnail': r're:^https://[\w.-]+\.prod\.boltdns\.net/[^?#]+/image\.jpg',
                'upload_date': '20230628',
                'title': 'Coco Gauff | My Wimbledon Inspiration',
                'tags': ['features', 'trending', 'homepage'],
                'uploader_id': '3506358525001',
                'duration': 163072.0,
            },
        },
        {
            'url': 'https://www.wimbledon.com/en_GB/video/media/6308703111112.html',
            'skip': 'Old /video/media/ URLs redirect to the video index',
            'info_dict': {
                'id': '6308703111112',
                'ext': 'mp4',
                'thumbnail': r're:^https://[\w.-]+\.prod\.boltdns\.net/[^?#]+/image\.jpg',
                'description': 'null',
                'upload_date': '20220629',
                'uploader_id': '3506358525001',
                'title': 'Roblox | WimbleWorld ',
                'duration': 101440.0,
                'tags': ['features', 'kids'],
                'timestamp': 1656500867,
            },
        },
        {
            'url': 'https://www.wimbledon.com/en_US/video/media/6309327106112.html',
            'only_matching': True,
        },
        {
            'url': 'https://www.wimbledon.com/es_Es/video/media/6308377909112.html',
            'only_matching': True,
        },
    ]

    def _call_graphql(self, video_id):
        data = self._download_json(
            self._GRAPHQL_API,
            video_id,
            'Downloading GraphQL JSON',
            data=json.dumps(
                {
                    'operationName': 'Video',
                    'query': self._GRAPHQL_QUERY,
                    'variables': {'contentId': f'/video/{video_id}'},
                },
                separators=(',', ':'),
            ).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': self._GRAPHQL_AUTH,
                'Origin': 'https://www.wimbledon.com',
                'Referer': 'https://www.wimbledon.com/',
            },
        )
        video = traverse_obj(data, ('data', 'video', {dict}))
        if video:
            return video
        message = traverse_obj(data, ('errors', 0, 'message', {str}))
        raise ExtractorError(message or 'Unable to extract video data', expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if video_id.isdecimal():
            return self.url_result(
                f'https://players.brightcove.net/3506358525001/default_default/index.html?videoId={video_id}',
                ie='BrightcoveNew',
                video_id=video_id,
                url_transparent=True,
            )

        video = self._call_graphql(video_id)
        body = traverse_obj(video, ('body', 0, {dict})) or {}
        hls_url = url_or_none(body.get('hlsManifest'))
        progressive_url = url_or_none(body.get('progressiveUrl'))
        if not hls_url and not progressive_url:
            if video.get('exclusive'):
                self.raise_login_required('This video is exclusive to myWimbledon members')
            raise ExtractorError('No video formats found', expected=True)

        formats, subtitles = [], {}
        if hls_url:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(hls_url, video_id, 'mp4', m3u8_id='hls')
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if progressive_url:
            formats.append(
                {
                    'url': progressive_url,
                    'format_id': 'http',
                },
            )

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': int_or_none(body.get('duration')),
            'thumbnail': (
                url_or_none(body.get('thumbnail'))
                or traverse_obj(video, ('images', 0, ('url16x9large', 'urlOriginal'), {url_or_none}), get_all=False)
            ),
            **traverse_obj(
                video,
                {
                    'title': ('title', {str}),
                    'description': ('abstract', {str}),
                    'timestamp': ('date', {parse_iso8601}),
                    'tags': ('tags', ..., {str}),
                    'categories': ('category', 'categoryName', {str}, filter, all),
                },
            ),
        }
