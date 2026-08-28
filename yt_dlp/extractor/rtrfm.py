from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
    parse_qs,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import find_element, traverse_obj


class RTRFMIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtrfm\.com\.au/(?:shows|show-episode)/(?P<id>[^/?#&]+)'
    _TESTS = [
        {
            'url': 'https://rtrfm.com.au/shows/breakfast/?date=2026-08-21',
            'md5': '2fcabd7eceb2309dd94344c6774c8e26',
            'info_dict': {
                'id': 'breakfast-2026-08-21',
                'ext': 'mp3',
                'series': 'Breakfast with Pam',
                'title': 'Breakfast with Pam 2026-08-21',
                'description': 'md5:82e0c923f8dddf279c471b73fd964cb1',
                'release_date': '20260821',
                'duration': 10800,
            },
        },
        {
            'url': 'https://rtrfm.com.au/shows/breakfast/',
            'only_matching': True,
        },
        {
            'url': 'https://rtrfm.com.au/show-episode/breakfast-2021-11-11/',
            'skip': 'video gone',
            'md5': '396bedf1e40f96c62b30d4999202a790',
            'info_dict': {
                'id': 'breakfast-2021-11-11',
                'ext': 'mp3',
                'series': 'Breakfast with Taylah',
                'title': 'Breakfast with Taylah 2021-11-11',
                'description': 'md5:0979c3ab1febfbec3f1ccb743633c611',
            },
        },
        {
            'url': 'https://rtrfm.com.au/show-episode/breakfast-2020-06-01/',
            'md5': '594027f513ec36a24b15d65007a24dff',
            'info_dict': {
                'id': 'breakfast-2020-06-01',
                'ext': 'mp3',
                'series': 'Breakfast with Taylah',
                'title': 'Breakfast with Taylah 2020-06-01',
                'description': r're:^Breakfast with Taylah ',
            },
            'skip': 'This audio has expired',
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        restream = extract_attributes(
            traverse_obj(webpage, ({find_element(attr='x-data', value='restream', html=True)},)) or '',
        )
        show = restream.get('data-slug')
        date = traverse_obj(parse_qs(url), ('date', 0)) or restream.get('data-date')
        title = restream.get('data-name')
        if not all((show, date, title)):
            show, date, title = self._search_regex(
                r'''\.playShow(?:From)?\(['"](?P<show>[^'"]+)['"],\s*['"](?P<date>\d{4}-\d{2}-\d{2})['"],\s*['"](?P<title>[^'"]+)['"]''',
                webpage,
                'details',
                group=('show', 'date', 'title'),
            )

        audio_url = url_or_none(
            traverse_obj(
                self._download_json(
                    'https://restreams.rtrfm.com.au/rzz', show, 'Downloading MP3 URL', query={'n': show, 'd': date},
                ),
                'u',
            ),
        )
        # This is the only indicator of an error until trying to download the URL and
        # downloads of mp4 URLs always fail (403 for current episodes, 404 for missing).
        if not audio_url or '.mp4' in audio_url:
            self.raise_no_formats('Expired or no episode on this date', expected=True)

        return {
            'id': f'{show}-{date}',
            'title': f'{title} {date}',
            'series': title,
            'url': audio_url,
            'ext': 'mp3',
            'vcodec': 'none',
            'duration': int_or_none(restream.get('data-duration')),
            'release_date': unified_strdate(date),
            'description': self._og_search_description(webpage),
        }
