import itertools
import urllib.parse

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    extract_attributes,
    int_or_none,
    remove_start,
    str_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class RozhlasIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?prehravac\.rozhlas\.cz/audio/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://prehravac.rozhlas.cz/audio/3421320',
        'md5': '504c902dbc9e9a1fd50326eccf02a7e2',
        'info_dict': {
            'id': '3421320',
            'ext': 'mp3',
            'title': 'Echo Pavla Klusáka (30.06.2015 21:00)',
            'description': 'Osmdesátiny Terryho Rileyho jsou skvělou příležitostí proletět se elektronickými i akustickými díly zakladatatele minimalismu, který je aktivní už přes padesát let',
        },
        'skip': 'This audio is no longer available',
    }, {
        'url': 'http://prehravac.rozhlas.cz/audio/3421320/embed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(
            f'http://prehravac.rozhlas.cz/audio/{audio_id}', audio_id)

        title = self._html_search_regex(
            r'<h3>(.+?)</h3>\s*<p[^>]*>.*?</p>\s*<div[^>]+id=["\']player-track',
            webpage, 'title', default=None) or remove_start(
            self._og_search_title(webpage), 'Radio Wave - ')
        description = self._html_search_regex(
            r'<p[^>]+title=(["\'])(?P<url>(?:(?!\1).)+)\1[^>]*>.*?</p>\s*<div[^>]+id=["\']player-track',
            webpage, 'description', fatal=False, group='url')
        duration = int_or_none(self._search_regex(
            r'data-duration=["\'](\d+)', webpage, 'duration', default=None))

        return {
            'id': audio_id,
            'url': f'http://media.rozhlas.cz/_audio/{audio_id}.mp3',
            'title': title,
            'description': description,
            'duration': duration,
            'vcodec': 'none',
        }


class RozhlasBaseIE(InfoExtractor):
    def _extract_formats(self, entry, audio_id):
        formats = []
        for audio in traverse_obj(entry, ('audioLinks', lambda _, v: url_or_none(v['url']))):
            ext = audio.get('variant')
            for retry in self.RetryManager():
                if retry.attempt > 1:
                    self._sleep(1, audio_id)
                try:
                    if ext == 'dash':
                        formats.extend(self._extract_mpd_formats(
                            audio['url'], audio_id, mpd_id=ext))
                    elif ext == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            audio['url'], audio_id, 'm4a', m3u8_id=ext))
                    else:
                        formats.append({
                            'url': audio['url'],
                            'ext': ext,
                            'format_id': ext,
                            'abr': int_or_none(audio.get('bitrate')),
                            'acodec': ext,
                            'vcodec': 'none',
                        })
                except ExtractorError as e:
                    if isinstance(e.cause, HTTPError) and e.cause.status == 429:
                        retry.error = e.cause
                    else:
                        self.report_warning(e.msg)

        return formats


