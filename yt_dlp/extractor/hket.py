from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
    traverse_obj,
    unescapeHTML,
    unified_strdate,
    url_or_none,
)


class HKETIE(InfoExtractor):
    IE_NAME = 'hket'
    IE_DESC = 'Hong Kong Economic Times'
    _VALID_URL = r'https?://video\.hket\.com/(?:video|article)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://video.hket.com/video/4181718',
        'md5': 'f1dc8145607fd13d984dec090395ee06',
        'info_dict': {
            'id': '4181718',
            'ext': 'mp4',
            'title': '手足口病吃水果恐讓潰瘍更痛　醫生教「冰涼飲食法」舒緩痛感',
            'description': '手足口病腸病毒需要提升免疫力戰勝，但酸性水果千萬別吃！兒科專科蘇詠怡醫生教大家一招「冰涼飲食法」，減輕口腔潰瘍疼痛、精準補水。',
            'thumbnail': 'https://static06.hket.com/res/v3/image/video/4180000/4181718/Reels2_1024.jpg',
            'duration': 41,
            'timestamp': 1788235500,
            'upload_date': '20260901',
            'series': '健康專題影片',
            'tags': ['實體詞', '疾病／痛症／損傷／病徵', '痱滋', '工種', '醫生', '病菌及病毒', '腸病毒', '手足口病'],
        },
    }, {
        'url': 'https://video.hket.com/video/3388102?r=cpstna',
        'only_matching': True,
    }, {
        'url': 'https://video.hket.com/article/3278159',
        'only_matching': True,
    }, {
        'url': 'https://video.hket.com/video/3388102/%E3%80%90%E9%9D%92%E5%A7%90%E8%A9%B1%E3%80%91%E8%B7%8C%E8%B7%8C%E8%B7%8C%20%E4%BB%B2%E6%9C%89%E4%B9%9C%E6%9C%AA%E8%B7%8C%EF%BC%9F',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        attrs = extract_attributes(self._search_regex(
            r'(<video\b[^>]+>)', webpage, 'video player', default=''))
        m3u8_url = url_or_none(traverse_obj(attrs, 'data-m3u8')) or url_or_none(
            unescapeHTML(self._search_regex(
                r'\bdata-m3u8=(["\'])(?P<url>https?://[^"\']+)\1',
                webpage, 'm3u8 url', group='url')))

        is_live = attrs.get('data-live') == 'true'
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', live=is_live,
            headers={'Referer': 'https://video.hket.com/'})

        info = self._search_json_ld(webpage, video_id, default={})
        info.pop('url', None)
        info.pop('ext', None)

        tags = [t.strip() for t in (attrs.get('data-formaltag') or '').split(',') if t.strip()]
        info.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (attrs.get('data-videotitle')
                      or self._og_search_title(webpage, default=None)
                      or info.get('title')
                      or self._html_extract_title(webpage)),
            'description': info.get('description') or self._og_search_description(webpage, default=None),
            'thumbnail': (info.get('thumbnail')
                          or traverse_obj(info, ('thumbnails', 0, 'url'))
                          or self._og_search_thumbnail(webpage, default=None)),
            'duration': info.get('duration') or int_or_none(attrs.get('data-length')),
            'upload_date': info.get('upload_date') or unified_strdate(attrs.get('data-videopublishdate')),
            'series': attrs.get('data-videoprogram') or None,
            'tags': tags or None,
        })
        if is_live:
            info['live_status'] = 'is_live'
        elif attrs.get('data-videotype') == 'live_archive':
            info['live_status'] = 'was_live'
        return info
