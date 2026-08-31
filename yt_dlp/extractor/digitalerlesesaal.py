from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class DigitalerLesesaalIE(InfoExtractor):
    IE_NAME = 'digitalerlesesaal'
    IE_DESC = 'Digitaler Lesesaal des Bundesarchivs'
    _VALID_URL = [
        r'https?://digitaler-lesesaal\.bundesarchiv\.de/(?:(?P<lang>en|de)/)?(?:archive/)?video/(?P<id>\d+)(?:/(?P<copy_id>\d+))?',
        r'https?://digitaler-lesesaal\.bundesarchiv\.de/lixe/view/(?P<id>[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})',
    ]
    _API_BASE = 'https://digitaler-lesesaal.bundesarchiv.de/api/archive/video'
    _PLAYER_BASE = 'https://digitaler-lesesaal.bundesarchiv.de/lixe'
    _TESTS = [{
        'url': 'https://digitaler-lesesaal.bundesarchiv.de/en/video/7490/658446',
        'md5': '15a1d4db904191236cd67c733686db05',
        'info_dict': {
            'id': '9482ea42-6295-4e9c-8754-d690cb76ac32',
            'ext': 'mp4',
            'title': 'Die Stadt der Millionen (Originaltitel)',
            'display_id': '7490',
            'description': 'md5:82bfc7d776c3cbb36c5126faf91ab1a0',
            'duration': 4295,
            'thumbnail': 'https://digitaler-lesesaal.bundesarchiv.de/lixe/files/94/82/9482ea42-6295-4e9c-8754-d690cb76ac32/81959_1_1_Die_Stadt.jpg',
            'release_year': 1925,
            'creators': ['Adolf Trotz'],
            'genres': ['Trickart: Zeichentrick'],
            'categories': ['NichtSpielfilm', 'Kulturfilm', 'Animationsfilm'],
        },
    }, {
        'url': 'https://digitaler-lesesaal.bundesarchiv.de/video/7490/721308',
        'only_matching': True,
    }, {
        'url': 'https://digitaler-lesesaal.bundesarchiv.de/video/7490',
        'only_matching': True,
    }, {
        'url': 'https://digitaler-lesesaal.bundesarchiv.de/en/video/358/661603',
        'only_matching': True,
    }, {
        'url': 'https://digitaler-lesesaal.bundesarchiv.de/lixe/view/9482ea42-6295-4e9c-8754-d690cb76ac32',
        'only_matching': True,
    }]

    def _extract_lixe_player(self, uuid, video_id):
        player_url = f'{self._PLAYER_BASE}/view/{uuid}'
        webpage = self._download_webpage(
            player_url, video_id, note='Downloading liXe player page')
        player = self._search_json(r'var\s+data\s*=', webpage, 'liXe player data', video_id)
        path = traverse_obj(player, ('path', {str})) or f'{uuid[:2]}/{uuid[2:4]}/{uuid}'
        files_base = f'{self._PLAYER_BASE}/files/{path}/'
        item = traverse_obj(player, (
            'items', lambda _, v: v.get('m3u8') or v.get('type') == 'video', {dict}),
            get_all=False) or {}
        m3u8_url = url_or_none(urljoin(files_base, traverse_obj(item, ('m3u8', {str}))))
        if not m3u8_url:
            self.raise_no_formats(
                'No HLS stream in liXe player data', expected=True, video_id=video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', headers={'Referer': player_url})
        thumbnail = url_or_none(urljoin(files_base, traverse_obj(item, ('thumbnail', {str}))))
        return {
            'id': traverse_obj(player, ('uuid', {str})) or uuid,
            'formats': formats,
            'subtitles': subtitles,
            'title': traverse_obj(player, ('title', {str})),
            'thumbnail': thumbnail or f'{self._PLAYER_BASE}/thumbnail/{uuid}',
        }

    def _archive_metadata(self, doc):
        def field(*keys):
            for key in keys:
                value = traverse_obj(doc, (key, 0, {str}))
                if value:
                    return value

        return {
            'title': field('_str.title'),
            'description': field(
                'hit.teaser._str.filmwerk_texte',
                'hit.teaser._str.manifestation_kurzinhalt_inhaltsbeschreibung',
                '_str.manifestation_kurzinhalt_inhaltsbeschreibung'),
            'duration': parse_duration(field('_str.exemplar_laufzeit')),
            'release_year': int_or_none(field('_int.filmwerk_produktionsjahr_von')),
            'creators': traverse_obj(doc, ('_str.filmwerk_regie', ..., {str})),
            'genres': traverse_obj(doc, ('_str.filmwerk_genre', ..., {str})),
            'categories': traverse_obj(doc, ('_str.filmwerk_gattung', ..., {str})),
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        copy_id = mobj.groupdict().get('copy_id')
        lang = mobj.groupdict().get('lang') or 'de'

        if '-' in video_id:
            return self._extract_lixe_player(video_id, video_id)

        work = traverse_obj(self._download_json(
            f'{self._API_BASE}/video', video_id, query={'id': video_id, 'lang': lang}),
            ('documents', 0, {dict}))
        if not work:
            raise ExtractorError('Unable to extract archive video metadata', expected=True)

        copy_doc = None
        if copy_id:
            copies = self._download_json(
                f'{self._API_BASE}/copies', video_id,
                query={'id': video_id, 'lang': lang}, fatal=False)
            copy_doc = traverse_obj(copies, (
                'documents',
                lambda _, v: copy_id in (v.get('_int.exemplar_id') or []), {dict}),
                get_all=False)

        if copy_doc is not None:
            uuid = traverse_obj(copy_doc, ('_raw.exemplar_uuid', 0, {str}))
        else:
            uuid = traverse_obj(work, ('_raw.exemplar_uuid', 0, {str}))
        if not uuid:
            self.raise_no_formats(
                'No public viewing copy is available', expected=True, video_id=video_id)

        info = self._extract_lixe_player(uuid, video_id)
        info['display_id'] = video_id
        info.update({k: v for k, v in self._archive_metadata(copy_doc or work).items() if v})
        return info
