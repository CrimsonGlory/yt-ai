import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    orderedSet,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PalestineFilmInstituteIE(InfoExtractor):
    IE_NAME = 'palestinefilminstitute'
    IE_DESC = 'Palestine Film Institute'
    _VALID_URL = (
        r'https?://cdn\.palestinefilminstitute\.org/'
        r'(?:watch/(?P<id>[0-9a-fA-F]{32})/?|share/hls\.m3u8\?(?:[^#]*&)?token=(?P<hls_id>[0-9a-fA-F]{32}))')
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>(?:https?:)?//cdn\.palestinefilminstitute\.org/watch/[0-9a-fA-F]{32})']
    _TESTS = [{
        'url': 'https://cdn.palestinefilminstitute.org/watch/9aea2aeddc86407ba3dfeee0f7e60351',
        'md5': '8ac409684d282259ddd4d64010f011b7',
        'info_dict': {
            'id': '9aea2aeddc86407ba3dfeee0f7e60351',
            'ext': 'mp4',
            'title': '9aea2aeddc86407ba3dfeee0f7e60351',
            'thumbnail': r're:https://cdn2\.palestinefilminstitute\.org/share/poster\.jpg\?token=9aea2aeddc86407ba3dfeee0f7e60351',
        },
    }, {
        'url': 'https://cdn.palestinefilminstitute.org/watch/8a53509aefaf4b34a0f82b15463390cd/',
        'info_dict': {
            'id': '8a53509aefaf4b34a0f82b15463390cd',
            'ext': 'mp4',
            'title': '8a53509aefaf4b34a0f82b15463390cd',
            'thumbnail': r're:https://cdn2\.palestinefilminstitute\.org/share/poster\.jpg\?token=8a53509aefaf4b34a0f82b15463390cd',
        },
        'params': {'skip_download': 'm3u8'},
    }, {
        'url': 'https://cdn.palestinefilminstitute.org/share/hls.m3u8?token=9aea2aeddc86407ba3dfeee0f7e60351',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = (mobj.group('id') or mobj.group('hls_id')).lower()
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'https://cdn.palestinefilminstitute.org/share/hls.m3u8?token={video_id}',
            video_id, 'mp4', m3u8_id='hls')

        meta = self._download_json(
            f'https://cdn.palestinefilminstitute.org/share/meta.json?token={video_id}',
            video_id, 'Downloading video metadata', fatal=False)

        extra_subs = {}
        for lang, sub_url in (traverse_obj(meta, ('subs', {dict})) or {}).items():
            if url_or_none(sub_url):
                extra_subs.setdefault(lang, []).append({'url': sub_url})
        self._merge_subtitles(extra_subs, target=subtitles)

        return {
            'id': video_id,
            'title': video_id,
            'thumbnail': traverse_obj(meta, ('poster', {url_or_none})),
            'formats': formats,
            'subtitles': subtitles,
        }


class PalestineFilmInstitutePageIE(InfoExtractor):
    IE_NAME = 'palestinefilminstitute:page'
    IE_DESC = 'Palestine Film Institute pages'
    _VALID_URL = (
        r'https?://(?:www\.)?palestinefilminstitute\.org/'
        r'(?:[a-z]{2}/)?(?P<id>pfp|palestine-film-platform)/?(?:[?#].*)?$')
    _TESTS = [{
        'url': 'https://www.palestinefilminstitute.org/en/pfp',
        'playlist_mincount': 1,
        'info_dict': {
            'id': 'pfp',
            'title': str,
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.palestinefilminstitute.org/en/palestine-film-platform',
        'only_matching': True,
    }, {
        'url': 'https://www.palestinefilminstitute.org/ar/pfp',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_ids = orderedSet(re.findall(
            r'cdn\.palestinefilminstitute\.org/watch/([0-9a-fA-F]{32})', webpage))
        if not video_ids:
            raise ExtractorError('No Palestine Film Institute player embed found', expected=True)

        title = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage)
        entries = [
            self.url_result(
                f'https://cdn.palestinefilminstitute.org/watch/{video_id}',
                PalestineFilmInstituteIE, video_id)
            for video_id in video_ids]
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, display_id, title)
