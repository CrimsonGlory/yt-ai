import contextlib
import json

from .common import InfoExtractor
from ..utils import int_or_none


class PodomaticIE(InfoExtractor):
    IE_NAME = 'podomatic'
    _VALID_URL = r'''(?x)
                    (?P<proto>https?)://
                        (?:
                            (?P<channel>[^.]+)\.podomatic\.com/entry|
                            (?:www\.)?podomatic\.com/podcasts/(?P<channel_2>[^/]+)/episodes
                        )/
                        (?P<id>[^/?#&]+)
                '''

    _TESTS = [{
        'url': 'http://scienceteachingtips.podomatic.com/entry/2009-01-02T16_03_35-08_00',
        'skip': 'video gone',
        'md5': '84bb855fcf3429e6bf72460e1eed782d',
        'info_dict': {
            'id': '2009-01-02T16_03_35-08_00',
            'ext': 'mp3',
            'uploader': 'Science Teaching Tips',
            'uploader_id': 'scienceteachingtips',
            'title': '64.  When the Moon Hits Your Eye',
            'duration': 446,
        },
    }, {
        'url': 'http://ostbahnhof.podomatic.com/entry/2013-11-15T16_31_21-08_00',
        'skip': 'video gone',
        'md5': 'd2cf443931b6148e27638650e2638297',
        'info_dict': {
            'id': '2013-11-15T16_31_21-08_00',
            'ext': 'mp3',
            'uploader': 'Ostbahnhof / Techno Mix',
            'uploader_id': 'ostbahnhof',
            'title': 'Einunddreizig',
            'duration': 3799,
        },
    }, {
        'url': 'https://www.podomatic.com/podcasts/scienceteachingtips/episodes/2009-01-02T16_03_35-08_00',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        channel = mobj.group('channel') or mobj.group('channel_2')

        json_url = ('{}://{}.podomatic.com/entry/embed_params/{}?permalink=true&rtmp=0'.format(
            mobj.group('proto'), channel, video_id))
        data_json = self._download_webpage(
            json_url, video_id, 'Downloading video info', fatal=False)
        data = {}
        if data_json:
            with contextlib.suppress(ValueError, TypeError, json.JSONDecodeError):
                data = json.loads(data_json)

        video_url = data.get('downloadLink')
        if not video_url and data.get('streamer') and data.get('mediaLocation'):
            video_url = '{}/{}'.format(data['streamer'].replace('rtmp', 'http'), data['mediaLocation'])

        webpage = None
        if not video_url:
            webpage = self._download_webpage(url, video_id)
            json_ld = self._search_json_ld(webpage, video_id, default={})
            video_url = (
                json_ld.get('url') or json_ld.get('contentUrl')
                or self._og_search_property('og:audio', webpage, default=None)
                or self._og_search_video_url(webpage, default=None)
                or self._search_regex(
                    r'(https?://[^"\']+\.(?:mp3|m4a|mp4)[^"\']*)', webpage, 'media url', default=None))
            data.setdefault('title', json_ld.get('title') or self._og_search_title(webpage, default=video_id))
            data.setdefault('imageLocation', json_ld.get('thumbnails') or self._og_search_thumbnail(webpage))
            data.setdefault('podcast', self._og_search_property('og:site_name', webpage, default=channel))

        return {
            'id': video_id,
            'url': video_url,
            'title': data.get('title') or video_id,
            'uploader': data.get('podcast'),
            'uploader_id': channel,
            'thumbnail': data.get('imageLocation'),
            'duration': int_or_none(data.get('length'), 1000),
        }
