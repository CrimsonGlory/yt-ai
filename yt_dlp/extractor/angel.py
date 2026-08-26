import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    merge_dicts,
    traverse_obj,
    url_or_none,
)


class AngelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?angel\.com/watch/(?P<series>[^/?#]+)/episode/(?P<id>[\w-]+)/season-(?P<season_number>\d+)/episode-(?P<episode_number>\d+)/(?P<title>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.angel.com/watch/tuttle-twins/episode/2f3d0382-ea82-4cdc-958e-84fbadadc710/season-1/episode-1/when-laws-give-you-lemons',
        'md5': 'bca0509e0b6a1af9f154b0f1b5be79bf',
        'info_dict': {
            'id': '2f3d0382-ea82-4cdc-958e-84fbadadc710',
            'ext': 'mp4',
            'title': 'When Laws Give You Lemons',
            'description': 'md5:73b704897c20ab59c433a9c0a8202d5e',
            'thumbnail': r're:https?://images\.angelstudios\.com/image/upload/.+',
            'duration': 1265,
            'timestamp': 1633996800,
            'upload_date': '20211012',
            'series': 'Tuttle Twins',
            'season': 'Tuttle Twins - Season 1',
            'season_number': 1,
            'episode': 'Tuttle Twins S1E1: When Laws Give You Lemons',
            'episode_number': 1,
        },
        # HLS --test only fetches the fMP4 init fragment (~1KB), below the default 10KB check
        'file_minsize': None,
        'params': {
            'format': 'bv[vcodec^=avc1]/bv/b',
        },
    }, {
        'url': 'https://www.angel.com/watch/the-chosen/episode/8dfb714d-bca5-4812-8125-24fb9514cd10/season-1/episode-1/i-have-called-you-by-name',
        'skip': 'This video is no longer available',
        'info_dict': {
            'id': '8dfb714d-bca5-4812-8125-24fb9514cd10',
            'ext': 'mp4',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        # JSON-LD contentUrl is the webpage, not a media stream
        json_ld.pop('url', None)

        m3u8_url = traverse_obj(self._search_nextjs_data(webpage, video_id), (
            'props', 'pageProps', (('episode', 'source', 'url'), ('contentEpisode', 'url')), {url_or_none}),
            get_all=False)
        if not m3u8_url:
            raise ExtractorError('Unable to extract HLS URL', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', note='Downloading HD m3u8 information')

        # Angel uses cloudinary in the background and supports image transformations.
        # We remove these transformations and return the source file
        base_thumbnail_url = url_or_none(self._og_search_thumbnail(webpage))
        if not base_thumbnail_url:
            base_thumbnail_url = traverse_obj(json_ld, ('thumbnails', 0, 'url', {url_or_none}))
        json_ld.pop('thumbnails', None)
        thumbnail = re.sub(
            r'(/upload)/.+?(/v\d+/(?:angel-app|studio-app)/.+)$',
            r'\1\2', base_thumbnail_url) if base_thumbnail_url else None

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
        }, json_ld, {
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
        })
