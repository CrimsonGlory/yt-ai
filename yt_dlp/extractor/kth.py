from .common import InfoExtractor
from ..utils import smuggle_url


class KTHIE(InfoExtractor):
    _VALID_URL = r'https?://play\.kth\.se/(?:[^/]+/)+(?P<id>[a-z0-9_]+)'
    _TEST = {
        'url': 'https://play.kth.se/media/Lunch+breakA+De+nya+aff%C3%A4rerna+inom+Fordonsdalen/0_uoop6oz9',
        'md5': 'fbb67b54056dff324eee9ffe675632dc',
        'info_dict': {
            'id': '0_uoop6oz9',
            'ext': 'mp4',
            'title': 'Lunch break: De nya affärerna inom Fordonsdalen',
            'uploader_id': 'kajha@kth.se',
            'duration': 3516,
            'thumbnail': 'https://api.kltr.nordu.net/p/308/sp/30800/thumbnail/entry_id/0_uoop6oz9/version/100032',
            'timestamp': 1647348958,
            'upload_date': '20220315',
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result(
            smuggle_url(f'kaltura:308:{video_id}', {
                'service_url': 'https://api.kaltura.nordu.net'}),
            'Kaltura')
