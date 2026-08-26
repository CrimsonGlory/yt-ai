from .common import InfoExtractor
from .jwplatform import JWPlatformIE


class BusinessInsiderIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?businessinsider\.(?:com|nl)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.businessinsider.com/excel-index-match-vlookup-video-how-to-2015-2?IR=T',
        'md5': '9cd25f3aeddbcd5bfc442761a5719d27',
        'info_dict': {
            'id': '24hZsa73',
            'ext': 'mp4',
            'title': 'This is what separates the Excel masters from the wannabes',
            'description': '',
            'thumbnail': r're:https?://cdn\.jwplayer\.com/v2/media/.+',
            'upload_date': '20150209',
            'timestamp': 1423507627,
            'duration': 191.0,
        },
        'params': {'format': 'best[protocol=https]'},
    }, {
        'url': 'http://uk.businessinsider.com/how-much-radiation-youre-exposed-to-in-everyday-life-2016-6',
        'skip': 'uk.businessinsider.com domain is gone',
        'md5': 'ffed3e1e12a6f950aa2f7d83851b497a',
        'info_dict': {
            'id': 'cjGDb0X9',
            'ext': 'mp4',
            'title': 'Bananas give you more radiation exposure than living next to a nuclear power plant',
            'description': 'md5:0175a3baf200dd8fa658f94cade841b3',
            'upload_date': '20160611',
            'timestamp': 1465675620,
        },
    }, {
        'url': 'https://www.businessinsider.nl/5-scientifically-proven-things-make-you-less-attractive-2017-7/',
        'skip': 'video gone',
        'md5': '43f438dbc6da0b89f5ac42f68529d84a',
        'info_dict': {
            'id': '5zJwd4FK',
            'ext': 'mp4',
            'title': 'Deze dingen zorgen ervoor dat je minder snel een date scoort',
            'description': 'md5:2af8975825d38a4fed24717bbe51db49',
            'upload_date': '20170705',
            'timestamp': 1499270528,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        jwplatform_id = self._search_regex(
            (r'data-media-id=["\']([a-zA-Z0-9]{8})',
             r'id=["\']jwplayer_([a-zA-Z0-9]{8})',
             r'id["\']?\s*:\s*["\']?([a-zA-Z0-9]{8})',
             r'(?:jwplatform\.com/players/|jwplayer_)([a-zA-Z0-9]{8})'),
            webpage, 'jwplatform id')
        return self.url_result(
            f'jwplatform:{jwplatform_id}', ie=JWPlatformIE.ie_key(),
            video_id=video_id)
