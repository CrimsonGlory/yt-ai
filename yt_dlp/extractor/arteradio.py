from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    clean_podcast_url,
    int_or_none,
    parse_iso8601,
    str_or_none,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ArteRadioAudioblogIE(InfoExtractor):
    IE_DESC = 'ARTE Radio Audioblog'
    _VALID_URL = r'https?://(?:www\.)?audioblog\.arteradio\.com/(?:blog/\d+/podcast|embed)/(?P<id>\d+)'
    _API_BASE = 'https://back-audioblog.arteradio.com'
    _TESTS = [{
        'url': 'https://audioblog.arteradio.com/blog/174532/podcast/174698/la-caverne-ep-1-max-lampin',
        'md5': '538515acc7a07fe535f50cd0cc9dcbac',
        'info_dict': {
            'id': '174698',
            'ext': 'mp3',
            'title': 'La Caverne ep.1 - Max Lampin',
            'description': 'md5:fa9b65eab40d737d39549865a4586b76',
            'thumbnail': 'https://sons-audioblogs.arte.tv/audioblogs/v2/sons/174532/174698/origin_174698_gD0Hp.jpeg',
            'duration': 3194,
            'timestamp': 1637970904,
            'upload_date': '20211126',
            'uploader': 'la caverne',
            'uploader_id': '21458',
            'series': 'La Caverne',
            'series_id': '174532',
            'tags': ['musique', 'rock', 'punk', 'noise'],
            'language': 'fr',
            'vcodec': 'none',
        },
    }, {
        'url': 'https://audioblog.arteradio.com/embed/174698',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        podcast_id = self._match_id(url)
        data = self._download_json(
            f'{self._API_BASE}/node/{podcast_id}', podcast_id,
            query={'_format': 'json'})
        if traverse_obj(data, 'type') != 'podcast':
            raise ExtractorError('Not a public podcast', expected=True)

        media_url = traverse_obj(data, (
            'file_url', {url_or_none}, {clean_podcast_url}))
        if not media_url:
            self.raise_no_formats(
                'No audio URL available', expected=True, video_id=podcast_id)

        return {
            'id': podcast_id,
            'url': media_url,
            'vcodec': 'none',
            **traverse_obj(data, {
                'title': ('title', {str}),
                'description': ('presentation', {clean_html}, {strip_or_none}),
                'thumbnail': ('image_akamai', {url_or_none}),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('created', {parse_iso8601}),
                'uploader': ('blog', 'blogger', 'name', {str}),
                'uploader_id': ('blog', 'blogger', 'uid', {int_or_none}, {str_or_none}),
                'series': ('blog', 'title', {str}),
                'series_id': ('blog', 'id', {int_or_none}, {str_or_none}),
                'tags': ('keywords', ..., 'name', {str}),
                'language': ('blog', 'language', {str}),
            }),
        }
