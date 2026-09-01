from .ukdevilz import UKDevilzIE


class UKDevilz18IE(UKDevilzIE):
    IE_NAME = 'ukdevilz:18'
    IE_DESC = '18.ukdevilz.com'
    _VALID_URL = r'https?://(?:www\.)?18\.ukdevilz\.com/watch/(?P<id>-?\d+_\d+)'
    _TESTS = [{
        'url': 'https://18.ukdevilz.com/watch/-181972558_456239071',
        'md5': '4cb5fe595c900bf7d48bbaa3085f1538',
        'info_dict': {
            'id': '-181972558_456239071',
            'ext': 'mp4',
            'title': 'Остановил время и рассматривает пизды девушек (голые телки в супермаркете, девушки без трусов, пизда в фильме без цензуры)',
            'description': 'Video Остановил время и рассматривает пизды девушек (голые телки в супермаркете, девушки без трусов, пизда в фильме без цензуры) HQ Mp4',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 121,
            'view_count': int,
            'like_count': int,
            'upload_date': '20190526',
            'timestamp': 1558828800,
            'tags': ['голые', 'девушек', 'девушки', 'пизда', 'фильме', 'цензуры', 'телки'],
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.18.ukdevilz.com/watch/-181972558_456239071',
        'only_matching': True,
    }]
