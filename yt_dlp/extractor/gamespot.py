import urllib.parse

from .common import InfoExtractor
from .jwplatform import JWPlatformIE
from ..utils import (
    extract_attributes,
    get_element_html_by_class,
)


class GameSpotIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?gamespot\.com/(?:video|article|review)s/'
        r'(?:embed/(?P<id>\d+)|(?P<slug>[^/]+)(?:/\d+-(?P<gs_id>\d+))?)/?')
    _TESTS = [{
        'url': 'http://www.gamespot.com/videos/the-witcher-3-wild-hunt-xbox-one-now-playing/2300-6424837/',
        'md5': '6ee0a7919c756bd16a633e3abd3ee616',
        'info_dict': {
            'id': 'KyuYpJqf',
            'ext': 'mp4',
            'title': 'Now Playing - The Witcher 3: Wild Hunt',
            'description': 'Join us as we take a look at the early hours of The Witcher 3: Wild Hunt and more.',
            'display_id': '6424837',
            'duration': 7399.0,
            'thumbnail': 'https://cdn.jwplayer.com/v2/media/KyuYpJqf/poster.jpg?width=720',
            'timestamp': 1431607980,
            'upload_date': '20150514',
        },
        'params': {
            # Prefer progressive MP4 so the live test is not HLS-only
            'format': 'best[protocol=https][ext=mp4]/best',
        },
    }, {
        'url': 'http://www.gamespot.com/videos/arma-3-community-guide-sitrep-i/2300-6410818/',
        'only_matching': True,
    }, {
        'url': 'https://www.gamespot.com/videos/embed/6439218/',
        'only_matching': True,
    }, {
        'url': 'https://www.gamespot.com/articles/the-last-of-us-2-receives-new-ps4-trailer/1100-6454469/',
        'only_matching': True,
    }, {
        'url': 'https://www.gamespot.com/reviews/gears-of-war-review/1900-6161188/',
        'only_matching': True,
    }, {
        'url': 'https://www.gamespot.com/videos/fable-a-new-look-at-combat/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        page_id = mobj.group('id') or mobj.group('gs_id') or mobj.group('slug')
        webpage = self._download_webpage(url, page_id, impersonate=True)

        embed = extract_attributes(
            get_element_html_by_class('video-embed-block', webpage) or '')
        jw_id = embed.get('data-jw-id') or self._search_regex(
            r'"jwMediaId"\s*:\s*"([a-zA-Z0-9]{8})"', webpage,
            'jw media id', default=None)
        if jw_id:
            return self.url_result(
                f'jwplatform:{jw_id}', ie=JWPlatformIE, video_id=jw_id,
                url_transparent=True, display_id=page_id,
                description=self._html_search_meta('description', webpage))

        youtube_id = embed.get('data-youtube-id')
        if youtube_id:
            return self.url_result(
                youtube_id, ie='Youtube', video_id=youtube_id,
                url_transparent=True, display_id=page_id)

        data_video = self._parse_json(self._html_search_regex(
            r'data-video=(["\'])({.*?})\1', webpage,
            'video data', group=2), page_id)
        title = urllib.parse.unquote(data_video['title'])
        streams = data_video['videoStreams']
        formats = []

        m3u8_url = streams.get('adaptive_stream')
        if m3u8_url:
            m3u8_formats = self._extract_m3u8_formats(
                m3u8_url, page_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False)
            for f in m3u8_formats:
                formats.append(f)
                http_f = f.copy()
                http_f.pop('manifest_url', None)
                http_f.update({
                    'format_id': f['format_id'].replace('hls-', 'http-'),
                    'protocol': 'http',
                    'url': f['url'].replace('.m3u8', '.mp4'),
                })
                formats.append(http_f)

        mpd_url = streams.get('adaptive_dash')
        if mpd_url:
            formats.extend(self._extract_mpd_formats(
                mpd_url, page_id, mpd_id='dash', fatal=False))

        return {
            'id': data_video.get('guid') or page_id,
            'display_id': page_id,
            'title': title,
            'formats': formats,
            'description': self._html_search_meta('description', webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
