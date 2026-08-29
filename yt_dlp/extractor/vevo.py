import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    parse_resolution,
    traverse_obj,
    url_or_none,
)


class VevoBaseIE(InfoExtractor):
    _GRAPHQL_API = 'https://api.vevo.com/graphql'
    _GRAPHQL_TOKEN = 'fny8q3azy3jy94wsjavj3hr3gc'
    _GEO_COUNTRIES = ['US', 'GB', 'CA', 'AU']
    _GEO_BYPASS = False

    def _call_graphql(self, query, variables, video_id, note='Downloading GraphQL JSON', country=None):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._GRAPHQL_TOKEN}',
        }
        if country:
            headers['country-code'] = country
        data = self._download_json(
            self._GRAPHQL_API, video_id, note,
            data=json.dumps({'query': query, 'variables': variables}).encode(),
            headers=headers)
        errors = data.get('errors')
        if errors:
            if isinstance(errors, dict):
                message = errors.get('message')
            else:
                message = join_nonempty(*(
                    traverse_obj(err, ('message', {str}))
                    for err in errors), delim=', ')
            raise ExtractorError(
                f'{self.IE_NAME} said: {message or "GraphQL error"}', expected=True)
        return data

    def _iter_countries(self):
        explicit = (self.get_param('geo_bypass_country') or '').upper() or None
        if explicit:
            yield explicit
            return
        if self.get_param('geo_bypass', True):
            yield from self._GEO_COUNTRIES
        else:
            yield None


