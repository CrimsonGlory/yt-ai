from .imggaming import ImgGamingBaseIE


class NZRPlusIE(ImgGamingBaseIE):
    IE_NAME = 'nzrplus'
    IE_DESC = 'NZR+'
    _NETRC_MACHINE = 'nzrplus'
    _REALM = 'nzrugby'
    _VALID_URL = (
        r'https?://(?P<domain>(?:(?:www|app)\.)?nzrplus\.com)/'
        r'(?P<type>live|playlist|video)/(?P<id>\d+)'
        r'(?:/[^/?#]+)?'
        r'(?:\?(?:[^#]*\bplaylistId=(?P<playlist_id>\d+)))?')
    _TESTS = [{
        'url': 'https://app.nzrplus.com/video/507175/tour-de-rugby--series-trailer--coming-september',
        'md5': '13ca0df2a363cadb731ab9981952d463',
        'info_dict': {
            'id': '507175',
            'ext': 'mp4',
            'title': 'Tour de Rugby | Series Trailer',
            'description': 'Oscar winner Taika Waititi travels to the rugby mad capital of Europe; France! He has one goal in mind; to see the best of French culture, high fashion, world renowned champagne and of course all things rugby!',
            'thumbnail': r're:https://dve-images\.imggaming\.com/.+',
            'duration': 69,
            'tags': ['DEfree', 'France', 'Rugby', 'Taika', 'Taika Waititi', 'Premium Originals', '1', 'New Zealand', 'Sizzle', 'trailersrow', 'lesbleusrow'],
        },
    }, {
        'url': 'https://app.nzrplus.com/video/507175/tour-de-rugby--series-trailer--coming-september?playlistId=17441',
        'only_matching': True,
    }, {
        'url': 'https://app.nzrplus.com/playlist/17441',
        'only_matching': True,
    }, {
        'url': 'https://nzrplus.com/video/507175',
        'only_matching': True,
    }]

    def _real_initialize(self):
        if self._HEADERS.get('Authorization'):
            return
        token = self._download_json(
            'https://dce-frontoffice.imggaming.com/api/v1/init/', None,
            'Downloading access token', headers=self._HEADERS, query={
                'lk': 'language',
                'readLicences': 'true',
                'countEvents': 'LIVE',
                'menuTargetPlatform': 'WEB',
            })['authentication']['authorisationToken']
        self._HEADERS['Authorization'] = f'Bearer {token}'
