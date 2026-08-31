from .common import InfoExtractor
from ..networking import HEADRequest
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    url_or_none,
    xpath_text,
)


class TreffDarcIE(InfoExtractor):
    IE_NAME = 'treffdarc'
    IE_DESC = 'TREFF.DARC.DE'
    _VALID_URL = r'https?://(?:[\w-]+\.)?treff\.darc\.de/(?:playback/)?presentation/(?:2\.\d+/)?(?P<id>[0-9a-f]{40}-\d+)'
    _TESTS = [{
        'url': 'https://treff.darc.de/playback/presentation/2.3/87e34c7a1b375e3c8cc94e9d0ae2ac54d41af2de-1756309263581',
        'md5': '6f86a1da4168ee02a71ef32b7ac79708',
        'info_dict': {
            'id': '87e34c7a1b375e3c8cc94e9d0ae2ac54d41af2de-1756309263581',
            'ext': 'webm',
            'title': 'HAMgroup LoRaWan - Low Power Wide Area Network (Referent: Dipl.-Ing. (FH) Jürgen Mayer, DL8MA)',
            'duration': 4670.012,
            'timestamp': 1756309263,
            'upload_date': '20250827',
            'thumbnail': r're:https://treff\.darc\.de/presentation/.+/thumbnails/thumb-\d+\.png',
        },
    }, {
        'url': 'https://treff.darc.de/playback/presentation/2.3/f2ece695693093a21a64cccaf471eda670b27eb1-1729945679988',
        'only_matching': True,
    }, {
        'url': 'https://treff.darc.de/presentation/87e34c7a1b375e3c8cc94e9d0ae2ac54d41af2de-1756309263581/video/webcams.webm',
        'only_matching': True,
    }]
    _MEDIA_HOST = 'treff.darc.de'

    def _public_url(self, media_url):
        media_url = self._proto_relative_url(media_url)
        _, sep, rest = media_url.partition('/presentation/')
        if not sep:
            return media_url
        return f'https://{self._MEDIA_HOST}/presentation/{rest}'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media_root = f'https://{self._MEDIA_HOST}/presentation/{video_id}'
        metadata = self._download_xml(
            f'{media_root}/metadata.xml', video_id,
            note='Downloading recording metadata')

        meeting = metadata.find('meeting')
        title = (
            (meeting.get('name') if meeting is not None else None)
            or xpath_text(metadata, './meta/meetingName')
            or video_id)

        formats = []
        for path, format_id, format_note, extra in (
            ('video/webcams.webm', 'webcam-webm', 'webcam/audio', {'preference': 1}),
            ('video/webcams.mp4', 'webcam-mp4', 'webcam/audio', {'preference': 1}),
            ('deskshare/deskshare.webm', 'deskshare-webm', 'screenshare', {
                'acodec': 'none',
                'preference': -10,
            }),
            ('deskshare/deskshare.mp4', 'deskshare-mp4', 'screenshare', {
                'acodec': 'none',
                'preference': -10,
            }),
            ('audio/audio.webm', 'audio-webm', 'audio', {
                'vcodec': 'none',
                'preference': -5,
            }),
        ):
            media_url = f'{media_root}/{path}'
            if self._request_webpage(
                    HEADRequest(media_url), video_id,
                    note=f'Checking {format_id}', errnote=False, fatal=False) is False:
                continue
            fmt = {
                'url': media_url,
                'format_id': format_id,
                'format_note': format_note,
                'ext': path.rsplit('.', 1)[-1],
            }
            fmt.update(extra)
            formats.append(fmt)

        if not formats:
            raise ExtractorError('No media found for this recording', expected=True)

        thumbnail = xpath_text(metadata, './/preview/images/image')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': float_or_none(xpath_text(metadata, './playback/duration'), scale=1000),
            'timestamp': int_or_none(xpath_text(metadata, './start_time'), scale=1000),
            'thumbnail': url_or_none(self._public_url(thumbnail) if thumbnail else None),
        }
