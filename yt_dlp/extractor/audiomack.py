import base64
import hashlib
import hmac
import time
import urllib.parse
import uuid

from .common import InfoExtractor
from .soundcloud import SoundcloudIE
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AudiomackBaseIE(InfoExtractor):
    _API_BASE = 'https://api.audiomack.com/v1'
    _API_CONSUMER_KEY = 'audiomack-web'
    _API_CONSUMER_SECRET = 'bd8a07e9f23fbe9d808646b730f89b8e'

    def _match_artist_slug(self, url):
        groups = self._match_valid_url(url).groupdict()
        return groups.get('artist') or groups['artist2'], groups['id']

    @staticmethod
    def _oauth_percent_encode(value):
        return urllib.parse.quote(str(value), safe='~')

    def _oauth_sign_url(self, url, query=None):
        parsed = urllib.parse.urlparse(url)
        base_url = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'
        params = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        if query:
            params.update({k: v for k, v in query.items() if v is not None})
        params.update(
            {
                'oauth_consumer_key': self._API_CONSUMER_KEY,
                'oauth_nonce': uuid.uuid4().hex,
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(time.time())),
                'oauth_version': '1.0',
            },
        )
        encode = self._oauth_percent_encode
        normalized = '&'.join(f'{encode(k)}={encode(params[k])}' for k in sorted(params))
        base_string = '&'.join((encode('GET'), encode(base_url), encode(normalized)))
        key = f'{encode(self._API_CONSUMER_SECRET)}&'
        params['oauth_signature'] = base64.b64encode(
            hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest(),
        ).decode()
        return f'{base_url}?{urllib.parse.urlencode(params)}'

    def _call_api(self, path, display_id, query=None, note='Downloading JSON metadata'):
        data = self._download_json(self._oauth_sign_url(f'{self._API_BASE}/{path}', query), display_id, note=note)
        if traverse_obj(data, 'errorcode'):
            raise ExtractorError(traverse_obj(data, 'message', default='Audiomack API error'), expected=True)
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        if not data:
            raise ExtractorError('Empty Audiomack API response', expected=True)
        return data

    def _extract_stream_url(self, music_id, display_id):
        stream_url = traverse_obj(
            self._call_api(f'music/play/{music_id}', display_id, note='Downloading playback URL'),
            ('signedUrl', {url_or_none}),
        )
        if not stream_url:
            raise ExtractorError('Unable to extract streaming URL', expected=True)
        return stream_url

    def _parse_music(self, music, stream_url):
        return {
            'url': stream_url,
            'vcodec': 'none',
            **traverse_obj(
                music,
                {
                    'id': ('id', {str_or_none}),
                    'title': ('title', {str}),
                    'artist': ('artist', {str}),
                    'uploader': ('uploader', 'name', {str}),
                    'uploader_id': ('uploader', 'url_slug', {str}),
                    'uploader_url': ('uploader', 'url_slug', {lambda x: f'https://audiomack.com/{x}'}),
                    'description': ('description', {clean_html}, filter),
                    'thumbnail': ('image', {url_or_none}),
                    'duration': ('duration', {int_or_none}),
                    'timestamp': ('uploaded', {int_or_none}),
                    'release_timestamp': ('released', {int_or_none}),
                    'genre': ('genre', {str}, filter),
                    'view_count': ('stats', 'plays-raw', {int_or_none}),
                    'like_count': ('stats', 'favorites-raw', {int_or_none}),
                    'repost_count': ('stats', 'reposts-raw', {int_or_none}),
                    'comment_count': ('stats', 'comments', {int_or_none}),
                    'tags': ('usertags', {lambda x: x.split(',') if x else None}),
                },
            ),
        }


