from .common import InfoExtractor
from .jwplatform import JWPlatformIE


class BundesligaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bundesliga\.com/[a-z]{2}/bundesliga/videos(?:/[^?]+)?\?vid=(?P<id>[a-zA-Z0-9]{8})'
    _TESTS = [
        {
            'url': 'https://www.bundesliga.com/en/bundesliga/videos?vid=bhhHkKyN',
            'md5': '8ec7b79ecc8e6cd886c68b929185be23',
            'info_dict': {
            'id': 'bhhHkKyN',
            'ext': 'mp4',
            'title': 'Watch: Alphonso Davies and Jeremie Frimpong head-to-head',
            'description': 'md5:803d4411bd134140c774021dd4b7598b',
            'duration': 146.0,
            'thumbnail': 'https://cdn.jwplayer.com/v2/media/bhhHkKyN/poster.jpg?width=720',
            'timestamp': 1664366511,
            'upload_date': '20220928',
        },
        },
        {
            'url': 'https://www.bundesliga.com/en/bundesliga/videos/latest-features/T8IKc8TX?vid=ROHjs06G',
            'only_matching': True,
        },
        {
            'url': 'https://www.bundesliga.com/en/bundesliga/videos/goals?vid=mOG56vWA',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result(f'jwplatform:{video_id}', JWPlatformIE, video_id)