class RozhlasVltavaIE(RozhlasBaseIE):
    _VALID_URL = r'https?://(?:\w+\.rozhlas|english\.radio)\.cz/[\w-]+-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://wave.rozhlas.cz/papej-masicko-porcujeme-a-bilancujeme-filmy-a-serialy-ktere-letos-zabily-8891337',
        'md5': 'c80937b545274646dd6ca3326e73d58d',
        'info_dict': {
            'id': '10520988',
            'ext': 'mp3',
            'title': 'Papej masíčko! Porcujeme a bilancujeme filmy a seriály, které to letos zabily',
            'description': 'md5:1c6d29fb9564e1f17fc1bb83ae7da0bc',
            'duration': 1574,
            'artists': ['Aleš Stuchlý'],
            'channel_id': 'radio-wave',
        },
    }, {
        'url': 'https://wave.rozhlas.cz/poslechnete-si-neklid-podcastovy-thriller-o-vine-strachu-a-vztahu-ktery-zasel-8554744',
        'info_dict': {
            'id': '8554744',
            'title': 'Poslechněte si Neklid. Podcastový thriller o vině, strachu a vztahu, který zašel příliš daleko',
        },
        'playlist_count': 5,
        'playlist': [{
            'md5': '38983b7bde245d27325b9609c5b236b8',
            'info_dict': {
                'id': '9890713',
                'ext': 'mp3',
                'title': 'Neklid #1',
                'description': '1. díl: Neklid: 1. díl',
                'duration': 1025,
                'artists': ['Josef Kokta'],
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #1',
                'chapter_number': 1,
            },
        }, {
            'md5': '6f54eec774eec2644c7d80f525fd672d',
            'info_dict': {
                'id': '9890716',
                'ext': 'mp3',
                'title': 'Neklid #2',
                'description': '2. díl: Neklid: 2. díl',
                'duration': 768,
                'artists': ['Josef Kokta'],
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #2',
                'chapter_number': 2,
            },
        }, {
            'md5': '52e13c54e784d9a9858ae9c81053868e',
            'info_dict': {
                'id': '9890722',
                'ext': 'mp3',
                'title': 'Neklid #3',
                'description': '3. díl: Neklid: 3. díl',
                'duration': 607,
                'artists': ['Josef Kokta'],
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #3',
                'chapter_number': 3,
            },
        }, {
            'md5': '3401162b8b45629a63ec0b3718ea71b8',
            'info_dict': {
                'id': '9890728',
                'ext': 'mp3',
                'title': 'Neklid #4',
                'description': '4. díl: Neklid: 4. díl',
                'duration': 621,
                'artists': ['Josef Kokta'],
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #4',
                'chapter_number': 4,
            },
        }, {
            'md5': 'cdadb7db11b06a19bb834c046fc562b1',
            'info_dict': {
                'id': '9890734',
                'ext': 'mp3',
                'title': 'Neklid #5',
                'description': '5. díl: Neklid: 5. díl',
                'duration': 908,
                'artists': ['Josef Kokta'],
                'channel_id': 'radio-wave',
                'chapter': 'Neklid #5',
                'chapter_number': 5,
            },
        }],
    }, {
        'url': 'https://dvojka.rozhlas.cz/karel-siktanc-cerny-jezdec-bily-kun-napinava-pohadka-o-tajemnem-prizraku-8946969',
        'skip': 'No video formats found',
        'info_dict': {
            'id': '8946969',
            'title': 'Karel Šiktanc: Černý jezdec, bílý kůň. Napínavá pohádka o tajemném přízraku',
        },
        'playlist_count': 1,
        'playlist': [{
            'info_dict': {
                'id': '10631121',
                'ext': 'm4a',
                'title': 'Karel Šiktanc: Černý jezdec, bílý kůň. Napínavá pohádka o tajemném přízraku',
                'description': 'Karel Šiktanc: Černý jezdec, bílý kůň',
                'duration': 2656,
                'artists': ['Tvůrčí skupina Drama a literatura'],
                'channel_id': 'dvojka',
            },
        }],
        'params': {'skip_download': 'dash'},
    }]

    def _extract_video(self, entry):
        audio_id = entry['meta']['ga']['contentId']
        chapter_number = traverse_obj(entry, ('meta', 'ga', 'contentSerialPart', {int_or_none}))

        return {
            'id': audio_id,
            'chapter': traverse_obj(entry, ('meta', 'ga', 'contentNameShort')) if chapter_number else None,
            'chapter_number': chapter_number,
            'formats': self._extract_formats(entry, audio_id),
            **traverse_obj(entry, {
                'title': ('meta', 'ga', 'contentName'),
                'description': 'title',
                'duration': ('duration', {int_or_none}),
                'artist': ('meta', 'ga', 'contentAuthor'),
                'channel_id': ('meta', 'ga', 'contentCreator'),
            }),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # FIXME: Use get_element_text_and_html_by_tag when it accepts less strict html
        data = self._parse_json(extract_attributes(self._search_regex(
            r'(<div class="mujRozhlasPlayer" data-player=\'[^\']+\'>)',
            webpage, 'player'))['data-player'], video_id)['data']

        entries = [self._extract_video(entry) for entry in data['playlist']]
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, str_or_none(data.get('embedId')) or video_id,
            traverse_obj(data, ('series', 'title')))


