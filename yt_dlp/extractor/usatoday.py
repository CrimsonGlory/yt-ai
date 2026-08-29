from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class USATodayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?usatoday\.com/(?:[^/]+/)*(?P<id>[^?/#]+)'
    _TESTS = [{
        'url': 'https://www.usatoday.com/videos/news/have-you-seen/2026/08/28/drone-captures-ancient-dinosaur-footprints-turned-into-puddles/91512551007/',
        'info_dict': {
            'id': '91512551007',
            'ext': 'mp4',
            'title': 'Drone captures ancient dinosaur footprints turned into puddles',
            'description': 'md5:1c1251a336989d1f725cbc1b6b9f6a15',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg)',
            'duration': 30,
            'timestamp': 1787944374,
            'upload_date': '20260828',
            'uploader': 'Anastasiia Riddle',
        },
    }, {
        # Brightcove Partner ID = 29906170001
        'url': 'http://www.usatoday.com/media/cinematic/video/81729424/us-france-warn-syrian-regime-ahead-of-new-peace-talks/',
        'skip': 'video gone',
        'md5': '033587d2529dc3411a1ab3644c3b8827',
        'info_dict': {
            'id': '4799374959001',
            'ext': 'mp4',
            'title': 'US, France warn Syrian regime ahead of new peace talks',
            'timestamp': 1457891045,
            'description': 'md5:7e50464fdf2126b0f533748d3c78d58f',
            'uploader_id': '29906170001',
            'upload_date': '20160313',
        },
    }, {
        # ui-video-data[asset_metadata][items][brightcoveaccount] = 28911775001
        'url': 'https://www.usatoday.com/story/tech/science/2018/08/21/yellowstone-supervolcano-eruption-stop-worrying-its-blow/973633002/',
        'skip': 'video gone',
        'info_dict': {
            'id': '5824495846001',
            'ext': 'mp4',
            'title': 'Yellowstone more likely to crack rather than explode',
            'timestamp': 1534790612,
            'description': 'md5:3715e7927639a4f16b474e9391687c62',
            'uploader_id': '28911775001',
            'upload_date': '20180820',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_data = self._search_json(
            r'\bdata-c-vpd=(["\'])', webpage, 'video data', display_id,
            end_pattern=r'\1', default={}, transform_source=unescapeHTML)
        json_ld = self._search_json_ld(webpage, display_id, default={})

        video_id = traverse_obj(video_data, ('id', {str_or_none})) or display_id
        hls_url = traverse_obj(video_data, ('hlsURL', {url_or_none}))
        if not hls_url:
            raise ExtractorError('no video on the webpage', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls')

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (traverse_obj(video_data, (('title', 'headline'), {str}, filter, any))
                      or json_ld.get('title')),
            'description': video_data.get('promoBrief') or json_ld.get('description'),
            'thumbnail': url_or_none(video_data.get('videoStill')) or json_ld.get('thumbnail'),
            'duration': int_or_none(video_data.get('length')) or json_ld.get('duration'),
            'timestamp': (int_or_none(video_data.get('cd'), scale=1000)
                          or json_ld.get('timestamp')),
            'uploader': video_data.get('byline') or video_data.get('origin'),
        }
