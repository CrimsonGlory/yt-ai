from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    remove_end,
    traverse_obj,
    url_basename,
)


class CinetecaMilanoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cinetecamilano\.it/(?:film/)?(?P<id>\d+|dona-il-tuo-5x1000-a-cineteca-milano|restauro-film)/?'
    _TESTS = [{
        'url': 'https://www.cinetecamilano.it/dona-il-tuo-5x1000-a-cineteca-milano/',
        'md5': '63a4e590e7a283272e4d3e8374ce861f',
        'info_dict': {
            'id': '5x1000',
            'ext': 'mp4',
            'title': 'Dona il tuo 5x1000 a Cineteca Milano',
            'description': 'Dona il tuo 5x1000 a Cineteca Milano e aiutaci a far scoprire tutto il bello del cinema alle nuove generazioni.',
            'thumbnail': r're:https?://.+\.jpe?g',
        },
    }, {
        'url': 'https://www.cinetecamilano.it/restauro-film/',
        'info_dict': {
            'id': 'restauro-film',
            'title': 'Restauro film',
            'description': 'md5:2bf15162f9d5b01671d976e117ea9196',
        },
        'playlist_mincount': 5,
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.cinetecamilano.it/film/1942',
        'skip': 'video gone',
        'info_dict': {
            'id': '1942',
            'ext': 'mp4',
            'title': 'Il draghetto Gris\u00f9 (4 episodi)',
            'release_date': '20220129',
            'thumbnail': r're:.+\.png',
            'description': 'md5:5328cbe080b93224712b6f17fcaf2c01',
            'modified_date': '20200520',
            'duration': 3139,
            'release_timestamp': 1643446208,
            'modified_timestamp': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        if not entries:
            raise ExtractorError('No video found', expected=True)

        for entry in entries:
            for fmt in entry.get('formats') or []:
                if fmt.get('url'):
                    fmt['url'] = fmt['url'].split('#')[0]
            if entry.get('url'):
                entry['url'] = entry['url'].split('#')[0]

        title = remove_end(
            self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage),
            ' | Cineteca Milano')
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        def clip_id_from_entry(entry, fallback):
            src = traverse_obj(entry, ('formats', 0, 'url'), 'url')
            if not src:
                return fallback
            name = url_basename(src.split('#')[0])
            return name.rsplit('.', 1)[0] or fallback

        if len(entries) == 1:
            info = entries[0]
            info.update({
                'id': clip_id_from_entry(info, video_id),
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
            })
            return info

        for i, entry in enumerate(entries, 1):
            clip_id = clip_id_from_entry(entry, f'{video_id}-{i}')
            entry.update({
                'id': clip_id,
                'title': clip_id.replace('_', ' '),
                'description': description,
            })
        return self.playlist_result(entries, video_id, title, description)
