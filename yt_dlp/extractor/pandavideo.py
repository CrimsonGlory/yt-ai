from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_qs,
)
from ..utils.traversal import traverse_obj


class PandaVideoIE(InfoExtractor):
    IE_DESC = 'Panda Video'
    _UUID_RE = r'[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12}'
    _LIBRARY_RE = r'vz-[a-z0-9]{8}-[a-z0-9]{3}'
    _VALID_URL = (
        rf'https?://(?:(?:[\w-]*?(?P<library>{_LIBRARY_RE}))\.tv\.pandavideo\.com\.br|'
        rf'player\.pandavideo\.com\.br)/embed/?\?(?:[^#"\']*&)?v=(?P<id>{_UUID_RE})')
    _EMBED_REGEX = [rf'<iframe[^>]+\bsrc=["\'](?P<url>{_VALID_URL})']
    _TESTS = [{
        'url': 'https://player-vz-ded14ebd-85a.tv.pandavideo.com.br/embed/?v=3b101f05-84aa-4de0-9b64-71f1855388af',
        'md5': 'd749f9fb362c7afebaea8bc924a3894a',
        'info_dict': {
            'id': '3b101f05-84aa-4de0-9b64-71f1855388af',
            'ext': 'mp4',
            'title': '3b101f05-84aa-4de0-9b64-71f1855388af',
            'thumbnail': 'https://cdn.pandavideo.com/vz-ded14ebd-85a/3b101f05-84aa-4de0-9b64-71f1855388af/thumbnail.jpg',
        },
    }, {
        'url': 'https://player.pandavideo.com.br/embed/?v=3b101f05-84aa-4de0-9b64-71f1855388af&l=vz-ded14ebd-85a',
        'only_matching': True,
    }, {
        'url': 'https://player-vz-ded14ebd-85a.tv.pandavideo.com.br/embed/?v=79cb9b0e-a64b-4485-8a44-47f36b292e4c&autoplay=true',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id, library_id = mobj.group('id', 'library')
        library_id = library_id or traverse_obj(parse_qs(url), ('l', -1))
        if not library_id:
            raise ExtractorError('Unable to determine Panda Video library id', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'https://b-{library_id}.tv.pandavideo.com.br/{video_id}/playlist.m3u8',
            video_id, 'mp4', m3u8_id='hls')

        return {
            'id': video_id,
            'title': video_id,
            'thumbnail': f'https://cdn.pandavideo.com/{library_id}/{video_id}/thumbnail.jpg',
            'formats': formats,
            'subtitles': subtitles,
        }
