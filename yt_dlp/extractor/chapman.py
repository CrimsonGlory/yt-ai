from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    parse_iso8601,
    parse_qs,
    unescapeHTML,
    update_url,
    url_or_none,
    urljoin,
)
from ..utils.traversal import require, traverse_obj


class ChapmanIE(InfoExtractor):
    IE_NAME = 'chapman'
    IE_DESC = 'Chapman University blogs and YuJa video'
    _VALID_URL = r'''(?x)
        https?://(?:
            blogs\.chapman\.edu/(?P<blog_id>[^/?#]+(?:/[^/?#]+)*/\d{4}/\d{2}/\d{2}/[^/?#]+)/?
            |video\.chapman\.edu/V/Video(?:[?#]|$)
        )
    '''
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://video\.chapman\.edu/V/Video\?[^"\']+)\1']
    _API_BASE = 'https://video.chapman.edu'
    _TESTS = [
        {
            'url': 'https://blogs.chapman.edu/huell-howser-archives/1991/07/07/preserving-the-past-californias-gold-207/',
            'md5': '6738ced32614a4338196753b3845ee5f',
            'info_dict': {
                'id': '9842745',
                'ext': 'mp4',
                'title': "Preserving the Past – California's Gold (207)",
                'description': 'md5:c2b3eda5352819b5707c290a53fe031a',
                'display_id': 'huell-howser-archives/1991/07/07/preserving-the-past-californias-gold-207',
                'duration': 1656.357,
                'thumbnail': 'https://video.chapman.edu/P/DataPage/BroadcastsThumb/Dg2kOyJ4ONY',
                'timestamp': 678852384,
                'upload_date': '19910707',
                'tags': 'count:25',
            },
        },
        {
            'url': 'https://video.chapman.edu/V/Video?v=9842745&node=43207828&a=103486387&preload=false',
            'only_matching': True,
        },
        {
            'url': 'https://blogs.chapman.edu/huell-howser-archives/2012/07/05/cabrillos-ship-californias-gold-15005/',
            'only_matching': True,
        },
    ]

    def _extract_player_url(self, url, display_id):
        webpage = self._download_webpage(url, display_id, impersonate=True)
        player_url = unescapeHTML(
            self._search_regex(
                r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://video\.chapman\.edu/V/Video\?[^"\']+)\1',
                webpage,
                'Chapman video embed',
                group='url',
            ),
        )
        title = self._html_search_regex(
            r'<h1[^>]+class="entry-title"[^>]*>([^<]+)', webpage, 'title', default=None,
        ) or self._og_search_title(webpage, default=None)
        description = self._html_search_regex(
            r'itemprop="text"\s*>\s*<p[^>]*>(.+?)</p>', webpage, 'description', default=None,
        )
        timestamp = parse_iso8601(self._html_search_meta('article:published_time', webpage, default=None))
        return player_url, {
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'display_id': display_id,
        }

    def _extract_source_formats(self, source, video_id):
        formats, subtitles = [], {}
        for stream in traverse_obj(source, ('streams', ..., {dict})):
            media = traverse_obj(stream, ('typeAndVideoSourceMap', {dict})) or {}
            hls_url = traverse_obj(media, ('HLS', 'cloudFrontURL', {url_or_none})) or traverse_obj(
                media, ('HLS', 'fileURL', {url_or_none}),
            )
            if hls_url:
                hls_url = update_url(hls_url, netloc='video.chapman.edu')
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                )
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            mp4_url = traverse_obj(media, ('MP4', 'cloudFrontURL', {url_or_none})) or traverse_obj(
                media, ('MP4', 'fileURL', {url_or_none}),
            )
            if mp4_url:
                formats.append(
                    {
                        'url': mp4_url,
                        'ext': 'mp4',
                        'format_id': 'http-mp4',
                    },
                )
        return formats, subtitles

    def _real_extract(self, url):
        blog_id = self._match_valid_url(url).group('blog_id')
        webpage_info = {}
        if blog_id:
            url, webpage_info = self._extract_player_url(url, blog_id)

        qs = parse_qs(url)
        video_id = traverse_obj(qs, ('v', 0, {str}))
        if not video_id:
            raise ExtractorError('Unable to extract Chapman video id', expected=True)

        query = {'video': video_id}
        node_id = traverse_obj(qs, ('node', 0, {str}))
        auth_code = traverse_obj(qs, ('a', 0, {str}))
        if node_id:
            query['node'] = node_id
        if auth_code:
            query['a'] = auth_code
        if 'node' not in query and 'a' not in query:
            raise ExtractorError('This Chapman video URL is missing a node or auth parameter', expected=True)

        data = self._download_json(f'{self._API_BASE}/P/Data/VideoJSON', video_id, query=query)
        if not data.get('success'):
            reason = data.get('reason') or 'Unable to retrieve video metadata'
            raise ExtractorError(reason, expected=True)

        video = traverse_obj(data, ('video', {dict}, {require('video metadata')}))
        if video.get('isLocked'):
            self.raise_login_required('This video is locked')

        video_link = traverse_obj(video, ('videoLink', {str}, {require('video link')}))
        source = self._download_json(
            f'{self._API_BASE}/P/Data/VideoSource',
            video_id,
            'Downloading video source JSON',
            query={
                'video': video_link,
                'videoPID': video_id,
                'videoListNodePID': node_id or '',
                'mp4Only': 'false',
                'trackingClassPID': '',
                'contentToken': data.get('contentToken') or '',
            },
        )
        if not source.get('success'):
            raise ExtractorError('Unable to retrieve video source', expected=True)

        formats, subtitles = self._extract_source_formats(source, video_id)
        if not formats:
            raise ExtractorError('No playable formats found', expected=True)

        return {
            'id': str(video.get('videoPID') or video_id),
            'formats': formats,
            'subtitles': subtitles,
            'title': webpage_info.get('title') or video.get('videoTitle'),
            'description': webpage_info.get('description') or video.get('description') or None,
            'duration': float_or_none(video.get('duration')),
            'thumbnail': urljoin(self._API_BASE, video.get('thumbImage')),
            'timestamp': webpage_info.get('timestamp') or parse_iso8601(video.get('postedUTC')),
            'tags': traverse_obj(video, ('broadcastKeywords', ..., {str})) or None,
            'display_id': webpage_info.get('display_id'),
        }
