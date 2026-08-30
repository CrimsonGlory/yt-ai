import re

from .audiomack import AudiomackAlbumIE, AudiomackIE
from .audius import AudiusIE, AudiusTrackIE
from .bandcamp import BandcampAlbumIE, BandcampIE
from .common import InfoExtractor
from .soundcloud import SoundcloudIE
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    orderedSet,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class SonglinkIE(InfoExtractor):
    IE_NAME = 'song.link'
    IE_DESC = 'Songlink/Odesli'
    _VALID_URL = (
        r'https?://(?:www\.)?song\.link/'
        r'(?:(?P<country>[a-z]{2})/)?'
        r'(?P<kind>[a-z]{1,3})/(?P<id>[\w-]+)')
    _TESTS = [{
        'url': 'https://song.link/y/nov2mB552aI',
        'md5': '74705a2a496ed91944cd55da897c75fc',
        'info_dict': {
            'id': 'nov2mB552aI',
            'ext': 'mp4',
            'title': 'Rilès - ENERGY (Prod. Rilès)',
            'description': 'md5:33d4a2cab97cb787240c8fc253a33bfa',
            'duration': 188,
            'uploader': 'Rilès',
            'uploader_id': '@0Riles',
            'uploader_url': 'https://www.youtube.com/@0Riles',
            'channel': 'Rilès',
            'channel_id': 'UC-NwsBEyZqZnPc9OaCFJSsw',
            'channel_url': 'https://www.youtube.com/channel/UC-NwsBEyZqZnPc9OaCFJSsw',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1499620697,
            'upload_date': '20170709',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'categories': ['Music'],
            'tags': 'count:19',
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
            'heatmap': 'count:100',
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
        'url': 'https://song.link/s/1np8LVImKHn43mnpNOZDBJ',
        'only_matching': True,
    }, {
        'url': 'https://song.link/us/y/nov2mB552aI',
        'only_matching': True,
    }]
    _MEDIA_IES = (
        YoutubeIE,
        SoundcloudIE,
        AudiusIE,
        AudiusTrackIE,
        AudiomackIE,
        AudiomackAlbumIE,
        BandcampIE,
        BandcampAlbumIE,
    )
    _PLATFORM_ORDER = {
        'youtube': 0,
        'youtubeMusic': 1,
        'soundcloud': 2,
        'audius': 3,
        'audiomack': 4,
        'bandcamp': 5,
    }
    _YOUTUBE_ID_RE = r'(?:youtube\.com/watch\?v=|youtu\.be/)(?P<id>[\w-]{11})'

    def _link_media_url(self, link):
        media_url = url_or_none(link.get('url'))
        if media_url:
            return media_url
        unique_id = str_or_none(link.get('uniqueId')) or ''
        platform, _, rest = unique_id.partition('|')
        _, _, media_id = rest.rpartition('|')
        if platform in ('youtube', 'youtubeMusic') and media_id:
            return f'https://www.youtube.com/watch?v={media_id}'

    def _iter_links(self, page_data):
        for section in traverse_obj(page_data, ('sections', ..., {dict})) or []:
            section_id = section.get('sectionId') or ''
            if '|links|buy' in section_id:
                continue
            if 'embed|youtube' in section_id:
                yield {**section, 'platform': 'youtube'}
            yield from traverse_obj(section, ('links', ..., {dict}))

        entity = traverse_obj(page_data, ('entityData', {dict})) or {}
        if entity.get('provider') in ('youtube', 'youtubeMusic') and entity.get('id'):
            yield {
                'platform': entity['provider'],
                'uniqueId': f'youtube|song|{entity["id"]}',
            }

    def _candidate_urls(self, page_data, webpage):
        seen = set()
        candidates = []

        def add(platform, media_url):
            if platform not in self._PLATFORM_ORDER:
                return
            media_url = url_or_none(media_url)
            if not media_url or media_url in seen:
                return
            seen.add(media_url)
            candidates.append((self._PLATFORM_ORDER[platform], media_url))

        for link in self._iter_links(page_data):
            add(link.get('platform'), self._link_media_url(link))

        for yt_id in orderedSet(re.findall(self._YOUTUBE_ID_RE, webpage)):
            add('youtube', f'https://www.youtube.com/watch?v={yt_id}')

        candidates.sort(key=lambda item: item[0])
        for _, media_url in candidates:
            yield media_url

    def _suitable_ie_key(self, url):
        for ie in self._MEDIA_IES:
            if ie.suitable(url):
                return ie.ie_key()

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        page_data = traverse_obj(
            self._search_nextjs_data(webpage, display_id, default={}),
            ('props', 'pageProps', 'pageData', {dict})) or {}

        for media_url in self._candidate_urls(page_data, webpage):
            ie_key = self._suitable_ie_key(media_url)
            if ie_key:
                return self.url_result(media_url, ie_key)

        raise ExtractorError('No supported streaming links found', expected=True)
