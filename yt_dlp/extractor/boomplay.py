from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    qualities,
    str_or_none,
    url_or_none,
    urlencode_postdata,
    urljoin,
)
from ..utils.traversal import traverse_obj


class BoomplayIE(InfoExtractor):
    IE_NAME = 'boomplay'
    IE_DESC = 'Boomplay'
    _VALID_URL = r'https?://(?:www\.)?boomplay(?:music)?\.com/(?:songs|share/music)/(?P<id>\d+|EQ[\w-]+)'
    _CDN = 'https://source.boomplaymusic.com/'
    _TESTS = [{
        'url': 'https://www.boomplay.com/songs/165481965',
        'md5': '249e132eb1413ac36efadba947542f80',
        'info_dict': {
            'id': '165481965',
            'ext': 'mp3',
            'title': 'Rise of the Fallen Heroes',
            'display_id': '165481965',
            'track': 'Rise of the Fallen Heroes',
            'artists': ['fatbunny'],
            'album': 'Legendary Battle',
            'thumbnail': r're:https://source\.boomplaymusic\.com/.+',
            'duration': 125.0,
            'release_year': 2024,
            'genres': ['Metal'],
            'comment_count': int,
            'like_count': int,
            'view_count': int,
            'repost_count': int,
            'channel': 'fatbunny',
            'channel_id': '52723101',
            'channel_url': 'https://www.boomplay.com/artists/52723101',
            'vcodec': 'none',
        },
    }, {
        'url': 'https://www.boomplay.com/songs/EQuBwk1dTK63Me7ePEIn9rbu',
        'only_matching': True,
    }, {
        'url': 'https://www.boomplay.com/share/music/165481965',
        'only_matching': True,
    }, {
        'url': 'https://www.boomplaymusic.com/share/music/EQtajfxkvIe7osDdGYaZVmF3',
        'only_matching': True,
    }]

    def _cdn_url(self, path):
        if not path or not isinstance(path, str):
            return None
        if path.startswith('http'):
            return path
        return urljoin(self._CDN, path.lstrip('/'))

    def _resolve_numeric_id(self, display_id):
        if display_id.isdigit():
            return display_id
        webpage = self._download_webpage(
            f'https://www.boomplay.com/share/music/{display_id}', display_id,
            note='Resolving song ID')
        return self._search_regex(
            r'data-data="(\d+)(?:%40|@)', webpage, 'numeric song ID')

    def _real_extract(self, url):
        display_id = self._match_id(url)
        song_id = self._resolve_numeric_id(display_id)
        data = self._download_json(
            'https://www.boomplay.com/share/getEventData', song_id,
            data=urlencode_postdata({
                'itemID': song_id,
                'itemType': 'MUSIC',
                'actionType': 'P',
            }))
        event_str = traverse_obj(data, ('eventStr', {str}))
        if not event_str:
            raise ExtractorError(traverse_obj(data, ('desc', {str})) or 'Unable to fetch song metadata', expected=True)
        song = traverse_obj(self._parse_json(event_str, song_id), ('musicList', 0, {dict}))
        if not song:
            raise ExtractorError('No song data returned', expected=True)

        quality = qualities(('ld', 'md', 'hd'))
        formats = []
        for fmt_id in ('ld', 'md', 'hd'):
            media_url = self._cdn_url(song.get(f'{fmt_id}SourceID'))
            if not media_url:
                continue
            formats.append({
                'url': media_url,
                'format_id': fmt_id,
                'ext': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
                'quality': quality(fmt_id),
                'filesize': int_or_none(song.get(f'{fmt_id}Size')),
            })
        if not formats:
            self.raise_no_formats('No public audio formats found', expected=True, video_id=song_id)

        artist_id = traverse_obj(song, ('beArtist', 'colID', {str_or_none}))
        return {
            'id': str_or_none(song.get('musicID')) or song_id,
            'display_id': display_id,
            'formats': formats,
            'duration': parse_duration(song.get('deaution')),
            'release_year': int_or_none(song.get('publicYear')),
            'thumbnail': self._cdn_url(song.get('cover')),
            'channel_id': artist_id,
            'channel_url': url_or_none(f'https://www.boomplay.com/artists/{artist_id}' if artist_id else None),
            **traverse_obj(song, {
                'title': ('name', {str}),
                'track': ('name', {str}),
                'artists': ('beArtist', 'name', {str}, filter, all),
                'album': ('beAlbum', 'name', {str}),
                'genres': ('genre', {str}, filter, all),
                'channel': ('beArtist', 'name', {str}),
                'comment_count': ('commentCount', {int_or_none}),
                'like_count': ('collectCount', {int_or_none}),
                'view_count': ('streamCount', {int_or_none}),
                'repost_count': ('shareCount', {int_or_none}),
            }),
        }
