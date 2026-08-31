from .peertube import PeerTubeIE, PeerTubePlaylistIE


class InfosecExchangeIE(PeerTubeIE):  # XXX: Do not subclass from concrete IE
    IE_NAME = 'InfosecExchange'
    IE_DESC = 'Infosec.Exchange Video'
    _VALID_URL = rf'''(?x)
        https?://(?P<host>video\.infosec\.exchange)/
        (?:videos/(?:watch|embed)|api/v\d/videos|w)/
        (?P<id>{PeerTubeIE._UUID_RE})
    '''
    _EMBED_REGEX = [rf'''(?x)<iframe[^>]+\bsrc=["'](?P<url>(?:https?:)?//video\.infosec\.exchange/videos/embed/{PeerTubeIE._UUID_RE})''']
    _TESTS = [{
        'url': 'https://video.infosec.exchange/w/e1ZoLkBBDcfZyj8hWALZLd',
        'md5': 'c426e582de5b47427ef138816d269922',
        'info_dict': {
            'id': 'e1ZoLkBBDcfZyj8hWALZLd',
            'ext': 'mp4',
            'title': 'Rust 101 - 1: Course intro',
            'description': 'md5:ba64b8edf2e9d012134a10331b57eaa4',
            'thumbnail': r're:https?://video\.infosec\.exchange/lazy-static/thumbnails/.+\.jpg',
            'timestamp': 1717958140,
            'upload_date': '20240609',
            'uploader': 'Andy Balaam',
            'uploader_id': '385470',
            'uploader_url': 'https://video.infosec.exchange/accounts/andybalaam',
            'channel': "Andy Balaam's programming lectures",
            'channel_id': '23520',
            'channel_url': 'https://video.infosec.exchange/video-channels/andybalaam_lectures',
            'language': 'en',
            'license': 'Attribution - Share Alike',
            'duration': 584,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': ['beginners', 'programming', 'rust'],
            'categories': ['Science & Technology'],
        },
        'params': {'format': 'b[protocol=https]'},
        'expected_warnings': ['HTTP Error 400: Bad Request'],
    }, {
        'url': 'https://video.infosec.exchange/videos/watch/696a2c05-7ecd-4292-a270-459409eea548',
        'only_matching': True,
    }, {
        'url': 'https://video.infosec.exchange/videos/embed/696a2c05-7ecd-4292-a270-459409eea548',
        'only_matching': True,
    }]


class InfosecExchangePlaylistIE(PeerTubePlaylistIE):  # XXX: Do not subclass from concrete IE
    IE_NAME = 'InfosecExchange:Playlist'
    _VALID_URL = r'''(?x)
        https?://(?P<host>video\.infosec\.exchange)/
        (?P<type>a|c|w/p)/(?P<id>[^/?#]+)
    '''
    _TESTS = [{
        'url': 'https://video.infosec.exchange/w/p/5044b454-2043-485c-8832-eee872a0251b',
        'info_dict': {
            'id': '5044b454-2043-485c-8832-eee872a0251b',
            'title': 'Rust 101 - learn to code Rust!',
            'description': 'md5:15debeb39dd3cdee0eb95cc8e50aa73a',
            'channel': 'andybalaam',
            'channel_id': '385470',
            'thumbnail': r're:https?://video\.infosec\.exchange/lazy-static/thumbnails/.+\.jpg',
            'timestamp': 1717921925,
            'upload_date': '20240609',
        },
        'playlist_mincount': 50,
    }, {
        'url': 'https://video.infosec.exchange/c/andybalaam_lectures/videos',
        'only_matching': True,
    }]

    def fetch_page(self, host, playlist_id, playlist_type, page):
        for entry in super().fetch_page(host, playlist_id, playlist_type, page):
            yield {**entry, 'ie_key': InfosecExchangeIE.ie_key()}
