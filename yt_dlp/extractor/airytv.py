from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AiryTVIE(InfoExtractor):
    IE_DESC = 'Airy TV'
    _VALID_URL = r'https?://(?:(?:www|live)\.)?airy\.tv/(?:on-demand|vod)/(?:episode|movie)/(?P<id>\d+)'
    _API_BASE = 'https://api.airy.tv/api/v2.1.7'
    _TESTS = [{
        'url': 'https://live.airy.tv/on-demand/episode/1537775',
        'md5': 'd441d11e93a7478d92addbd677b8981a',
        'info_dict': {
            'id': '1537775',
            'ext': 'mp4',
            'title': 'Mission Impossible',
            'description': 'md5:358b37bbc14b58f7263342e47a683d7e',
            'thumbnail': 'https://storage.googleapis.com/showfer_thumbnail/IzAvBqc-PazW72dBShbgn.jpg',
            'duration': 2921,
            'series': 'Mission Impossible',
            'series_id': '1537771',
            'categories': ['TV Shows'],
            'tags': ['TV SHows'],
        },
    }, {
        'url': 'https://airy.tv/on-demand/movie/1537216',
        'only_matching': True,
    }, {
        'url': 'https://airy.tv/vod/episode/1537775',
        'only_matching': True,
    }, {
        'url': 'https://www.airy.tv/on-demand/episode/1537775',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            f'{self._API_BASE}/content/{video_id}', video_id,
            headers={'Accept': 'application/json'})
        if traverse_obj(data, 'status') == 'error':
            raise ExtractorError(
                traverse_obj(data, ('errors', 'error', {str})) or 'Airy TV API error',
                expected=True)

        item = (
            traverse_obj(data, ('response', 'episode', {dict}))
            or traverse_obj(data, ('response', 'movie', {dict}))
            or traverse_obj(data, ('response', {dict})))
        if not item:
            raise ExtractorError('Unable to extract Airy TV video', expected=True)

        media_url = traverse_obj(item, ('sourceUrl', {url_or_none}))
        if not media_url:
            self.raise_no_formats('No video source', expected=True, video_id=video_id)

        ext = determine_ext(media_url, 'mp4')
        if ext == 'm3u8' or traverse_obj(item, 'mediaType') == 'hls':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats, subtitles = [{'url': media_url, 'ext': ext}], {}

        sub_url = traverse_obj(item, ('subtitleUrl', {url_or_none}))
        if sub_url:
            subtitles.setdefault('und', []).append({'url': sub_url})

        return {
            'id': str_or_none(item.get('id')) or video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(item, {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'thumbnail': ('posters', ('desktop', 'tablet', 'mobile'), {url_or_none}, any),
                'duration': ('duration', {int_or_none}),
                'series': ('series', 'name', {str}),
                'series_id': ('series', 'id', {str_or_none}),
                'average_rating': ('rating', {float_or_none}),
                'genres': ('genres', ..., {str}),
                'tags': ('keywords', ..., {str}),
                'categories': ('category', 'name', {str}, all),
            }),
        }
