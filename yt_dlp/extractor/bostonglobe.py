import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class BostonGlobeIE(InfoExtractor):
    _VALID_URL = r'(?i)https?://(?:www\.)?bostonglobe\.com/.*/(?P<id>[^/]+)/\w+(?:\.html)?'
    _TESTS = [
        {
            'url': 'https://www.bostonglobe.com/video/2026/08/26/sports/baseball/redsox/roman-anthony-hr-during-rehab-assignment-with-worcester/',
            'md5': '4fb8621327d8d224f96f95cb2847fc47',
            'info_dict': {
                'id': '21b66551-da43-46cd-8026-e76443981579',
                'ext': 'mp4',
                'title': 'Roman Anthony HR during rehab assignment with Worcester',
                'description': "Roman Anthony hit a two-run home run during the seventh inning in Worcester's 8-5 win over Scranton/Wilkes-Barre on Aug. 25 at Polar Park.",
                'thumbnail': r're:https?://.+\.jpg',
                'duration': 40,
                'timestamp': 1787777671,
                'upload_date': '20260826',
                'uploader': 'Craig Larson / Globe Staff',
            },
            'params': {'format': 'best[protocol=https]'},
        },
        {
            'url': 'http://www.bostonglobe.com/pf/dist/components/combinations/default.css?d=690&amp;mxId=00000000',
            'skip': 'video gone',
            'md5': '0a62181079c85c2d2b618c9a738aedaf',
            'info_dict': {
                'title': 'A tree finally succumbs to disease, leaving a hole in a neighborhood',
                'id': 'default',
                'ext': 'mp4',
                'description': 'It arrived as a sapling when the Back Bay was in its infancy, a spindly American elm tamped down into a square of dirt cut into the brick sidewalk of 1880s Marlborough Street, no higher than the first bay window of the new brownstone behind it.',
                'timestamp': 1486877593,
                'upload_date': '20170212',
                'uploader_id': '245991542',
            },
        },
        {
            # Embedded youtube video; we hand it off to the Generic extractor.
            'url': 'https://www.bostonglobe.com/lifestyle/names/2017/02/17/does-ben-affleck-play-matt-damon-favorite-version-batman/ruqkc9VxKBYmh5txn1XhSI/story.html',
            'skip': 'video gone',
            'md5': '582b40327089d5c0c949b3c54b13c24b',
            'info_dict': {
                'title': "Who Is Matt Damon's Favorite Batman?",
                'id': 'ZW1QCnlA6Qc',
                'ext': 'mp4',
                'upload_date': '20170217',
                'description': 'md5:3b3dccb9375867e0b4d527ed87d307cb',
                'uploader': 'The Late Late Show with James Corden',
                'uploader_id': 'TheLateLateShow',
            },
            'expected_warnings': ['404'],
        },
    ]

    def _extract_video(self, video, display_id):
        video_id = video.get('_id') or display_id
        formats = []
        urls = set()
        is_live = video.get('status') == 'live'
        for stream in traverse_obj(video, ('streams', ..., {dict})):
            stream_url = url_or_none(stream.get('url'))
            if not stream_url or stream_url in urls:
                continue
            urls.add(stream_url)
            stream_type = stream.get('stream_type')
            if stream_type in ('ts', 'hls'):
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, 'mp4', live=is_live, m3u8_id='hls', fatal=False))
            elif stream_type != 'smil':
                formats.append({
                    'format_id': join_nonempty(stream_type, int_or_none(stream.get('bitrate'))),
                    'url': stream_url,
                    'tbr': int_or_none(stream.get('bitrate')),
                    'width': int_or_none(stream.get('width')),
                    'height': int_or_none(stream.get('height')),
                    'filesize': int_or_none(stream.get('filesize')),
                })
        return {
            'id': video_id,
            'formats': formats,
            'is_live': is_live,
            **traverse_obj(video, {
                'title': ('headlines', 'basic', {str}),
                'description': ((('subheadlines', 'basic'), ('description', 'basic')), {str}, any),
                'thumbnail': ('promo_image', 'url', {url_or_none}),
                'duration': ('duration', {lambda v: int_or_none(v, 1000)}),
                'timestamp': ('created_date', {parse_iso8601}),
                'uploader': ('credits', 'affiliation', 0, 'name', {str}),
            }),
        }

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        video = self._search_json(
            r'Fusion\.globalContent\s*=', webpage, 'fusion content', page_id, default=None)
        if traverse_obj(video, 'type') == 'video' and video.get('streams'):
            return self._extract_video(video, page_id)

        page_title = self._og_search_title(webpage, default=None)

        # <video data-brightcove-video-id="5320421710001" data-account="245991542" data-player="SJWAiyYWg" data-embed="default" class="video-js" controls itemscope itemtype="http://schema.org/VideoObject">
        entries = []
        for video_tag in re.findall(r'(?i)(<video[^>]+>)', webpage):
            attrs = extract_attributes(video_tag)

            video_id = attrs.get('data-brightcove-video-id')
            account_id = attrs.get('data-account')
            player_id = attrs.get('data-player')
            embed = attrs.get('data-embed')

            if video_id and account_id and player_id and embed:
                entries.append(
                    f'http://players.brightcove.net/{account_id}/{player_id}_{embed}/index.html?videoId={video_id}')

        if len(entries) == 0:
            return self.url_result(url, 'Generic')
        elif len(entries) == 1:
            return self.url_result(entries[0], 'BrightcoveNew')
        else:
            return self.playlist_from_matches(entries, page_id, page_title, ie='BrightcoveNew')
