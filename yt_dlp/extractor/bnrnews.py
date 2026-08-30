from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    strip_or_none,
    traverse_obj,
)


class BNRNewsIE(InfoExtractor):
    IE_NAME = 'bnrnews'
    IE_DESC = 'BNR News (Bulgarian National Radio)'
    _VALID_URL = r'https?://(?:www\.)?bnrnews\.bg/(?P<program>[^/?#]+)/post/(?P<id>\d+)(?:/[^/?#]+)?'
    _TESTS = [{
        'url': 'https://bnrnews.bg/de/post/394279/bulgarien-heute-2-dezember-2025',
        'md5': 'eb5a9d9b47347e703c37270124a14169',
        'info_dict': {
            'id': '394279',
            'ext': 'mp3',
            'title': 'Bulgarien heute – 2. Dezember 2025',
            'description': 'md5:c89918d43328d3bb5abea0435228f74e',
            'thumbnail': 'https://bnrnews.bg/api/media/5168339e-0b81-4d38-9a00-039ef0860035?Size=large',
            'timestamp': 1764694820,
            'upload_date': '20251202',
            'uploader': 'Radio Bulgarien auf Deutsch',
            'uploader_id': 'de',
            'series': 'Sendung auf Deutsch',
            'creators': ['Марта Рос'],
            'tags': ['Ausschreitungen', 'lied des tages', 'Haushaltsentwurf 2026',
                     'Bulgarien heute', 'Massenproteste im ganzen Land'],
            'view_count': int,
            'vcodec': 'none',
        },
    }, {
        'url': 'https://bnrnews.bg/horizont/post/395494/100-godini-ot-rozhdenieto-na-georgi-partsalev',
        'info_dict': {
            'id': '395494',
            'title': '100 години от рождението на Георги Парцалев',
            'description': 'md5:5d91d452be8ce30e5b83d9a503c27340',
            'thumbnail': 'https://bnrnews.bg/api/media/ff6874b7-6085-4bb6-8152-039d79faf833?Size=large',
            'timestamp': 1765004410,
            'upload_date': '20251206',
            'uploader': 'Програма Хоризонт',
            'uploader_id': 'horizont',
            'creators': ['Гергана Хрисчева'],
            'tags': ['Георги Парцалев', 'Калин Сърменов',
                     '100 години от рождението на Працалев', 'фондация Лили Иванова'],
            'view_count': int,
        },
        'playlist_count': 2,
    }, {
        'url': 'https://bnrnews.bg/de/post/520566/bulgarien-heute-28-august-2026',
        'only_matching': True,
    }]

    def _media_entry(self, media, media_kind):
        media_id = traverse_obj(media, ('Id', {str}))
        if not media_id:
            return None
        filename = traverse_obj(media, ('FileName', {str}))
        ext = determine_ext(filename, 'mp3' if media_kind == 'audio' else 'mp4')
        if ext == 'unknown_video':
            ext = 'mp3' if media_kind == 'audio' else 'mp4'
        return {
            'id': media_id,
            'url': f'https://bnrnews.bg/api/media/{media_id}',
            'ext': ext,
            'title': traverse_obj(media, ('Description', {strip_or_none})),
            'vcodec': 'none' if media_kind == 'audio' else None,
        }

    def _real_extract(self, url):
        program, video_id = self._match_valid_url(url).group('program', 'id')
        data = self._download_json(
            f'https://bnrnews.bg/api/materials/{program}/{video_id}',
            video_id, fatal=False)
        if not traverse_obj(data, 'Id'):
            webpage = self._download_webpage(url, video_id)
            data = traverse_obj(
                self._search_nextjs_data(webpage, video_id),
                ('props', 'pageProps', 'data', {dict}))
        if not traverse_obj(data, 'Id'):
            raise ExtractorError('Unable to extract post data', expected=True)

        common = traverse_obj(data, {
            'title': ('Title', {str}),
            'thumbnail': ('MainImageInstance', 'Id', {
                lambda x: f'https://bnrnews.bg/api/media/{x}?Size=large' if x else None}),
            'timestamp': ('VisibleDate', {parse_iso8601}),
            'uploader': ('ProgramOwner', 'Name', {str}),
            'uploader_id': ('ProgramOwner', 'UrlName', {str}),
            'series': ('Broadcast', 'Title', {strip_or_none}),
            'creators': ('Workers', ..., {str}),
            'tags': ('Tags', ..., 'Name', {str}),
            'view_count': ('ViewsCount', {int_or_none}),
        })
        common['description'] = join_nonempty(*traverse_obj(data, (
            'Sections', lambda _, v: v['SectionType'] == 'Text',
            'Description', {clean_html})) or (), delim='\n\n') or None

        entries, seen = [], set()

        def add_media(media, media_kind):
            entry = self._media_entry(media, media_kind)
            if not entry or entry['id'] in seen:
                return
            seen.add(entry['id'])
            entries.append(entry)

        for key, kind in (('Audio', 'audio'), ('Video', 'video'), ('TextToSpeech', 'audio')):
            add_media(traverse_obj(data, (key, {dict})), kind)
        for section in traverse_obj(data, ('Sections', ..., {dict})) or []:
            add_media(traverse_obj(section, ('Audio', {dict})), 'audio')
            add_media(traverse_obj(section, ('Video', {dict})), 'video')

        if not entries:
            self.raise_no_formats('No audio or video found', expected=True, video_id=video_id)
            return {'id': video_id, **common}

        post_title = common.get('title')
        for entry in entries:
            entry['title'] = entry.get('title') or post_title

        if len(entries) == 1:
            return {
                **common,
                **entries[0],
                'id': video_id,
                'title': entries[0].get('title') or post_title,
            }
        return self.playlist_result(entries, video_id, **common)
