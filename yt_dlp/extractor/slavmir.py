from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    parse_duration,
    url_or_none,
    urljoin,
)
from ..utils.traversal import (
    find_element,
    traverse_obj,
)


class SlavmirIE(InfoExtractor):
    IE_NAME = 'slavmir'
    IE_DESC = 'Slavmir TV'
    _VALID_URL = r'https?://(?:www\.)?slavmir\.tv/video/detail/(?P<id>[\w-]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://www.slavmir.tv/video/detail/kak-odezhda-vliyaet-na-nashu-zhizn-kak-pravilno-odevatsya/',
        'md5': '6cb573676e6b06ddd285081883db2d2b',
        'info_dict': {
            'id': 'kak-odezhda-vliyaet-na-nashu-zhizn-kak-pravilno-odevatsya',
            'ext': 'mp4',
            'title': 'Как одежда влияет на нашу жизнь? Как правильно одеваться? (38:50)',
            'description': 'md5:6dec2007cfa8de73dd8bc9f87ca41a80',
            'thumbnail': 'https://www.slavmir.tv/upload/iblock/e8d/kak_odezhda_vliyaet_na_nashu_zhizn_kak_pravilno_odevatsya.jpg',
            'duration': 2330,
            'uploader': 'Славянскiй МiРЪ',
        },
    }, {
        'url': 'https://www.slavmir.tv/video/detail/kak-nas-otuchali-pomnit-svoikh-predkov-i-stroit-roda-kak-vernut-byloe-film-51-02/',
        'only_matching': True,
    }, {
        'url': 'https://slavmir.tv/video/detail/kak-odezhda-vliyaet-na-nashu-zhizn-kak-pravilno-odevatsya',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player = extract_attributes(traverse_obj(
            webpage, {find_element(id='video-player', html=True)}) or '')
        m3u8_url = url_or_none(player.get('data-url'))
        if not m3u8_url:
            self.raise_login_required(
                'This video is only available with a Slavmir subscription', method=None)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls')

        title = (
            player.get('data-title')
            or player.get('data-name')
            or self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None))

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None) or urljoin(
                url, player.get('data-picture')),
            'duration': parse_duration(self._search_regex(
                r'\((\d+:\d+(?::\d+)?)\)\s*$', title or '', 'duration', default=None)),
            'uploader': player.get('data-artist') or None,
            'formats': formats,
            'subtitles': subtitles,
        }
