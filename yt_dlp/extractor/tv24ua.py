import re

from .common import InfoExtractor
from ..utils import determine_ext, js_to_json, mimetype2ext, parse_qs, traverse_obj


class TV24UAVideoIE(InfoExtractor):
    _VALID_URL = r'https?://24tv\.ua/news/showPlayer\.do.*?(?:\?|&)objectId=(?P<id>\d+)'
    _EMBED_REGEX = [rf'<iframe[^>]+?src=["\']?(?P<url>{_VALID_URL}[^"\'>\s]*)']
    IE_NAME = '24tv.ua'
    _CDN_MP4_TMPL = 'https://videocdnl.luxnet.ua/tv24/resources/videos/{path}_main.mp4'
    _TESTS = [{
        'url': 'https://24tv.ua/news/showPlayer.do?objectId=2074790&videoUrl=2022/07/2074790&w=640&h=360',
        'md5': '58ebf15d2aae276a3bda44c1cee5ab74',
        'info_dict': {
            'id': '2074790',
            'ext': 'mp4',
            'title': '2074790',
            'thumbnail': r're:^https?://.*\.jpe?g',
        },
    }, {
        'url': 'https://24tv.ua/news/showPlayer.do?videoUrl=2022/07/2074790&objectId=2074790&w=640&h=360',
        'only_matching': True,
    }]

    _WEBPAGE_TESTS = [
        {
            # iframe embed created from share menu. Player HTML is CF-blocked;
            # Generic identifies the 24tv.ua embed and media is on luxnet CDN.
            'url': 'data:text/html,%3Ciframe%20src=%22https://24tv.ua/news/showPlayer.do?objectId=1886193&videoUrl'
                   '=2022/03/1886193&w=640&h=360%22%20width=%22640%22%20height=%22360%22%20frameborder=%220%22'
                   '%20scrolling=%22no%22%3E%3C/iframe%3E',
            'info_dict': {
                'id': '1886193',
                'ext': 'mp4',
                'title': '1886193',
                'thumbnail': r're:^https?://.*\.jpe?g',
            },
        },
        {
            'url': 'https://24tv.ua/vipalyuyut-nashi-mista-sela-dsns-pokazali-motoroshni-naslidki_n1883966',
            'skip': 'Cloudflare anti-bot',
            'info_dict': {
                'id': '1883966',
                'ext': 'mp4',
                'title': 'Випалюють наші міста та села, – моторошні наслідки обстрілів на Чернігівщині',
                'thumbnail': r're:^https?://.*\.jpe?g',
            },
            'params': {'allowed_extractors': ['Generic', '24tv.ua']},
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_path = traverse_obj(parse_qs(url), ('videoUrl', 0))
        if video_path and not re.fullmatch(r'\d{4}/\d{2}/\d+', video_path):
            video_path = None

        # Player HTML is behind a Cloudflare managed challenge; media is on luxnet.
        webpage = self._download_webpage(url, video_id, fatal=False, expected_status=403)
        if webpage and 'vPlayConfig' not in webpage:
            webpage = None

        formats = []
        subtitles = {}
        thumbnail = None
        for j in re.findall(r'vPlayConfig\.sources\s*=\s*(?P<json>\[{\s*(?s:.+?)\s*}])', webpage or ''):
            sources = self._parse_json(j, video_id, fatal=False, ignore_extra=True, transform_source=js_to_json, errnote='') or []
            for source in sources:
                if mimetype2ext(traverse_obj(source, 'type')) == 'm3u8':
                    f, s = self._extract_m3u8_formats_and_subtitles(source['src'], video_id)
                    formats.extend(f)
                    self._merge_subtitles(subtitles, s)
                else:
                    formats.append({
                        'url': source['src'],
                        'ext': determine_ext(source['src']),
                    })
        if webpage:
            thumbnail = traverse_obj(
                self._search_json(
                    r'var\s*vPlayConfig\s*=\s*', webpage, 'thumbnail',
                    video_id, default=None, transform_source=js_to_json), 'poster')

        if not formats and video_path:
            mp4_url = self._CDN_MP4_TMPL.format(path=video_path)
            formats.append({
                'url': mp4_url,
                'ext': 'mp4',
            })
            thumbnail = thumbnail or f'{mp4_url}.jpeg'

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail or (self._og_search_thumbnail(webpage) if webpage else None),
            'title': self._generic_title('', webpage or '', default=video_id),
            'description': self._og_search_description(webpage, default=None) if webpage else None,
        }