class MujRozhlasIE(RozhlasBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mujrozhlas\.cz/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        # single episode extraction
        'url': 'https://www.mujrozhlas.cz/vykopavky/ach-jo-zase-teleci-rizek-je-mnohem-min-cesky-nez-jsme-si-mysleli',
        'md5': '6f8fd68663e64936623e67c152a669e0',
        'info_dict': {
            'id': '10787730',
            'ext': 'mp3',
            'title': 'Vykopávky: Ach jo, zase to telecí! Řízek je mnohem míň český, než jsme si mysleli',
            'description': 'md5:db7141e9caaedc9041ec7cefb9a62908',
            'timestamp': 1684915200,
            'modified_timestamp': 1763046746,
            'series': 'Chudáčci',
            'thumbnail': 'https://portal.rozhlas.cz/sites/default/files/images/ec630486d201fff8ce3b955f20070620.jpg',
            'channel_id': 'radio-wave',
            'upload_date': '20230524',
            'modified_date': '20251113',
        },
    }, {
        # serial extraction
        'url': 'https://www.mujrozhlas.cz/radiokniha/jaroslava-janackova-pribeh-tajemneho-psani-o-pramenech-genezi-babicky',
        'playlist_mincount': 7,
        'info_dict': {
            'id': 'bb2b5f4e-ffb4-35a6-a34a-046aa62d6f6b',
            'title': 'Jaroslava Janáčková: Příběh tajemného psaní. O pramenech a genezi Babičky',
            'description': 'md5:7434d8fac39ac9fee6df098e11dfb1be',
        },
        'params': {'skip_download': True},
    }, {
        # show extraction
        'url': 'https://www.mujrozhlas.cz/nespavci',
        'playlist_mincount': 14,
        'info_dict': {
            'id': '09db9b37-d0f4-368c-986a-d3439f741f08',
            'title': 'Nespavci',
            'description': 'md5:c430adcbf9e2b9eac88b745881e814dc',
        },
        'params': {'skip_download': True},
    }, {
        # serialPart
        'url': 'https://www.mujrozhlas.cz/povidka/gustavo-adolfo-becquer-hora-duchu',
        'skip': 'No audio formats',
        'info_dict': {
            'id': '8889035',
            'ext': 'm4a',
            'title': 'Gustavo Adolfo Bécquer: Hora duchů',
            'description': 'md5:343a15257b376c276e210b78e900ffea',
            'chapter': 'Hora duchů a Polibek – dva tajemné příběhy Gustava Adolfa Bécquera',
            'thumbnail': 'https://portal.rozhlas.cz/sites/default/files/images/2adfe1387fb140634be725c1ccf26214.jpg',
            'timestamp': 1708173000,
            'episode': 'Episode 1',
            'episode_number': 1,
            'series': 'Povídka',
            'modified_date': '20240217',
            'upload_date': '20240217',
            'modified_timestamp': 1708173198,
            'channel_id': 'vltava',
        },
        'params': {'skip_download': 'dash'},
    }]

    def _call_api(self, path, item_id, msg='API JSON'):
        return self._download_json(
            f'https://api.mujrozhlas.cz/{path}/{item_id}', item_id,
            note=f'Downloading {msg}', errnote=f'Failed to download {msg}')['data']

    def _extract_audio_entry(self, entry):
        audio_id = traverse_obj(entry, ('meta', 'ga', 'contentId'), 'id')

        return {
            'id': audio_id,
            'formats': self._extract_formats(entry['attributes'], audio_id),
            **traverse_obj(entry, {
                'title': ('attributes', 'title'),
                'description': ('attributes', 'description'),
                'episode_number': ('attributes', 'part'),
                'series': ('attributes', 'mirroredShow', 'title'),
                'chapter': ('attributes', 'mirroredSerial', 'title'),
                'artist': ('meta', 'ga', 'contentAuthor'),
                'channel_id': ('meta', 'ga', 'contentCreator'),
                'timestamp': ('attributes', 'since', {unified_timestamp}),
                'modified_timestamp': ('attributes', 'updated', {unified_timestamp}),
                'thumbnail': ('attributes', 'asset', 'url', {url_or_none}),
            }),
        }

    def _entries(self, api_url, playlist_id):
        for page in itertools.count(1):
            episodes = self._download_json(
                api_url, playlist_id, note=f'Downloading episodes page {page}',
                errnote=f'Failed to download episodes page {page}', fatal=False)
            for episode in traverse_obj(episodes, ('data', lambda _, v: v['meta']['ga']['contentId'])):
                yield self._extract_audio_entry(episode)
            api_url = traverse_obj(episodes, ('links', 'next', {url_or_none}))
            if not api_url:
                break

    def _resolve_entity(self, url, display_id):
        # HTML pages are behind a Cloudflare JS challenge; the public search API
        # still resolves episode/show/serial slugs without that page.
        results = traverse_obj(
            self._download_json(
                'https://api.mujrozhlas.cz/search', display_id,
                query={'query': display_id, 'page[limit]': 30},
                note='Resolving slug via search API',
                errnote='Failed to resolve slug via search API'),
            ('data', lambda _, v: v['type'] and v['id']))
        if not results:
            raise ExtractorError(
                f'Unable to resolve mujRozhlas slug "{display_id}"', expected=True)
        if len(results) == 1:
            return results[0]['type'], results[0]['id']

        path_depth = len([p for p in urllib.parse.urlparse(url).path.split('/') if p])
        preferred_types = (
            ('show', 'serial') if path_depth == 1
            else ('episode', 'serialPart', 'serial', 'show'))
        for etype in preferred_types:
            match = next((entry for entry in results if entry['type'] == etype), None)
            if match:
                return etype, match['id']
        return results[0]['type'], results[0]['id']

    def _real_extract(self, url):
        display_id = self._match_id(url)
        entity, item_id = self._resolve_entity(url, display_id)

        if entity in ('episode', 'serialPart'):
            return self._extract_audio_entry(self._call_api(
                'episodes', item_id, 'episode info API JSON'))

        elif entity in ('show', 'serial'):
            data = self._call_api(f'{entity}s', item_id, f'{entity} playlist JSON')
            api_url = data['relationships']['episodes']['links']['related']
            return self.playlist_result(
                self._entries(api_url, item_id), item_id,
                **traverse_obj(data, ('attributes', {
                    'title': 'title',
                    'description': 'description',
                })))

        else:
            # `entity == 'person'` not implemented yet by API, ref:
            # https://api.mujrozhlas.cz/persons/8367e456-2a57-379a-91bb-e699619bea49/participation
            raise ExtractorError(f'Unsupported entity type "{entity}"')
