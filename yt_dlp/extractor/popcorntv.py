from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    extract_attributes,
    int_or_none,
    unified_timestamp,
    update_url,
    url_or_none,
)


class PopcornTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?popcorntv\.it/(?:guarda|streaming(?:/[^/?#]+)*)/(?P<display_id>[^/?#]+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.popcorntv.it/streaming/cinema/mank-2020/11418',
        'md5': 'e980d3bf9f98144ea26cd234b325f469',
        'info_dict': {
            'id': 'RihzDA9rXn0',
            'ext': 'mp4',
            'title': 'MANK | Trailer ufficiale | Netflix Italia',
            'description': 'md5:fc9ef63818f48d2a66f80ce7869e2db1',
            'duration': 164,
            'uploader': 'Netflix Italia',
            'uploader_id': '@netflixitalia',
            'uploader_url': 'https://www.youtube.com/@netflixitalia',
            'channel': 'Netflix Italia',
            'channel_id': 'UCi_T2R1AzOCun4-PI4Or2ng',
            'channel_url': 'https://www.youtube.com/channel/UCi_T2R1AzOCun4-PI4Or2ng',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1603353600,
            'upload_date': '20201022',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Entertainment'],
            'tags': 'count:25',
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
    }, {
        'url': 'https://animemanga.popcorntv.it/guarda/food-wars-battaglie-culinarie-episodio-01/9183',
        'skip': 'video gone',
        'md5': '47d65a48d147caf692ab8562fe630b45',
        'info_dict': {
            'id': '9183',
            'display_id': 'food-wars-battaglie-culinarie-episodio-01',
            'ext': 'mp4',
            'title': 'Food Wars, Battaglie Culinarie | Episodio 01',
            'description': 'md5:b8bea378faae4651d3b34c6e112463d0',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1497610857,
            'upload_date': '20170616',
            'duration': 1440,
            'view_count': int,
        },
    }, {
        'url': 'https://cinema.popcorntv.it/guarda/smash-cut/10433',
        'only_matching': True,
    }, {
        'url': 'https://popcorntv.it/streaming/cinema/joe-limplacabile-1967/11350',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, video_id = self._match_valid_url(url).group('display_id', 'id')

        # Apex popcorntv.it DNS points at origin with an expired cert. www is on
        # Cloudflare (valid cert) but 301s video pages to the apex. Request www
        # with Host: popcorntv.it so CF serves the page without that redirect.
        webpage = self._download_webpage(
            update_url(url, netloc='www.popcorntv.it'), display_id,
            headers={'Host': 'popcorntv.it'})

        if self._search_regex(
                r'<title[^>]*>\s*Video non pi[uù] disponibile',
                webpage, 'gone title', default=None):
            raise ExtractorError('Video is no longer available', expected=True)

        youtube_url = url_or_none(self._search_regex(
            r'(?:<iframe[^>]+src=|"contentUrl"\s*:\s*)["\'](https?://(?:www\.)?youtube\.com/embed/[^"\']+)',
            webpage, 'youtube embed', default=None))
        if youtube_url:
            return self.url_result(youtube_url, YoutubeIE)

        link = self._search_regex(
            r'(<link[^>]+itemprop=["\'](?:content|embed)Url[^>]*>)',
            webpage, 'content', default=None)
        media_url = extract_attributes(link).get('href') if link else None
        if not media_url:
            media_url = self._search_regex(
                r'"contentUrl"\s*:\s*"(https?://[^"]+)"',
                webpage, 'content url', default=None)

        if not media_url:
            raise ExtractorError('No video found on this page', expected=True)

        if YoutubeIE.suitable(media_url):
            return self.url_result(media_url, YoutubeIE)

        formats = self._extract_m3u8_formats(
            media_url, display_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        title = self._search_regex(
            r'<h1[^>]+itemprop=["\']name[^>]*>([^<]+)', webpage,
            'title', default=None) or self._og_search_title(webpage)

        description = self._html_search_regex(
            r'(?s)<article[^>]+itemprop=["\']description[^>]*>(.+?)</article>',
            webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = unified_timestamp(self._html_search_meta(
            'uploadDate', webpage, 'timestamp'))
        duration = int_or_none(self._html_search_meta(
            'duration', webpage), invscale=60)
        view_count = int_or_none(self._html_search_meta(
            'interactionCount', webpage, 'view count'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
