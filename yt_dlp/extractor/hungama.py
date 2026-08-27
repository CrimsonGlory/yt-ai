from .common import InfoExtractor
from ..utils import (
    int_or_none,
    join_nonempty,
    remove_end,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class HungamaBaseIE(InfoExtractor):
    def _call_api(self, path, content_id, fatal=False):
        return traverse_obj(self._download_json(
            f'https://cpage.api.hungama.com/v2/page/content/{content_id}/{path}/detail',
            content_id, fatal=fatal, query={
                'device': 'web',
                'platform': 'a',
                'storeId': '1',
            }), ('data', {dict})) or {}

    def _extract_playable_formats(self, content_id, content_type=None):
        formats, subtitles, seen = [], {}, set()
        query = {'user': 'free'}
        if content_type is not None:
            query['contentType'] = content_type

        for device in ('web', None):
            playable = self._download_json(
                f'https://chraurls.api.hungama.com/v1/content/{content_id}/url/playable',
                content_id, fatal=False,
                query={**query, **({} if device is None else {'device': device})},
                note='Downloading playable URL JSON' + ('' if device else ' (no device)'))
            streams = []
            for stream in traverse_obj(playable, (
                'data', 'body', 'data', 'url', 'playable', ..., {dict},
            )) or []:
                if url_or_none(stream.get('data')):
                    streams.append(stream)
            # Previews are often 503; prefer full renditions when present
            for stream in [s for s in streams if s.get('key') != 'preview'] or streams:
                stream_url = stream['data']
                if stream_url in seen:
                    continue
                seen.add(stream_url)
                protocol = (stream.get('protocol') or '').lower()
                if protocol == 'hls' or 'index.m3u8' in stream_url:
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        stream_url, content_id, 'mp4', m3u8_id='hls', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                elif protocol == 'dash' or stream_url.endswith('.mpd'):
                    fmts, subs = self._extract_mpd_formats_and_subtitles(
                        stream_url, content_id, mpd_id='dash', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                else:
                    formats.append({
                        'url': stream_url,
                        'format_id': stream.get('key'),
                    })
            if formats:
                break
        return formats, subtitles


class HungamaIE(HungamaBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.|un\.)?hungama\.com/
                        (?:
                            (?:video|movie|short-film)/[^/]+/|
                            tv-show/(?:[^/]+/){2}\d+/episode/[^/]+/
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [{
        'url': 'http://www.hungama.com/video/krishna-chants/39349649/',
        'md5': '5d2be70f908fde3ecd7b7c107b0ad4b1',
        'info_dict': {
            'id': '39349649',
            'ext': 'mp4',
            'title': 'Krishna Chants',
            'description': ' ',
            'upload_date': '20180829',
            'duration': 264,
            'timestamp': 1535500800,
            'view_count': int,
            'thumbnail': r're:https://images1\.hungama\.com/.+',
            'tags': 'count:6',
        },
    }, {
        'url': 'https://un.hungama.com/short-film/adira/102524179/',
        'info_dict': {
            'id': '102524179',
            'ext': 'mp4',
            'title': 'Adira',
            'description': 'md5:df20cd4d41eabb33634f06de1025a4b4',
            'upload_date': '20230417',
            'timestamp': 1681689600,
            'view_count': int,
            'thumbnail': r're:https://images1\.hungama\.com/.+',
            'tags': 'count:7',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.hungama.com/movie/kahaani-2/44129919/',
        'only_matching': True,
    }, {
        'url': 'https://www.hungama.com/tv-show/padded-ki-pushup/season-1/44139461/episode/ep-02-training-sasu-pathlaag-karing/44139503/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        metadata = self._call_api('movie', video_id)
        formats, subtitles = self._extract_playable_formats(
            video_id, traverse_obj(metadata, ('head', 'data', 'type', {int_or_none})))
        if not formats:
            self.raise_no_formats('No playable formats returned', expected=True, video_id=video_id)

        return {
            **traverse_obj(metadata, ('head', 'data', {
                'title': ('title', {str}),
                'description': ('misc', 'description', {str}),
                'duration': ('duration', {int}),  # duration in JSON is incorrect if string
                'timestamp': ('releasedate', {unified_timestamp}),
                'view_count': ('misc', 'playcount', {int_or_none}),
                'thumbnail': ('image', {url_or_none}),
                'tags': ('misc', 'keywords', ..., {str}),
            })),
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        }


class HungamaSongIE(HungamaBaseIE):
    _VALID_URL = r'https?://(?:www\.|un\.)?hungama\.com/song/[^/]+/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.hungama.com/song/kitni-haseen-zindagi/2931166/',
        'skip': 'No public playable URL',
        'md5': '964f46828e8b250aa35e5fdcfdcac367',
        'info_dict': {
            'id': '2931166',
            'ext': 'mp3',
            'title': 'Lucky Ali - Kitni Haseen Zindagi',
            'track': 'Kitni Haseen Zindagi',
            'artist': 'Lucky Ali',
            'release_year': 2000,
            'thumbnail': 'https://stat2.hungama.ind.in/assets/images/default_images/da-200x200.png',
        },
    }, {
        'url': 'https://un.hungama.com/song/tum-kya-mile-from-rocky-aur-rani-kii-prem-kahaani/103553672',
        'skip': 'No public playable URL',
        'md5': '964f46828e8b250aa35e5fdcfdcac367',
        'info_dict': {
            'id': '103553672',
            'ext': 'mp3',
            'title': 'md5:5ebeb1e10771b634ce5f700ce68ae5f4',
            'track': 'Tum Kya Mile (From "Rocky Aur Rani Kii Prem Kahaani")',
            'artist': 'Pritam Chakraborty, Arijit Singh, Shreya Ghoshal, Amitabh Bhattacharya',
            'album': 'Tum Kya Mile (From "Rocky Aur Rani Kii Prem Kahaani")',
            'release_year': 2023,
            'thumbnail': 'https://images.hungama.com/c/1/7c2/c7b/103553671/103553671_200x200.jpg',
        },
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)
        metadata = self._call_api('song', audio_id)
        head = traverse_obj(metadata, ('head', 'data', {dict})) or {}
        formats, _ = self._extract_playable_formats(
            audio_id, traverse_obj(head, ('type', {int_or_none})))
        if not formats:
            self.raise_no_formats('No public playable URL', expected=True, video_id=audio_id)

        track = head.get('title')
        artist = join_nonempty(*traverse_obj(
            head, ('misc', 'singerf', ..., {str})), delim=', ') or head.get('subtitle')
        title = f'{artist} - {track}' if artist and track else track

        return {
            'id': audio_id,
            'title': title,
            'thumbnail': url_or_none(head.get('image')) or url_or_none(head.get('playble_image')),
            'track': track,
            'artist': artist or None,
            'album': traverse_obj(head, ('misc', 'p_name', 0, {str})) or None,
            'release_year': int_or_none(str(head.get('releasedate') or '')[:4]),
            'formats': formats,
        }


class HungamaAlbumPlaylistIE(HungamaBaseIE):
    _VALID_URL = r'https?://(?:www\.|un\.)?hungama\.com/(?P<path>playlists|album)/[^/]+/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.hungama.com/album/bhuj-the-pride-of-india/69481490/',
        'playlist_mincount': 7,
        'info_dict': {
            'id': '69481490',
        },
    }, {
        'url': 'https://www.hungama.com/playlists/hindi-jan-to-june-2021/123063/',
        'playlist_mincount': 25,
        'info_dict': {
            'id': '123063',
        },
    }, {
        'url': 'https://un.hungama.com/album/what-jhumka-%3F-from-rocky-aur-rani-kii-prem-kahaani/103891805/',
        'skip': 'video gone',
        'playlist_mincount': 1,
        'info_dict': {
            'id': '103891805',
        },
    }]

    def _real_extract(self, url):
        playlist_id, path = self._match_valid_url(url).group('id', 'path')
        data = self._call_api(remove_end(path, 's'), playlist_id, fatal=True)

        def entries():
            for song_url in traverse_obj(data, ('body', 'rows', ..., 'data', 'misc', 'share', {url_or_none})):
                yield self.url_result(song_url, HungamaSongIE)

        return self.playlist_result(entries(), playlist_id)
