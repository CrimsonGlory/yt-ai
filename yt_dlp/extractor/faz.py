import re

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..compat import compat_etree_fromstring
from ..utils import (
    int_or_none,
    xpath_element,
    xpath_text,
)


class FazIE(InfoExtractor):
    IE_NAME = 'faz.net'
    _VALID_URL = r'https?://(?:www\.)?faz\.net/(?:[^/]+/)*.*?-(?P<id>\d+)\.html'

    _TESTS = [{
        # Current FAZ video pages embed YouTube
        'url': 'https://www.faz.net/video/aarke-filterkaffee-system-einfach-praktisch-oder-schoen-teuer-f-a-z-200995017.html',
        'md5': '8a53426ea441494680719cfb75e7bb47',
        'info_dict': {
            'id': 'DFzezgdUR30',
            'ext': 'mp4',
            'title': 'Aarke Filterkaffee-System: Einfach praktisch oder schön teuer?',
            'description': 'md5:a03676d62a5864582d8e6f8d11b9f6b1',
            'duration': 617,
            'uploader': 'faz',
            'uploader_id': '@faz',
            'uploader_url': 'https://www.youtube.com/@faz',
            'channel': 'faz',
            'channel_id': 'UCcPcua2PF7hzik2TeOBx3uw',
            'channel_url': 'https://www.youtube.com/channel/UCcPcua2PF7hzik2TeOBx3uw',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1783076909,
            'upload_date': '20260703',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['News & Politics'],
            'tags': ['Kaffeemaschine'],
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
        },
        'add_ie': ['Youtube'],
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'n challenge solving failed',
        ],
    }, {
        'url': 'http://www.faz.net/multimedia/videos/stockholm-chemie-nobelpreis-fuer-drei-amerikanische-forscher-12610585.html',
        'skip': 'video gone',
        'info_dict': {
            'id': '12610585',
            'ext': 'mp4',
            'title': 'Stockholm: Chemie-Nobelpreis für drei amerikanische Forscher',
            'description': 'md5:1453fbf9a0d041d985a47306192ea253',
        },
    }, {
        'url': 'http://www.faz.net/aktuell/politik/berlin-gabriel-besteht-zerreissprobe-ueber-datenspeicherung-13659345.html',
        'only_matching': True,
    }, {
        'url': 'http://www.faz.net/berlin-gabriel-besteht-zerreissprobe-ueber-datenspeicherung-13659345.html',
        'only_matching': True,
    }, {
        'url': 'http://www.faz.net/-13659345.html',
        'only_matching': True,
    }, {
        'url': 'http://www.faz.net/aktuell/politik/-13659345.html',
        'only_matching': True,
    }, {
        'url': 'http://www.faz.net/foobarblafasel-13659345.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        youtube_id = self._search_regex(
            (r'"embedUrl"\s*:\s*"https?://(?:www\.)?youtube\.com/embed/(?P<id>[0-9A-Za-z_-]{11})',
             r'"embeddedYoutube"\s*,\s*"(?P<id>[0-9A-Za-z_-]{11})"'),
            webpage, 'youtube id', default=None, group='id')
        if youtube_id:
            return self.url_result(youtube_id, YoutubeIE, youtube_id)

        youtube_url = YoutubeIE._extract_url(webpage)
        if youtube_url:
            return self.url_result(youtube_url, YoutubeIE)

        description = self._og_search_description(webpage)
        media = self._html_search_regex(
            r"data-videojs-media='([^']+)",
            webpage, 'media')
        if media == 'extern':
            perform_url = self._search_regex(
                r"<iframe[^>]+?src='((?:http:)?//player\.performgroup\.com/eplayer/eplayer\.html#/?[0-9a-f]{26}\.[0-9a-z]{26})",
                webpage, 'perform url')
            return self.url_result(perform_url)
        config = compat_etree_fromstring(media)

        encodings = xpath_element(config, 'ENCODINGS', 'encodings', True)
        formats = []
        for pref, code in enumerate(['LOW', 'HIGH', 'HQ']):
            encoding = xpath_element(encodings, code)
            if encoding is not None:
                encoding_url = xpath_text(encoding, 'FILENAME')
                if encoding_url:
                    tbr = xpath_text(encoding, 'AVERAGEBITRATE', 1000)
                    if tbr:
                        tbr = int_or_none(tbr.replace(',', '.'))
                    f = {
                        'url': encoding_url,
                        'format_id': code.lower(),
                        'quality': pref,
                        'tbr': tbr,
                        'vcodec': xpath_text(encoding, 'CODEC'),
                    }
                    mobj = re.search(r'(\d+)x(\d+)_(\d+)\.mp4', encoding_url)
                    if mobj:
                        f.update({
                            'width': int(mobj.group(1)),
                            'height': int(mobj.group(2)),
                            'tbr': tbr or int(mobj.group(3)),
                        })
                    formats.append(f)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': description.strip() if description else None,
            'thumbnail': xpath_text(config, 'STILL/STILL_BIG'),
            'duration': int_or_none(xpath_text(config, 'DURATION')),
        }
