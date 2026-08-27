from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CinemaxIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = (
        r'https?://(?:www\.)?cinemax\.com/'
        r'(?P<show>(?!hbo|order|schedule|terms-of-use|ways-to-get|specials|about)[^/?#]+)'
        r'(?:/video/(?P<slug>[0-9a-z-]+?))?(?:\.embed)?/?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://www.cinemax.com/warrior/video/s1-ep-1-recap-20126903',
        'info_dict': {
            'id': '20126903',
            'ext': 'mp4',
            'title': 'S1 Ep 1: Recap',
            'series': 'WARRIOR',
            'thumbnail': r're:https://.+\.jpg',
        },
    }, {
        'url': 'https://www.cinemax.com/warrior',
        'info_dict': {
            'id': 'warrior',
            'title': 'WARRIOR',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'https://www.cinemax.com/warrior/video/s1-ep-1-recap-20126903.embed',
        'only_matching': True,
    }]

    def _id_from_vid(self, vid):
        return self._search_regex(r'(\d+)$', vid, 'id', default=vid)

    def _parse_videos(self, webpage, display_id):
        next_data = self._search_nextjs_data(webpage, display_id)
        videos, seen = [], set()
        for value in traverse_obj(next_data, ('props', 'pageProps', 'dataByMapping', ..., 'value')):
            parsed = value
            if isinstance(value, str) and value.startswith('[{'):
                parsed = self._parse_json(value, display_id, fatal=False)
            if not isinstance(parsed, list):
                continue
            for item in parsed:
                video = traverse_obj(item, {
                    'vid': ('vid', {str}),
                    'url': ('videoUrl', {url_or_none}),
                    'title': ('title', {str}),
                    'thumbnail': ('poster', {url_or_none}),
                })
                if not video.get('vid') or not video.get('url') or video['vid'] in seen:
                    continue
                seen.add(video['vid'])
                videos.append(video)
        return videos

    def _extract_video(self, video, series):
        video_id = self._id_from_vid(video['vid'])
        formats = self._extract_m3u8_formats(video['url'], video_id, 'mp4', m3u8_id='hls')
        return {
            'id': video_id,
            'title': (video.get('title') or video['vid']).strip(),
            'thumbnail': video.get('thumbnail'),
            'series': series,
            'formats': formats,
        }

    def _real_extract(self, url):
        show, slug = self._match_valid_url(url).group('show', 'slug')
        display_id = slug or show
        webpage = self._download_webpage(f'https://www.cinemax.com/{show}', display_id)
        videos = self._parse_videos(webpage, display_id)
        if not videos:
            raise ExtractorError('No videos found', expected=True)

        series = self._html_search_regex(
            r'<h1[^>]*>([^<]+)', webpage, 'series', default=show).strip()

        video = None
        if slug:
            slug = slug.removesuffix('.embed')
            video = next((v for v in videos if v['vid'] == slug), None)
            if not video:
                raise ExtractorError(f'Unable to find video {slug}', expected=True)
        elif not self._yes_playlist(show, self._id_from_vid(videos[0]['vid'])):
            video = videos[0]

        if video:
            return self._extract_video(video, series)

        return self.playlist_result((
            self.url_result(
                f'https://www.cinemax.com/{show}/video/{v["vid"]}',
                ie=self.ie_key(), video_id=self._id_from_vid(v['vid']),
                video_title=(v.get('title') or v['vid']).strip())
            for v in videos), show, series)