class VevoIE(VevoBaseIE):
    """
    Accepts urls from vevo.com or in the format 'vevo:{id}'
    (currently used by MTVIE and MySpaceIE)
    """
    _VALID_URL = r'''(?x)
        (?:https?://(?:www\.)?vevo\.com/watch/(?!playlist|genre)(?:[^/]+/(?:[^/]+/)?)?|
           https?://cache\.vevo\.com/m/html/embed\.html\?video=|
           https?://videoplayer\.vevo\.com/embed/embedded\?videoId=|
           https?://embed\.vevo\.com/.*?[?&]isrc=|
           https?://tv\.vevo\.com/watch/artist/(?:[^/]+)/|
           vevo:)
        (?P<id>[^&?#]+)'''
    _EMBED_REGEX = [r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:cache\.)?vevo\.com/.+?)\1']
    _QUERY_VIDEO = '''\
query GetVideo($id: String!) {
  video(id: $id) {
    id
    title
    thumbnail
    genre
    explicit
    hls
    dash
    mp4 { quality url }
    created
    duration
    unavailable
    artists { role artist { name } }
    viewCounts { total }
    captions { srt { url } vtt { url } ttml { url } }
  }
}'''

    _TESTS = [{
        'url': 'http://www.vevo.com/watch/hurts/somebody-to-die-for/GB1101300280',
        'md5': 'd84af2c66db9949d79fd6fb1ab5a83ec',
        'info_dict': {
            'id': 'GB1101300280',
            'ext': 'mp4',
            'title': 'Hurts - Somebody to Die For (Official Video)',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png)',
            'timestamp': 1688688410,
            'upload_date': '20230707',
            'uploader': 'Hurts',
            'track': 'Somebody to Die For (Official Video)',
            'artist': 'Hurts',
            'artists': ['Hurts'],
            'genre': 'Pop',
            'genres': ['Pop'],
            'duration': 230,
            'age_limit': 0,
            'view_count': int,
        },
        'params': {'format': 'http-high'},
    }, {
        'note': 'v3 HTTP/HLS formats',
        'url': 'http://www.vevo.com/watch/cassadee-pope/i-wish-i-could-break-your-heart/USUV71302923',
        'info_dict': {
            'id': 'USUV71302923',
            'ext': 'mp4',
            'title': 'Cassadee Pope - I Wish I Could Break Your Heart',
            'thumbnail': r're:https?://.+',
            'timestamp': 1688686495,
            'upload_date': '20230706',
            'uploader': 'Cassadee Pope',
            'track': 'I Wish I Could Break Your Heart',
            'artist': 'Cassadee Pope',
            'artists': ['Cassadee Pope'],
            'genre': 'Country',
            'genres': ['Country'],
            'duration': 226,
            'age_limit': 0,
            'view_count': int,
        },
        'params': {'skip_download': True},
    }, {
        'note': 'Age-limited video',
        'url': 'https://www.vevo.com/watch/justin-timberlake/tunnel-vision-explicit/USRV81300282',
        'info_dict': {
            'id': 'USRV81300282',
            'ext': 'mp4',
            'title': 'Justin Timberlake - Tunnel Vision (Explicit)',
            'thumbnail': r're:https?://.+',
            'timestamp': 1688705194,
            'upload_date': '20230707',
            'age_limit': 18,
            'uploader': 'Justin Timberlake',
            'track': 'Tunnel Vision (Explicit)',
            'artist': 'Justin Timberlake',
            'artists': ['Justin Timberlake'],
            'genre': 'Pop',
            'genres': ['Pop'],
            'duration': 418,
            'view_count': int,
        },
        'params': {'skip_download': True},
    }, {
        'note': 'Featured artist',
        'url': 'http://www.vevo.com/watch/k-camp-1/Till-I-Die/USUV71503000',
        'info_dict': {
            'id': 'USUV71503000',
            'ext': 'mp4',
            'title': 'K CAMP ft. T.I. - Till I Die',
            'thumbnail': r're:https?://.+',
            'timestamp': 1688696215,
            'upload_date': '20230707',
            'age_limit': 18,
            'uploader': 'K CAMP',
            'track': 'Till I Die',
            'artist': 'K CAMP ft. T.I.',
            'artists': ['K CAMP ft. T.I.'],
            'genre': 'Hip Hop',
            'genres': ['Hip Hop'],
            'duration': 194,
            'view_count': int,
        },
        'params': {'skip_download': True},
    }, {
        'note': 'Featured test',
        'url': 'https://www.vevo.com/watch/lemaitre/Wait/USUV71402190',
        'info_dict': {
            'id': 'USUV71402190',
            'ext': 'mp4',
            'title': 'Lemaitre ft. Lolo - Wait',
            'thumbnail': r're:https?://.+',
            'timestamp': 1688694976,
            'upload_date': '20230707',
            'age_limit': 0,
            'uploader': 'Lemaitre',
            'track': 'Wait',
            'artist': 'Lemaitre ft. Lolo',
            'artists': ['Lemaitre ft. Lolo'],
            'genre': 'Electronic',
            'genres': ['Electronic'],
            'duration': 205,
            'view_count': int,
        },
        'params': {'skip_download': True},
    }, {
        'note': 'Only available via webpage',
        'url': 'http://www.vevo.com/watch/GBUV71600656',
        'md5': '67e79210613865b66a47c33baa5e37fe',
        'info_dict': {
            'id': 'GBUV71600656',
            'ext': 'mp4',
            'title': 'ABC - Viva Love',
        },
        'skip': 'Unavailable in tested Vevo TV markets',
    }, {
        # no genres available
        'url': 'http://www.vevo.com/watch/INS171400764',
        'only_matching': True,
    }, {
        # Another case available only via the webpage; using streams/streamsV3 formats
        # Geo-restricted to Netherlands/Germany
        'url': 'http://www.vevo.com/watch/boostee/pop-corn-clip-officiel/FR1A91600909',
        'only_matching': True,
    }, {
        'url': 'https://embed.vevo.com/?isrc=USH5V1923499&partnerId=4d61b777-8023-4191-9ede-497ed6c24647&partnerAdCode=',
        'only_matching': True,
    }, {
        'url': 'https://tv.vevo.com/watch/artist/janet-jackson/US0450100550',
        'only_matching': True,
    }]

    def _extract_video(self, video_id):
        last_video = None
        for country in self._iter_countries():
            note = 'Downloading GraphQL video info'
            if country:
                note += f' ({country})'
            data = self._call_graphql(
                self._QUERY_VIDEO, {'id': video_id}, video_id, note, country)
            video = traverse_obj(data, ('data', 'video', {dict}))
            if not video:
                continue
            last_video = video
            if not video.get('unavailable'):
                return video
        if last_video:
            self.raise_geo_restricted(
                'This video is not available in the requested Vevo market',
                countries=self._GEO_COUNTRIES)
        raise ExtractorError('Unable to extract Vevo video info', expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._extract_video(video_id)

        formats = []
        seen_urls = set()

        def add_http_format(format_url, format_id):
            format_url = url_or_none(format_url)
            if not format_url or format_url in seen_urls:
                return
            seen_urls.add(format_url)
            fmt = {
                'url': format_url,
                'format_id': format_id,
                'ext': determine_ext(format_url, 'mp4'),
                **parse_resolution(format_url),
            }
            mobj = re.search(
                r'_(?P<width>\d+)x(?P<height>\d+)_(?P<vcodec>[a-z0-9]+)_(?P<vbr>\d+)_(?P<acodec>[a-z0-9]+)_(?P<abr>\d+)',
                format_url, re.I)
            if mobj:
                fmt.update({
                    'width': int(mobj.group('width')),
                    'height': int(mobj.group('height')),
                    'vcodec': mobj.group('vcodec'),
                    'vbr': int(mobj.group('vbr')),
                    'acodec': mobj.group('acodec'),
                    'abr': int(mobj.group('abr')),
                })
            formats.append(fmt)

        for mp4 in traverse_obj(video, ('mp4', ..., {dict})) or []:
            add_http_format(mp4.get('url'), join_nonempty('http', mp4.get('quality')))

        dash_url = url_or_none(video.get('dash'))
        if dash_url:
            if determine_ext(dash_url) == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    dash_url, video_id, mpd_id='dash', fatal=False))
            else:
                add_http_format(dash_url, 'http-dash')

        hls_url = url_or_none(video.get('hls'))
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        main, featured = [], []
        for item in traverse_obj(video, ('artists', ..., {dict})) or []:
            name = traverse_obj(item, ('artist', 'name', {str}))
            if not name:
                continue
            if (item.get('role') or '').lower() == 'featured':
                featured.append(name)
            else:
                main.append(name)

        uploader = main[0] if main else None
        artist = join_nonempty(*main, delim=', ')
        if featured:
            artist = join_nonempty(artist, f'ft. {join_nonempty(*featured, delim=", ")}', delim=' ')
        track = video.get('title')
        title = join_nonempty(artist, track, delim=' - ') or video_id

        is_explicit = video.get('explicit')
        if is_explicit is True:
            age_limit = 18
        elif is_explicit is False:
            age_limit = 0
        else:
            age_limit = None

        subtitles = {}
        for lang_ext, cap_url in (
            ('srt', traverse_obj(video, ('captions', 'srt', 'url', {url_or_none}))),
            ('vtt', traverse_obj(video, ('captions', 'vtt', 'url', {url_or_none}))),
            ('ttml', traverse_obj(video, ('captions', 'ttml', 'url', {url_or_none}))),
        ):
            if cap_url:
                subtitles.setdefault('en', []).append({
                    'url': cap_url,
                    'ext': lang_ext,
                })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': url_or_none(video.get('thumbnail')),
            'timestamp': parse_iso8601(video.get('created')),
            'uploader': uploader,
            'duration': int_or_none(video.get('duration'), scale=1000),
            'view_count': int_or_none(traverse_obj(video, ('viewCounts', 'total'))),
            'age_limit': age_limit,
            'track': track,
            'artist': artist or uploader,
            'genre': video.get('genre'),
            'subtitles': subtitles or None,
        }


class VevoPlaylistIE(VevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vevo\.com/watch/(?P<kind>playlist|genre)/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.vevo.com/watch/genre/rock',
        'info_dict': {
            'id': 'rock',
            'title': 'Rock',
        },
        'playlist_count': 20,
        'skip': 'Vevo consumer playlist pages now redirect to hq.vevo.com',
    }, {
        'url': 'http://www.vevo.com/watch/genre/rock?index=0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_valid_url(url).group('id')
        raise ExtractorError(
            'Vevo consumer playlist pages are no longer available',
            expected=True, video_id=playlist_id)
