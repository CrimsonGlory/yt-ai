import json
import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    try_get,
    url_or_none,
)


class PolsatGoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?polsat(?:box)?go\.pl/.+/(?P<id>[0-9a-fA-F]+)(?:[/#?]|$)'
    _TESTS = [{
        'url': 'https://polsatgo.pl/wideo/seriale/swiat-wedlug-kiepskich/5024045/sezon-1/5028300/swiat-wedlug-kiepskich-odcinek-88/4121',
        'skip': 'Polsat Go shut down 2023-08-31; video no longer available',
        'info_dict': {
            'id': '4121',
            'ext': 'mp4',
            'title': 'Świat według Kiepskich - Odcinek 88',
            'age_limit': 12,
        },
    }, {
        'url': 'https://polsatboxgo.pl/wideo/zwierzostan/5029183/zwiastun-1/42f601b4869a83e89e2592783f91d739/ogladaj',
        'skip': 'Requires a Polsat Box Go subscription',
        'info_dict': {
            'id': '42f601b4869a83e89e2592783f91d739',
            'ext': 'mp4',
            'title': 'Zwiastun 1',
            'age_limit': 16,
        },
    }]

    def _extract_formats(self, sources, video_id):
        for source in sources or []:
            if not source.get('id'):
                continue
            try:
                url = url_or_none(self._call_api(
                    'drm', video_id, 'getPseudoLicense',
                    {'mediaId': video_id, 'sourceId': source['id']}).get('url'))
            except ExtractorError as e:
                if e.expected:
                    continue
                raise
            if not url:
                continue
            yield {
                'url': url,
                'height': int_or_none(try_get(source, lambda x: x['quality'][:-1])),
            }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media = self._call_api('navigation', video_id, 'prePlayData', {'mediaId': video_id})['mediaItem']

        formats = list(self._extract_formats(
            try_get(media, lambda x: x['playback']['mediaSources']), video_id))
        if not formats:
            self.raise_login_required(
                'This video requires a Polsat Box Go subscription', method=None)

        return {
            'id': video_id,
            'title': media['displayInfo']['title'],
            'formats': formats,
            'age_limit': int_or_none(media['displayInfo']['ageGroup']),
        }

    def _call_api(self, endpoint, media_id, method, params):
        rand_uuid = str(uuid.uuid4())
        res = self._download_json(
            f'https://b2c-mobile.redefine.pl/rpc/{endpoint}/', media_id,
            note=f'Downloading {method} JSON metadata',
            data=json.dumps({
                'method': method,
                'id': '2137',
                'jsonrpc': '2.0',
                'params': {
                    **params,
                    'userAgentData': {
                        'deviceType': 'mobile',
                        'application': 'native',
                        'os': 'android',
                        'build': 10003,
                        'widevine': False,
                        'portal': 'pbg',
                        'player': 'cpplayer',
                    },
                    'deviceId': {
                        'type': 'other',
                        'value': rand_uuid,
                    },
                    'clientId': rand_uuid,
                    'cpid': 1,
                },
            }).encode(),
            headers={'Content-type': 'application/json'})
        if not res.get('result'):
            error = res.get('error') or {}
            data = error.get('data') or {}
            user_message = data.get('userMessage') or error.get('message') or ''
            code = error.get('code')
            if 'zamknięcie serwisu Polsat Go' in user_message:
                raise ExtractorError(
                    'Polsat Go shut down on 2023-08-31; content moved to Polsat Box Go (subscription required)',
                    expected=True)
            if code == 13404:
                raise ExtractorError(
                    'This video is either unavailable in your region or is DRM protected', expected=True)
            if code in (13403, 13443):
                raise ExtractorError('This video requires a Polsat Box Go subscription', expected=True)
            raise ExtractorError(f'Solorz said: {error.get("message")} - {user_message}')
        return res['result']
