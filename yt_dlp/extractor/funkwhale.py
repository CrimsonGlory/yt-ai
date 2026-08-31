import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    int_or_none,
    mimetype2ext,
    parse_iso8601,
    str_or_none,
    unified_strdate,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj

_NETLOC_RE = r'(?:www\.)?(?P<host>funk\.firobe\.fr)'


class FunkwhaleBaseIE(InfoExtractor):
    _PAGE_SIZE = 50

    def _call_api(self, host, path, video_id, **kwargs):
        return self._download_json(f"https://{host}/api/v1/{path.lstrip('/')}", video_id, **kwargs)

    def _api_pages(self, host, path, video_id, query=None):
        query = dict(query or {})
        query.setdefault('page_size', self._PAGE_SIZE)
        page = 1
        while True:
            data = self._call_api(host, path, video_id, query={**query, 'page': page}, note=f'Downloading page {page}')
            results = traverse_obj(data, ('results', ..., {dict}))
            yield from results
            if not data.get('next') or not results:
                break
            page += 1

    def _cover_url(self, *objs):
        return traverse_obj(
            objs,
            (
                ...,
                ('cover', 'attachment_cover'),
                'urls',
                ('original', 'large_square_crop', 'medium_square_crop', 'source'),
                {url_or_none},
                any,
            ),
        )

    def _funkwhale_text(self, value):
        if isinstance(value, dict):
            return clean_html(value.get('html') or value.get('text'))
        return clean_html(value)

    def _track_url(self, host, track_id):
        return f'https://{host}/library/tracks/{track_id}'

    def _track_result(self, host, track):
        track_id = str_or_none(traverse_obj(track, ('id', {int_or_none})))
        if not track_id:
            return None
        return self.url_result(
            self._track_url(host, track_id), FunkwhaleIE, track_id, traverse_obj(track, ('title', {str})),
        )


