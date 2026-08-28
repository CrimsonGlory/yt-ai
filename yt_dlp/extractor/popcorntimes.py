import base64
import codecs

from .common import InfoExtractor
from .dailymotion import DailymotionIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    int_or_none,
    urljoin,
)


class PopcorntimesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?popcorntimes\.tv/[^/]+/(?P<kind>[mt])/(?P<id>[^/]+)/(?P<display_id>[^/?#&]+)'
    _GEO_COUNTRIES = ['DE', 'AT', 'CH']
    # Cloudflare geo-blocks feature-film stream URLs by real client IP
    _GEO_BYPASS = False
    _TESTS = [
        {
            'url': 'https://popcorntimes.tv/de/t/1a80UQvz/evil-dead-burn',
            'md5': 'c3b8147598ff02a9c8c79a8e8ee09fb6',
            'info_dict': {
                'id': 'TnHby2cxJzs',
                'ext': 'mp4',
                'title': 'Evil Dead Burn | Official Trailer',
                'description': 'md5:d697a045b24bf96ac1642cf692704ff3',
                'duration': 145,
                'uploader': 'Warner Bros.',
                'uploader_id': '@WarnerBros',
                'uploader_url': 'https://www.youtube.com/@WarnerBros',
                'channel': 'Warner Bros.',
                'channel_id': 'UCjmJDM5pRKbUlVIzDYYWb6g',
                'channel_url': 'https://www.youtube.com/channel/UCjmJDM5pRKbUlVIzDYYWb6g',
                'channel_follower_count': int,
                'channel_is_verified': True,
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'age_limit': 0,
                'timestamp': 1778172773,
                'upload_date': '20260507',
                'thumbnail': r're:https?://i\.ytimg\.com/.+',
                'categories': ['Entertainment'],
                'tags': [],
                'playable_in_embed': True,
                'availability': 'public',
                'live_status': 'not_live',
                'media_type': 'video',
                'heatmap': 'count:100',
            },
            'add_ie': ['Youtube'],
            'params': {
                'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
            },
            'expected_warnings': [
                'Remote component challenge solver script',
                'No supported JavaScript runtime',
                'n challenge solving failed',
            ],
        },
        {
            'url': 'https://popcorntimes.tv/de/m/A1XCFvz/haensel-und-gretel-opera-fantasy',
            'skip': 'geo-restricted to DE/AT/CH; movie pages omit PCTMLOC outside DACH (X-Forwarded-For is ignored)',
            'md5': '93f210991ad94ba8c3485950a2453257',
            'info_dict': {
                'id': 'A1XCFvz',
                'display_id': 'haensel-und-gretel-opera-fantasy',
                'ext': 'mp4',
                'title': 'Hänsel und Gretel',
                'description': 'md5:1b8146791726342e7b22ce8125cf6945',
                'thumbnail': r're:^https?://.*\.jpg$',
                'creator': 'John Paul',
                'release_date': '19541009',
                'duration': 4260,
                'tbr': 5380,
                'width': 720,
                'height': 540,
            },
        },
        {
            'url': 'https://popcorntimes.tv/de/m/2nIortDo/verbotene-liebe',
            'only_matching': True,
        },
    ]

    def _decode_pctmloc(self, loc):
        if not loc or loc == 'null':
            return None
        loc = loc.strip()
        if loc.startswith(('http://', 'https://')):
            return loc
        if loc.startswith('//'):
            return urljoin('https:', loc)
        try:
            return base64.b64decode(codecs.decode(loc, 'rot_13')).decode()
        except (ValueError, TypeError):
            return None

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')

        webpage = self._download_webpage(url, display_id)

        loc = self._search_regex(
            r'PCTMLOC\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage, 'loc', default=None, group='value',
        )
        video_url = self._decode_pctmloc(loc)
        if video_url and video_url.startswith('//'):
            video_url = urljoin('https:', video_url)

        if not video_url:
            youtube_id = self._search_regex(
                r'data-youtubeid=(["\'])(?P<id>[^"\']+)\1', webpage, 'youtube id', default=None, group='id',
            )
            dm_id = self._search_regex(
                r'data-dm-video=(["\'])(?P<id>[^"\']+)\1', webpage, 'dailymotion id', default=None, group='id',
            )
            if youtube_id:
                video_url = youtube_id
            elif dm_id:
                video_url = f'https://www.dailymotion.com/video/{dm_id}'

        if not video_url:
            geo_match = self._search_regex(r'var\s+PCTGM\s*=\s*(true|false)', webpage, 'geo match', default='false')
            if geo_match == 'false':
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
            raise ExtractorError('This video is no longer available', expected=True)

        if YoutubeIE.suitable(video_url):
            return self.url_result(video_url, ie=YoutubeIE)
        if DailymotionIE.suitable(video_url):
            return self.url_result(video_url, ie=DailymotionIE)

        title = self._search_regex(r'<h1>([^<]+)', webpage, 'title', default=None) or self._html_search_meta(
            'ya:ovs:original_name', webpage, 'title', fatal=True,
        )

        description = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']pt-movie-desc[^>]+>(.+?)</div>', webpage, 'description', fatal=False,
        )

        thumbnail = self._search_regex(
            r'<img[^>]+class=["\']video-preview[^>]+\bsrc=(["\'])(?P<value>(?:(?!\1).)+)\1',
            webpage,
            'thumbnail',
            default=None,
            group='value',
        ) or self._og_search_thumbnail(webpage)

        creator = self._html_search_meta('video:director', webpage, 'creator', default=None)

        release_date = self._html_search_meta('video:release_date', webpage, default=None)
        if release_date:
            release_date = release_date.replace('-', '')

        def int_meta(name):
            return int_or_none(self._html_search_meta(name, webpage, default=None))

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'creator': creator,
            'release_date': release_date,
            'duration': int_meta('video:duration'),
            'tbr': int_meta('ya:ovs:bitrate'),
            'width': int_meta('og:video:width'),
            'height': int_meta('og:video:height'),
            'http_headers': {
                'Referer': url,
            },
        }
