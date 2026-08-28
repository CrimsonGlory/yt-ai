from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    qualities,
    traverse_obj,
    url_or_none,
)


class NprIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?npr\.org/(?:sections/[^/]+/)?\d{4}/\d{2}/\d{2}/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.npr.org/sections/allsongs/2015/10/21/449974205/new-music-from-beach-house-chairlift-cmj-discoveries-and-more',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '449974205',
            'title': 'New Music From Beach House, Chairlift, CMJ Discoveries And More',
        },
        'playlist_count': 7,
    }, {
        'url': 'https://www.npr.org/sections/deceptivecadence/2015/10/09/446928052/music-from-the-shadows-ancient-armenian-hymns-and-piano-jazz',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '446928052',
            'title': "Songs We Love: Tigran Hamasyan, 'Your Mercy is Boundless'",
        },
        'playlist': [{
            'md5': '12fa60cb2d3ed932f53609d4aeceabf1',
            'info_dict': {
                'id': '446929930',
                'ext': 'mp3',
                'title': 'Your Mercy is Boundless (Bazum en Qo gtutyunqd)',
                'duration': 402,
            },
        }],
    }, {
        # multimedia, not media title
        'url': 'https://www.npr.org/2017/06/19/533198237/tigers-jaw-tiny-desk-concert',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '533198237',
            'title': 'Tigers Jaw: Tiny Desk Concert',
        },
        'playlist': [{
            'md5': '12fa60cb2d3ed932f53609d4aeceabf1',
            'info_dict': {
                'id': '533201718',
                'ext': 'mp4',
                'title': 'Tigers Jaw: Tiny Desk Concert',
                'duration': 402,
            },
        }],
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        # multimedia, no formats, stream
        'url': 'https://www.npr.org/2020/02/14/805476846/laura-stevenson-tiny-desk-concert',
        'only_matching': True,
    }, {
        'url': 'https://www.npr.org/2022/03/15/1084896560/bonobo-tiny-desk-home-concert',
        'md5': '43d5eebbe13a463da72255814431f0a0',
        'info_dict': {
            'id': '1084896560',
            'ext': 'mp4',
            'title': 'Bonobo: Tiny Desk (Home) Concert',
            'description': 'md5:d3423705cde0fd76a3dedabda5726a9a',
            'thumbnail': r're:^https?://.+\.(?:jpg|jpeg)',
            'duration': 1061.0,
            'timestamp': 1647337020,
            'upload_date': '20220315',
        },
        'params': {
            'format': '1080p/best[ext=mp4][protocol=https]/best',
        },
    }, {
        'url': 'https://www.npr.org/2026/08/27/g-s1-139808/e-u-tiny-desk-concert',
        'only_matching': True,
    }, {
        'url': 'https://www.npr.org/2026/08/27/nx-s1-5946375/ratko-mladic-dead',
        'only_matching': True,
    }]

    def _extract_json_ld_media(self, url, video_id):
        webpage = self._download_webpage(url, video_id)
        json_ld_list = list(self._yield_json_ld(webpage, video_id, fatal=False))
        media_url = traverse_obj(json_ld_list, (
            ..., 'subjectOf', ..., ('embedUrl', 'contentUrl'), {url_or_none}), get_all=False)
        if not media_url:
            return None

        info = self._search_json_ld(webpage, video_id, default={})
        info.pop('url', None)
        info.pop('ext', None)

        jw_id = self._search_regex(
            r'cdn\.jwplayer\.com/manifests/(\w+)', media_url, 'jwplayer id', default=None)
        if jw_id:
            jw_info = self._parse_jwplayer_data(
                self._download_json(f'https://cdn.jwplayer.com/v2/media/{jw_id}', video_id),
                video_id, require_title=False, m3u8_id='hls')
            info['formats'] = jw_info.get('formats')
            info['duration'] = jw_info.get('duration')
            info['subtitles'] = jw_info.get('subtitles') or info.get('subtitles')
        elif determine_ext(media_url) == 'm3u8':
            info['formats'] = self._extract_m3u8_formats(
                media_url, video_id, 'mp4', m3u8_id='hls')
        else:
            info['formats'] = [{'url': media_url}]

        info.update({
            'id': video_id,
            'title': info.get('title') or self._og_search_title(webpage),
            'description': info.get('description') or self._og_search_description(webpage),
            'thumbnail': (info.get('thumbnail')
                          or traverse_obj(info, ('thumbnails', 0, 'url'))
                          or self._og_search_thumbnail(webpage)),
        })
        return info

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage_info = self._extract_json_ld_media(url, playlist_id)
        if webpage_info:
            return webpage_info

        story = traverse_obj(self._download_json(
            'https://api.npr.org/query', playlist_id, fatal=False, query={
                'id': playlist_id,
                'fields': 'audio,multimedia,title',
                'format': 'json',
                'apiKey': 'MDAzMzQ2MjAyMDEyMzk4MTU1MDg3ZmM3MQ010',
            }), ('list', 'story', 0))
        if not story:
            raise ExtractorError('No media found', expected=True)
        playlist_title = story.get('title', {}).get('$text')

        KNOWN_FORMATS = ('threegp', 'm3u8', 'smil', 'mp4', 'mp3')
        quality = qualities(KNOWN_FORMATS)

        entries = []
        for media in story.get('audio', []) + story.get('multimedia', []):
            media_id = media['id']

            formats = []
            for format_id, formats_entry in media.get('format', {}).items():
                if not formats_entry:
                    continue
                if isinstance(formats_entry, list):
                    formats_entry = formats_entry[0]
                format_url = formats_entry.get('$text')
                if not format_url:
                    continue
                if format_id in KNOWN_FORMATS:
                    if format_id == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            format_url, media_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    elif format_id == 'smil':
                        smil_formats = self._extract_smil_formats(
                            format_url, media_id, transform_source=lambda s: s.replace(
                                'rtmp://flash.npr.org/ondemand/', 'https://ondemand.npr.org/'),
                            fatal=False)
                        self._check_formats(smil_formats, media_id)
                        formats.extend(smil_formats)
                    else:
                        formats.append({
                            'url': format_url,
                            'format_id': format_id,
                            'quality': quality(format_id),
                        })
            for stream_id, stream_entry in media.get('stream', {}).items():
                if not isinstance(stream_entry, dict):
                    continue
                if stream_id != 'hlsUrl':
                    continue
                stream_url = url_or_none(stream_entry.get('$text'))
                if not stream_url:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    stream_url, stream_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))

            if not formats:
                raw_json_ld = self._yield_json_ld(self._download_webpage(url, playlist_id), playlist_id, fatal=False)
                m3u8_url = traverse_obj(list(raw_json_ld), (..., 'subjectOf', ..., 'embedUrl'), get_all=False)
                formats = self._extract_m3u8_formats(m3u8_url, media_id, 'mp4', m3u8_id='hls', fatal=False)

            entries.append({
                'id': media_id,
                'title': media.get('title', {}).get('$text') or playlist_title,
                'thumbnail': media.get('altImageUrl', {}).get('$text'),
                'duration': int_or_none(media.get('duration', {}).get('$text')),
                'formats': formats,
            })

        return self.playlist_result(entries, playlist_id, playlist_title)