class FunkwhaleIE(FunkwhaleBaseIE):
    IE_NAME = 'funkwhale'
    IE_DESC = 'Funkwhale'
    _VALID_URL = [
        rf'https?://{_NETLOC_RE}/library/tracks/(?P<id>\d+)',
        rf'https?://{_NETLOC_RE}/embed\.html\?(?:[^#]*&)?type=track(?:&[^#]*)?&id=(?P<id>\d+)',
        rf'https?://{_NETLOC_RE}/embed\.html\?(?:[^#]*&)?id=(?P<id>\d+)(?:&[^#]*)?&type=track',
    ]
    _TESTS = [
        {
            'url': 'https://funk.firobe.fr/library/tracks/168524',
            'md5': '067e9cdac9bc8cfe58f05fc4995ba5e1',
            'info_dict': {
                'id': '168524',
                'ext': 'mp3',
                'title': 'Do This Thing',
                'track': 'Do This Thing',
                'track_number': 27,
                'disc_number': 2,
                'album': 'Mean Girls',
                'album_artists': ['HITS Theatre'],
                'artists': ['HITS Theatre'],
                'uploader': 'hypnotized',
                'uploader_id': 'hypnotized@funk.firobe.fr',
                'duration': 310,
                'timestamp': 1786991902,
                'upload_date': '20260817',
                'release_date': '20260101',
                'thumbnail': 'https://funk.firobe.fr/media/attachments/f7/7f/ba/cover.png',
                'tags': ['Musical'],
                'vcodec': 'none',
            },
        },
        {
            'url': 'https://funk.firobe.fr/library/tracks/110004',
            'only_matching': True,
        },
        {
            'url': 'https://funk.firobe.fr/embed.html?type=track&id=110004',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        host, track_id = self._match_valid_url(url).group('host', 'id')
        track = self._call_api(host, f'tracks/{track_id}/', track_id)
        if track.get('is_playable') is False:
            raise ExtractorError('This track is not playable', expected=True)

        formats = []
        uploads = traverse_obj(track, ('uploads', ..., {dict})) or [{}]
        seen_urls = set()
        for upload in uploads:
            listen_url = url_or_none(
                urljoin(f'https://{host}/', traverse_obj(upload, ('listen_url', {str})) or track.get('listen_url')),
            )
            if not listen_url or listen_url in seen_urls:
                continue
            seen_urls.add(listen_url)
            ext = traverse_obj(upload, ('extension', {str})) or mimetype2ext(upload.get('mimetype'))
            formats.append(
                {
                    'url': listen_url,
                    'format_id': traverse_obj(upload, ('uuid', {str})) or 'http',
                    'ext': ext,
                    'vcodec': 'none',
                    'acodec': ext,
                    'filesize': traverse_obj(upload, ('size', {int_or_none})),
                    'tbr': float_or_none(upload.get('bitrate'), scale=1000),
                    'http_headers': {
                        'Referer': f'https://{host}/',
                        'Accept': 'audio/mpeg,audio/*,*/*;q=0.9',
                    },
                },
            )
        if not formats:
            raise ExtractorError('No playable audio was returned', expected=True)

        artist = traverse_obj(track, ('artist', {dict})) or {}
        album = traverse_obj(track, ('album', {dict})) or {}
        attributed = traverse_obj(track, ('attributed_to', {dict})) or {}
        channel_id = traverse_obj(artist, ('channel', 'actor', 'full_username', {str}))
        duration = traverse_obj(uploads, (..., 'duration', {int_or_none}, any))

        return {
            'id': str_or_none(track.get('id')) or track_id,
            'formats': formats,
            'duration': duration,
            'thumbnail': self._cover_url(track, album, artist),
            **traverse_obj(
                track,
                {
                    'title': ('title', {str}),
                    'track': ('title', {str}),
                    'description': ('description', {self._funkwhale_text}),
                    'timestamp': ('creation_date', {parse_iso8601}),
                    'track_number': ('position', {int_or_none}),
                    'disc_number': ('disc_number', {int_or_none}),
                    'license': ('license', {str}),
                    'tags': ('tags', ..., {str}, all, filter),
                },
            ),
            'album': traverse_obj(album, ('title', {str})),
            'album_artists': traverse_obj(album, ('artist', 'name', {str}, filter, all, filter)),
            'release_date': unified_strdate(album.get('release_date')),
            'artists': traverse_obj(artist, ('name', {str}, filter, all, filter)),
            'uploader': traverse_obj(attributed, (('name', 'preferred_username'), {str}, any)),
            'uploader_id': traverse_obj(attributed, ('full_username', {str})),
            'channel': traverse_obj(artist, ('name', {str})) if channel_id else None,
            'channel_id': channel_id,
            'channel_url': f'https://{host}/channels/{channel_id}' if channel_id else None,
            'vcodec': 'none',
        }


class FunkwhalePlaylistIE(FunkwhaleBaseIE):
    IE_NAME = 'funkwhale:playlist'
    _VALID_URL = rf'https?://{_NETLOC_RE}/library/playlists/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://funk.firobe.fr/library/playlists/31',
            'info_dict': {
                'id': '31',
                'title': 'Jazz',
            },
            'playlist_mincount': 16,
            'params': {'skip_download': True},
        },
        {
            'url': 'https://funk.firobe.fr/library/playlists/117',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        host, playlist_id = self._match_valid_url(url).group('host', 'id')
        playlist = self._call_api(host, f'playlists/{playlist_id}/', playlist_id)
        entries = []
        for item in self._api_pages(host, f'playlists/{playlist_id}/tracks/', playlist_id):
            entry = self._track_result(host, traverse_obj(item, ('track', {dict})) or item)
            if entry:
                entries.append(entry)
        return self.playlist_result(entries, playlist_id, traverse_obj(playlist, ('name', {str})))


class FunkwhaleAlbumIE(FunkwhaleBaseIE):
    IE_NAME = 'funkwhale:album'
    _VALID_URL = rf'https?://{_NETLOC_RE}/library/albums/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://funk.firobe.fr/library/albums/22892',
            'info_dict': {
                'id': '22892',
                'title': 'Mean Girls',
            },
            'playlist_mincount': 28,
            'params': {'skip_download': True},
        },
    ]

    def _real_extract(self, url):
        host, album_id = self._match_valid_url(url).group('host', 'id')
        album = self._call_api(host, f'albums/{album_id}/', album_id)
        entries = []
        for track in self._api_pages(host, 'tracks/', album_id, query={'album': album_id}):
            entry = self._track_result(host, track)
            if entry:
                entries.append(entry)
        return self.playlist_result(
            entries, album_id, traverse_obj(album, ('title', {str})), self._funkwhale_text(album.get('description')),
        )


class FunkwhaleChannelIE(FunkwhaleBaseIE):
    IE_NAME = 'funkwhale:channel'
    _VALID_URL = rf'https?://{_NETLOC_RE}/channels/(?P<id>[^/?#]+)'
    _TESTS = [
        {
            'url': 'https://funk.firobe.fr/channels/digitalmenteliberi@funkwhale.it',
            'info_dict': {
                'id': 'digitalmenteliberi@funkwhale.it',
                'title': 'Digitalmente Liberi',
                'description': 'md5:dff9f74c591a2f9b89acd1d9d9af22e5',
            },
            'playlist_mincount': 1,
            'params': {'skip_download': True},
        },
    ]

    def _real_extract(self, url):
        host, channel_id = self._match_valid_url(url).group('host', 'id')
        channel_id = urllib.parse.unquote(channel_id)
        channel = self._call_api(host, f'channels/{channel_id}/', channel_id)
        artist_id = traverse_obj(channel, ('artist', 'id', {int_or_none}, {str_or_none}))
        if not artist_id:
            raise ExtractorError('Unable to extract channel artist', expected=True)
        entries = []
        for track in self._api_pages(
            host,
            'tracks/',
            channel_id,
            query={
                'artist': artist_id,
                'include_channels': 'true',
            },
        ):
            entry = self._track_result(host, track)
            if entry:
                entries.append(entry)
        return self.playlist_result(
            entries,
            channel_id,
            traverse_obj(
                channel, ('actor', 'name', {str}), ('artist', 'name', {str}), ('actor', 'preferred_username', {str}),
            ),
            self._funkwhale_text(traverse_obj(channel, ('artist', 'description'))),
        )
