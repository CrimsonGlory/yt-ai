from .common import InfoExtractor
from .vimeo import VimeoIE
from .youtube import YoutubeIE
from ..utils import (
    int_or_none,
    parse_iso8601,
    update_url_query,
)


class AmaraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?amara\.org/(?:\w+/)?videos/(?P<id>\w+)'
    _TESTS = [{
        # Direct Link (TED HTML5)
        'url': 'https://amara.org/en/videos/U7nug0p1xZ5a/info/we-need-to-talk-about-an-injustice/',
        'md5': '425e42807d634b0f2e800b80af94d273',
        'info_dict': {
            'id': 'U7nug0p1xZ5a',
            'ext': 'mp4',
            'title': 'We need to talk about an injustice',
            'description': 'md5:e6b5445ecd4d88db98433e95383086d8',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': dict,
            'duration': 1400,
            'timestamp': 1331095533,
            'upload_date': '20120307',
        },
    }, {
        # Youtube
        'url': 'https://amara.org/en/videos/jVx79ZKGK1ky/info/why-jury-trials-are-becoming-less-common/?tab=video',
        'skip': 'video gone',
        'md5': 'ea10daf2b6154b8c1ecf9922aca5e8ae',
        'info_dict': {
            'id': 'h6ZuVdvYnfE',
            'ext': 'mp4',
            'title': 'Why jury trials are becoming less common',
            'description': 'md5:a61811c319943960b6ab1c23e0cbc2c1',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': dict,
            'upload_date': '20160813',
            'uploader': 'PBS NewsHour',
            'uploader_id': 'PBSNewsHour',
            'timestamp': 1549639570,
        },
    }, {
        # Vimeo
        'url': 'https://amara.org/en/videos/kYkK1VUTWW5I/info/vimeo-at-ces-2011',
        'skip': 'HTTP Error 403',
        'md5': '99392c75fa05d432a8f11df03612195e',
        'info_dict': {
            'id': '18622084',
            'ext': 'mov',
            'title': 'Vimeo at CES 2011!',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': dict,
            'timestamp': 1294763658,
            'upload_date': '20110111',
            'uploader': 'Sam Morrill',
            'uploader_id': 'sammorrill',
        },
    }, {
        # Direct Link
        'url': 'https://amara.org/en/videos/s8KL7I3jLmh6/info/the-danger-of-a-single-story/',
        'skip': 'video gone',
        'md5': 'd3970f08512738ee60c5807311ff5d3f',
        'info_dict': {
            'id': 's8KL7I3jLmh6',
            'ext': 'mp4',
            'title': 'The danger of a single story',
            'description': 'md5:d769b31139c3b8bb5be9177f62ea3f23',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': dict,
            'upload_date': '20091007',
            'timestamp': 1254942511,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._download_json(
            f'https://amara.org/api/videos/{video_id}/',
            video_id, query={'format': 'json'})
        title = meta['title']
        video_url = meta['all_urls'][0]

        subtitles = {}
        for language in (meta.get('languages') or []):
            subtitles_uri = language.get('subtitles_uri')
            if not (subtitles_uri and language.get('published')):
                continue
            subtitle = subtitles.setdefault(language.get('code') or 'en', [])
            for f in ('json', 'srt', 'vtt'):
                subtitle.append({
                    'ext': f,
                    'url': update_url_query(subtitles_uri, {'format': f}),
                })

        info = {
            'url': video_url,
            'id': video_id,
            'subtitles': subtitles,
            'title': title,
            'description': meta.get('description'),
            'thumbnail': meta.get('thumbnail'),
            'duration': int_or_none(meta.get('duration')),
            'timestamp': parse_iso8601(meta.get('created')),
        }

        for ie in (YoutubeIE, VimeoIE):
            if ie.suitable(video_url):
                info.update({
                    '_type': 'url_transparent',
                    'ie_key': ie.ie_key(),
                })
                break

        return info
