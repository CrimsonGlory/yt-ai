from .common import InfoExtractor
from ..utils import determine_ext, unescapeHTML, url_or_none


class MirrorCoUKIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mirror\.co\.uk/[/+[\w-]+-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.mirror.co.uk/tv/tv-news/love-island-fans-baffled-after-27163139',
        'md5': 'ebf4aabe18044e80d7a05eae8441aac2',
        'info_dict': {
            'id': '27163139',
            'ext': 'mp4',
            'title': 'Love Island: Gemma Owen enters the villa',
            'description': 'Love Island: Michael Owen\'s daughter Gemma Owen enters the villa.',
            'thumbnail': r're:https?://video\.primis\.tech/.+',
            'display_id': '27163139',
            'timestamp': 1654548965,
            'duration': 58,
            'upload_date': '20220606',
        },
    }, {
        'url': 'https://www.mirror.co.uk/3am/celebrity-news/michael-jacksons-son-blankets-new-25344890',
        'info_dict': {
            'id': '25344890',
            'ext': 'mp4',
            'title': 'Michael Jackson’s son Bigi calls for action on climate change',
            'description': 'md5:d39ceaba2b7a615b4ca6557e7bc40222',
            'thumbnail': r're:https?://video\.primis\.tech/.+',
            'display_id': '25344890',
            'timestamp': 1635752064,
            'duration': 56,
            'upload_date': '20211101',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.mirror.co.uk/sport/football/news/antonio-conte-next-tottenham-manager-25346042',
        'info_dict': {
            'id': '25346042',
            'ext': 'mp4',
            'title': 'Nuno sacked by Tottenham after fifth Premier League defeat of the season',
            'description': 'Nuno Espirito Santo has been sacked as Tottenham boss after only four months in charge.',
            'thumbnail': r're:https?://video\.primis\.tech/.+',
            'display_id': '25346042',
            'timestamp': 1635765039,
            'duration': 41,
            'upload_date': '20211101',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.mirror.co.uk/3am/celebrity-news/johnny-depp-splashes-50k-curry-27160737',
        'info_dict': {
            'id': '27160737',
            'ext': 'mp4',
            'title': 'Johnny Depp Leaves The Grand Hotel in Birmingham',
            'description': 'Johnny Depp Leaves The Grand Hotel in Birmingham.',
            'thumbnail': r're:https?://video\.primis\.tech/.+',
            'display_id': '27160737',
            'timestamp': 1654551170,
            'duration': 66,
            'upload_date': '20220606',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.mirror.co.uk/tv/tv-news/love-islands-liam-could-first-27162602',
        'info_dict': {
            'id': '27162602',
            'ext': 'mp4',
            'title': 'Love Island: Davide reveals plot twist after receiving text',
            'description': 'Love Island: Davide reveals plot twist after receiving text',
            'thumbnail': r're:https?://video\.primis\.tech/.+',
            'display_id': '27162602',
            'timestamp': 1654555548,
            'duration': 24,
            'upload_date': '20220606',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.mirror.co.uk/news/uk-news/william-kate-sent-message-george-27160572',
        'info_dict': {
            'id': '27160572',
            'ext': 'mp4',
            'title': 'Prince William and Kate arrive in Wales with George and Charlotte',
            'description': 'Prince William and Kate Middleton arrive in Wales with children Prince George and Princess Charlotte.',
            'thumbnail': r're:https?://video\.primis\.tech/.+',
            'display_id': '27160572',
            'timestamp': 1654530009,
            'duration': 107,
            'upload_date': '20220606',
        },
        'params': {'skip_download': True},
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        json_ld = self._search_json_ld(webpage, display_id, default={})
        json_ld.pop('ext', None)
        video_url = url_or_none(json_ld.pop('url', None))
        if video_url:
            info = {
                'id': display_id,
                'display_id': display_id,
                **json_ld,
            }
            if determine_ext(video_url) == 'm3u8':
                info['formats'] = self._extract_m3u8_formats(
                    video_url, display_id, 'mp4', m3u8_id='hls')
            else:
                info['url'] = video_url
            return info

        data = self._search_json(
            r'div\s+class="json-placeholder"\s+data-json="',
            webpage, 'data', display_id, transform_source=unescapeHTML)['videoData']

        return {
            '_type': 'url_transparent',
            'url': f'jwplatform:{data["videoId"]}',
            'ie_key': 'JWPlatform',
            'display_id': display_id,
        }
