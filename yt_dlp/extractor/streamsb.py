import binascii
import random
import string

from .common import InfoExtractor
from ..utils import url_basename, urljoin


def streamsb_to_ascii_hex(value):
    return binascii.hexlify(value.encode()).decode('ascii')


def streamsb_random_string(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))


class StreamsbIE(InfoExtractor):
    IE_NAME = 'viewsb'
    IE_DESC = 'viewsb.com (StreamSB)'
    _DOMAINS = ('viewsb.com',)
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>%s)/(?:embed-)?(?P<id>[0-9a-zA-Z]+)' % '|'.join(_DOMAINS)
    _TESTS = [{
        'url': 'https://viewsb.com/dxfvlu4qanjx',
        'md5': '488d111a63415369bf90ea83adc8a325',
        'info_dict': {
            'id': 'dxfvlu4qanjx',
            'ext': 'mp4',
            'title': 'Sintel',
        },
    }, {
        'url': 'https://www.viewsb.com/dxfvlu4qanjx',
        'only_matching': True,
    }, {
        'url': 'https://viewsb.com/embed-dxfvlu4qanjx',
        'only_matching': True,
    }]

    def _build_sources_url(self, domain, video_code, app_version='50'):
        req = '||'.join((
            streamsb_random_string(12),
            video_code,
            streamsb_random_string(12),
            'streamsb',
        ))
        return f'https://{domain}/sources{app_version}/{streamsb_to_ascii_hex(req)}'

    def _real_extract(self, url):
        domain, video_id = self._match_valid_url(url).group('domain', 'id')
        webpage = self._download_webpage(url, video_id)

        iframe_rel_url = self._search_regex(
            r'(?i)<iframe\b[^>]+\bsrc\s*=\s*([\'"])(?P<path>/[^\'"]+\.html)\1',
            webpage, 'iframe', group='path', default=None)
        if iframe_rel_url:
            iframe_url = urljoin(f'https://{domain}', iframe_rel_url)
            iframe_data = self._download_webpage(iframe_url, video_id)
        else:
            iframe_url = url
            iframe_data = webpage

        app_version = self._search_regex(
            r'<script\b[^>]+\bsrc\s*=\s*["\'][^"\']*/app\.min\.(\d+)\.js',
            iframe_data, 'app version', default='50')
        video_code = url_basename(iframe_url).rsplit('.', 1)[0] or video_id
        sources_url = self._build_sources_url(domain, video_code, app_version)

        player_data = self._download_json(sources_url, video_id, headers={
            'Referer': iframe_url,
            'watchsb': 'sbstream',
        })
        stream_data = player_data['stream_data']
        formats = self._extract_m3u8_formats(
            stream_data['file'], video_id, ext='mp4', m3u8_id='hls', fatal=False)

        return {
            'id': video_id,
            'title': stream_data.get('title') or video_id,
            'formats': formats,
        }
