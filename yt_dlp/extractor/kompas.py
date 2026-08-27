from .jixie import JixieBaseIE


class KompasVideoIE(JixieBaseIE):
    _VALID_URL = r'https?://video\.kompas\.com/\w+/(?P<id>\d+)/(?P<slug>[\w-]+)'
    _TESTS = [{
        'url': 'https://video.kompas.com/watch/1810471/tas-kw-mirip-banget-asli-beginicaramembedakannya',
        'md5': '23bb19fefae5d93c138042c912d0cf7b',
        'info_dict': {
            'id': '1810471',
            'ext': 'mp4',
            'title': 'Tas KW Mirip Banget Asli, Begini\xa0Cara\xa0Membedakannya',
            'description': 'md5:91b436419a9014bd98282c41f0adacc1',
            'uploader_id': '9262bf2590d558736cac4fff7978fcb1',
            'display_id': 'tas-kw-mirip-banget-asli-beginicaramembedakannya',
            'duration': 368.0,
            'timestamp': 1733570788,
            'upload_date': '20241207',
            'thumbnail': 'https://assets-studiohub.kompas.com/video2019/73f614858444241bddf143/e8fe67dab6537c1e9a75c73fc33c0b4a/p_e8fe67dab6537c1e9a75c73fc33c0b4a.jpg',
        },
    }, {
        'url': 'https://video.kompas.com/watch/164474/kim-jong-un-siap-kirim-nuklir-lawan-as-dan-korsel',
        'skip': 'video gone',
        'info_dict': {
            'id': '164474',
            'ext': 'mp4',
            'title': 'Kim Jong Un Siap Kirim Nuklir Lawan AS dan Korsel',
            'description': 'md5:262530c4fb7462398235f9a5dba92456',
            'uploader_id': '9262bf2590d558736cac4fff7978fcb1',
            'display_id': 'kim-jong-un-siap-kirim-nuklir-lawan-as-dan-korsel',
            'duration': 85.066667,
            'categories': ['news'],
            'thumbnail': 'https://video.jixie.media/1001/164474/164474_1280x720.jpg',
            'tags': 'count:9',
        },
    }]

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'slug')
        webpage = self._download_webpage(url, display_id)

        return self._extract_data_from_jixie_id(display_id, video_id, webpage)