class AudiomackIE(AudiomackBaseIE):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/(?:embed/)?(?:song/(?P<artist>[\w-]+)|(?P<artist2>[\w-]+)/song)/(?P<id>[\w-]+)'
    IE_NAME = 'audiomack'
    _TESTS = [
        {
            'url': 'https://audiomack.com/djlandlord/song/seyi-vibes-mix-2026-mixtape',
            'md5': 'ecd3ab1ccd0c788f638f928f1c085361',
            'info_dict': {
                'id': '99574259',
                'ext': 'm4a',
                'title': 'BEST OF SEYI VIBEZ 2026 MIXTAPE',
                'artist': 'Dj Landlord',
                'artists': ['Dj Landlord'],
                'uploader': 'Dj Landlord',
                'uploader_id': 'djlandlord',
                'uploader_url': 'https://audiomack.com/djlandlord',
                'thumbnail': r're:https?://i\.audiomack\.com/djlandlord/.+',
                'duration': 4291,
                'timestamp': 1782933562,
                'upload_date': '20260701',
                'release_timestamp': 1782933557,
                'release_date': '20260701',
                'genre': 'dj-mix',
                'genres': ['dj-mix'],
                'view_count': int,
                'like_count': int,
                'repost_count': int,
                'comment_count': int,
                'tags': list,
                'vcodec': 'none',
            },
        },
        {
            # hosted on audiomack
            'url': 'http://www.audiomack.com/song/roosh-williams/extraordinary',
            'skip': 'video gone',
            'info_dict': {
                'id': '310086',
                'ext': 'mp3',
                'uploader': 'Roosh Williams',
                'title': 'Extraordinary',
            },
        },
        {
            # audiomack wrapper around soundcloud song
            'add_ie': ['Soundcloud'],
            'url': 'http://www.audiomack.com/song/hip-hop-daily/black-mamba-freestyle',
            'info_dict': {
                'id': '258901379',
                'ext': 'mp3',
                'description': 'mamba day freestyle for the legend Kobe Bryant ',
                'title': 'Black Mamba Freestyle [Prod. By Danny Wolf]',
                'uploader': 'ILOVEMAKONNEN',
                'upload_date': '20160414',
            },
            'skip': 'Song has been removed from the site',
        },
        {
            'url': 'https://audiomack.com/floyymenor/song/pastillitas-de-color',
            'only_matching': True,
        },
        {
            'url': 'https://audiomack.com/embed/djlandlord/song/seyi-vibes-mix-2026-mixtape',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        artist, slug = self._match_artist_slug(url)
        display_id = f'{artist}/{slug}'
        song = self._call_api(f'music/song/{artist}/{slug}', display_id)

        if traverse_obj(song, 'geo_restricted'):
            self.raise_geo_restricted()
        if traverse_obj(song, 'private') == 'yes':
            raise ExtractorError('This song is private', expected=True)

        music_id = str_or_none(song.get('id')) or display_id
        stream_url = self._extract_stream_url(music_id, display_id)

        if song.get('is_soundcloud') or SoundcloudIE.suitable(stream_url):
            return self.url_result(stream_url, SoundcloudIE.ie_key())

        return self._parse_music(song, stream_url)


class AudiomackAlbumIE(AudiomackBaseIE):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/(?:embed/)?(?:album/(?P<artist>[\w-]+)|(?P<artist2>[\w-]+)/album)/(?P<id>[\w-]+)'
    IE_NAME = 'audiomack:album'
    _TESTS = [
        {
            # Standard album playlist
            'url': 'http://www.audiomack.com/album/flytunezcom/tha-tour-part-2-mixtape',
            'skip': 'video gone',
            'playlist_count': 11,
            'info_dict': {
                'id': '812251',
                'title': 'Tha Tour: Part 2 (Official Mixtape)',
            },
        },
        {
            # Album playlist ripped from fakeshoredrive with no metadata
            'url': 'http://www.audiomack.com/album/fakeshoredrive/ppp-pistol-p-project',
            'skip': 'video gone',
            'info_dict': {
                'title': 'PPP (Pistol P Project)',
                'id': '837572',
            },
            'playlist': [
                {
                    'info_dict': {
                        'title': 'PPP (Pistol P Project) - 8. Real (prod by SYK SENSE  )',
                        'id': '837576',
                        'ext': 'mp3',
                        'uploader': 'Lil Herb a.k.a. G Herbo',
                    },
                },
                {
                    'info_dict': {
                        'title': 'PPP (Pistol P Project) - 10. 4 Minutes Of Hell Part 4 (prod by DY OF 808 MAFIA)',
                        'id': '837580',
                        'ext': 'mp3',
                        'uploader': 'Lil Herb a.k.a. G Herbo',
                    },
                },
            ],
        },
        {
            'url': 'https://audiomack.com/floyymenor/album/man-in-black',
            'only_matching': True,
        },
    ]

    def _entries(self, album):
        for track in traverse_obj(album, ('tracks', ..., {dict})) or []:
            artist = traverse_obj(track, 'uploader_url_slug', {str})
            slug = traverse_obj(track, 'url_slug', {str})
            if not artist or not slug:
                continue
            yield self.url_result(
                f'https://audiomack.com/{artist}/song/{slug}',
                AudiomackIE,
                traverse_obj(track, 'song_id', {str_or_none}),
                traverse_obj(track, 'title', {str}),
            )

    def _real_extract(self, url):
        artist, slug = self._match_artist_slug(url)
        display_id = f'{artist}/{slug}'
        album = self._call_api(f'music/album/{artist}/{slug}', display_id)
        return self.playlist_result(
            self._entries(album),
            str_or_none(album.get('id')) or display_id,
            traverse_obj(album, 'title', {str}),
            traverse_obj(album, 'description', {clean_html}, filter),
        )
