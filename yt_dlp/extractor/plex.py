import urllib.parse
import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_age_limit,
    unified_strdate,
    update_url_query,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PlexIE(InfoExtractor):
    IE_NAME = 'plex'
    IE_DESC = 'Plex Watch'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?watch\.plex\.tv/
        (?:[a-z]{2}(?:-[A-Z]{2})?/)?
        (?:watch/)?
        (?:
            movie/(?P<id>[\w-]+)
            |show/(?P<show>[\w-]+)/season/(?P<season>\d+)/episode/(?P<episode>\d+)
        )
    '''
    _TESTS = [{
        'url': 'https://watch.plex.tv/movie/nosferatu',
        'md5': 'cefda892d1efbaab86b54c803136e4a9',
        'info_dict': {
            'id': '5d7768278718ba001e311d5d',
            'ext': 'mp4',
            'display_id': 'nosferatu',
            'title': 'Nosferatu',
            'alt_title': 'Nosferatu, eine Symphonie des Grauens',
            'description': 'md5:34eb8b8605b0580ac7e795a5b5ca06c7',
            'thumbnail': r're:https?://metadata-static\.plex\.tv/.+',
            'duration': 5139,
            'release_year': 1922,
            'release_date': '19220518',
            'average_rating': float,
            'genres': ['Fantasy', 'Horror'],
            'cast': 'count:20',
            'creators': ['F. W. Murnau'],
        },
        # Native HLS --test only fetches the CMAF init segment (~1KB)
        'params': {'external_downloader': 'ffmpeg'},
    }, {
        'url': 'https://watch.plex.tv/de/movie/nosferatu',
        'only_matching': True,
    }, {
        'url': 'https://watch.plex.tv/watch/movie/nosferatu',
        'only_matching': True,
    }, {
        'url': 'https://watch.plex.tv/watch/movie/nosferatu?uri=provider://tv.plex.provider.vod/library/metadata/5d7768278718ba001e311d5d',
        'only_matching': True,
    }, {
        'url': 'https://watch.plex.tv/show/popeye-the-sailor-1960/season/1/episode/1',
        'only_matching': True,
    }, {
        'url': 'https://watch.plex.tv/movie/shoguns-ninja-2025',
        'only_matching': True,
    }]
    _TOKEN = None
    _CLIENT_ID = None
    _VOD_BASE = 'https://vod.provider.plex.tv'

    def _plex_headers(self, token=True):
        headers = {
            'Accept': 'application/json',
            'X-Plex-Client-Identifier': self._CLIENT_ID,
            'X-Plex-Product': 'Plex Mediaverse',
            'X-Plex-Provider-Version': '7.2.0',
        }
        if token and self._TOKEN:
            headers['X-Plex-Token'] = self._TOKEN
        return headers

    def _real_initialize(self):
        if self._TOKEN:
            return
        PlexIE._CLIENT_ID = str(uuid.uuid4())
        data = self._download_json(
            'https://plex.tv/api/v2/users/anonymous', None,
            'Logging in anonymously', data=b'', headers=self._plex_headers(token=False))
        token = traverse_obj(data, ('authToken', {str}))
        if not token:
            raise ExtractorError('Unable to obtain a Plex anonymous token', expected=True)
        PlexIE._TOKEN = token

    def _call_vod(self, path, video_id, **kwargs):
        return self._download_json(
            f'{self._VOD_BASE}{path}', video_id, headers=self._plex_headers(), **kwargs)

    def _metadata_id_from_url(self, url):
        uri = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('uri', [None])[0]
        if not uri:
            return None
        return self._search_regex(
            r'/library/metadata/([0-9a-f]+)', uri, 'metadata id', default=None)

    def _metadata_id_from_webpage(self, url, display_id):
        webpage = self._download_webpage(url, display_id)
        return (
            self._search_regex(
                r'provider://tv\.plex\.provider\.vod/library/metadata/([0-9a-f]+)',
                webpage, 'metadata id', default=None)
            or self._search_regex(
                r'plex://(?:movie|episode)/([0-9a-f]+)', webpage, 'metadata id'))

    def _extract_item(self, url, media_type, slug, display_id):
        metadata_id = self._metadata_id_from_url(url)
        if not metadata_id and media_type == 'movie':
            data = self._call_vod(
                f'/library/metadata/movie:{slug}', display_id, fatal=False)
            item = traverse_obj(data, ('MediaContainer', 'Metadata', 0, {dict}))
            if item:
                return item

        if not metadata_id:
            metadata_id = self._metadata_id_from_webpage(url, display_id)

        data = self._call_vod(f'/library/metadata/{metadata_id}', display_id)
        item = traverse_obj(data, ('MediaContainer', 'Metadata', 0, {dict}))
        if not item:
            raise ExtractorError('No Plex metadata found', expected=True)
        return item

    def _manifest_url(self, part_key):
        return update_url_query(urllib.parse.urljoin(self._VOD_BASE, part_key), {
            'X-Plex-Token': self._TOKEN,
            'includeAllStreams': '1',
        })

    def _merge_metadata_subtitles(self, part, subtitles):
        for stream in traverse_obj(part, ('Stream', lambda _, v: v.get('streamType') == 3)):
            stream_key = stream.get('key')
            if not stream_key:
                continue
            lang = stream.get('languageCode') or stream.get('id') or 'und'
            self._merge_subtitles({lang: [{
                'url': update_url_query(
                    urllib.parse.urljoin(self._VOD_BASE, stream_key),
                    {'X-Plex-Token': self._TOKEN}),
            }]}, target=subtitles)

    def _extract_formats_and_subtitles(self, item, video_id):
        formats, subtitles, had_drm, dash_media = [], {}, False, []
        for media in traverse_obj(item, ('Media', ..., {dict})):
            part = traverse_obj(media, ('Part', 0, {dict})) or {}
            if media.get('drm') or part.get('drm'):
                had_drm = True
                continue
            part_key = part.get('key')
            if not part_key:
                continue
            protocol = media.get('protocol')
            if protocol == 'hls' or part_key.endswith('.m3u8'):
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    self._manifest_url(part_key), video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                self._merge_metadata_subtitles(part, subtitles)
            elif protocol == 'dash' or part_key.endswith('.mpd'):
                dash_media.append((part_key, part))

        if not formats:
            for part_key, part in dash_media:
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    self._manifest_url(part_key), video_id, mpd_id='dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                self._merge_metadata_subtitles(part, subtitles)

        if not formats:
            if had_drm:
                self.report_drm(video_id)
            self.raise_no_formats('No playable streams', expected=True, video_id=video_id)
        return formats, subtitles

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        media_type = 'movie' if mobj.group('id') else 'show'
        slug = mobj.group('id') or mobj.group('show')
        season, episode = mobj.group('season', 'episode')
        display_id = slug if media_type == 'movie' else f'{slug}-s{season}e{episode}'

        item = self._extract_item(url, media_type, slug, display_id)
        video_id = traverse_obj(item, ('ratingKey', {str})) or display_id
        formats, subtitles = self._extract_formats_and_subtitles(item, video_id)

        info = {
            'id': video_id,
            'display_id': traverse_obj(item, ('slug', {str})) or display_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': int_or_none(item.get('duration'), scale=1000),
            'age_limit': parse_age_limit(item.get('contentRating')),
            **traverse_obj(item, {
                'title': ('title', {str}),
                'alt_title': ('originalTitle', {str}),
                'description': ('summary', {str}),
                'thumbnail': ('thumb', {url_or_none}),
                'release_year': ('year', {int_or_none}),
                'release_date': ('originallyAvailableAt', {unified_strdate}),
                'average_rating': ('audienceRating', {float_or_none}),
                'genres': ('Genre', ..., 'tag', {str}),
                'cast': ('Role', ..., 'tag', {str}),
                'creators': ('Director', ..., 'tag', {str}),
            }),
        }
        if item.get('type') == 'episode':
            info.update(traverse_obj(item, {
                'series': ('grandparentTitle', {str}),
                'season': ('parentTitle', {str}),
                'season_number': ('parentIndex', {int_or_none}),
                'episode': ('title', {str}),
                'episode_number': ('index', {int_or_none}),
            }))
        return info
