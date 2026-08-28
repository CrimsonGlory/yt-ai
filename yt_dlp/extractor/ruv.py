import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    parse_duration,
    traverse_obj,
    unified_timestamp,
)


class RuvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ruv\.is/(?:sarpurinn/[^/]+|node)/(?P<id>[^/]+(?:/\d+)?)'
    _TESTS = [{
        # m3u8
        'url': 'http://ruv.is/sarpurinn/ruv-aukaras/fh-valur/20170516',
        'md5': '66347652f4e13e71936817102acc1724',
        'info_dict': {
            'id': '1144499',
            'display_id': 'fh-valur/20170516',
            'ext': 'mp4',
            'title': 'FH - Valur',
            'description': 'Bein útsending frá 3. leik FH og Vals í úrslitum Olísdeildar karla í handbolta.',
            'timestamp': 1494963600,
            'upload_date': '20170516',
        },
        'skip': 'sarpurinn URLs redirect to the current /sjonvarp player',
    }, {
        # mp3
        'url': 'http://ruv.is/sarpurinn/ras-2/morgunutvarpid/20170619',
        'md5': '395ea250c8a13e5fdb39d4670ef85378',
        'info_dict': {
            'id': '1153630',
            'display_id': 'morgunutvarpid/20170619',
            'ext': 'mp3',
            'title': 'Morgunútvarpið',
            'description': 'md5:a4cf1202c0a1645ca096b06525915418',
            'timestamp': 1497855000,
            'upload_date': '20170619',
        },
        'skip': 'sarpurinn URLs redirect to the current /sjonvarp player',
    }, {
        'url': 'http://ruv.is/sarpurinn/ruv/frettir/20170614',
        'only_matching': True,
    }, {
        'url': 'http://www.ruv.is/node/1151854',
        'only_matching': True,
    }, {
        'url': 'http://ruv.is/sarpurinn/klippa/secret-soltice-hefst-a-morgun',
        'only_matching': True,
    }, {
        'url': 'http://ruv.is/sarpurinn/ras-1/morgunvaktin/20170619',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)

        FIELD_RE = r'video\.%s\s*=\s*(["\'])(?P<url>(?:(?!\1).)+)\1'

        media_url = self._html_search_regex(
            FIELD_RE % 'src', webpage, 'video URL', group='url')

        video_id = self._search_regex(
            r'<link\b[^>]+\bhref=["\']https?://www\.ruv\.is/node/(\d+)',
            webpage, 'video id', default=display_id)

        ext = determine_ext(media_url)

        if ext == 'm3u8':
            formats = self._extract_m3u8_formats(
                media_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls')
        elif ext == 'mp3':
            formats = [{
                'format_id': 'mp3',
                'url': media_url,
                'vcodec': 'none',
            }]
        else:
            formats = [{
                'url': media_url,
            }]

        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._search_regex(
            FIELD_RE % 'poster', webpage, 'thumbnail', fatal=False)
        timestamp = unified_timestamp(self._html_search_meta(
            'article:published_time', webpage, 'timestamp', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'formats': formats,
        }


class RuvSpilaIE(InfoExtractor):
    IE_NAME = 'ruv.is:spila'
    _VALID_URL = r'https?://(?:www\.)?ruv\.is/(?:(?:sjon|ut)varp|(?:krakka|ung)ruv)/spila/.+/(?P<series_id>[0-9]+)/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        'url': 'https://www.ruv.is/sjonvarp/spila/svepparikid/33431/9uqaji',
        'info_dict': {
            'id': '9uqaji',
            'ext': 'mp4',
            'title': 'Matur',
            'description': 'md5:5337bca4ea78819d604be8291aea91be',
            'timestamp': 1755459900,
            'upload_date': '20250817',
            'thumbnail': r're:https://myndir\.ruv\.is/.+',
            'age_limit': 0,
            'chapters': [],
        },
        'expected_warnings': ['Ignoring subtitle tracks found in the HLS manifest'],
    }, {
        'url': 'https://www.ruv.is/sjonvarp/spila/ithrottir/30657/9jcnd4',
        'info_dict': {
            'id': '9jcnd4',
            'ext': 'mp4',
            'title': '01.02.2022',
            'chapters': 'count:4',
            'timestamp': 1643743500,
            'upload_date': '20220201',
            'thumbnail': 'https://d38kdhuogyllre.cloudfront.net/fit-in/1960x/filters:quality(65)/hd_posters/94boog-iti3jg.jpg',
            'description': 'Íþróttafréttir.',
            'age_limit': 0,
        },
        'skip': 'video gone',
    }, {
        'url': 'https://www.ruv.is/utvarp/spila/i-ljosi-sogunnar/23795/7hqkre',
        'info_dict': {
            'id': '7hqkre',
            'ext': 'mp3',
            'thumbnail': 'https://d38kdhuogyllre.cloudfront.net/fit-in/1960x/filters:quality(65)/hd_posters/7hqkre-7uepao.jpg',
            'description': 'md5:8d7046549daff35e9a3190dc9901a120',
            'chapters': [],
            'upload_date': '20220204',
            'timestamp': 1643965500,
            'title': 'Nellie Bly II',
            'age_limit': 0,
        },
        'skip': 'video gone',
    }, {
        'url': 'https://www.ruv.is/ungruv/spila/ungruv/28046/8beuph',
        'only_matching': True,
    }, {
        'url': 'https://www.ruv.is/krakkaruv/spila/krakkafrettir/30712/9jbgb0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, series_id = self._match_valid_url(url).group('id', 'series_id')
        program = self._download_json(
            'https://www.ruv.is/gql/', display_id, data=json.dumps({'query': '''{
                Program(id: %s){
                    title image description short_description
                    episodes(id: {value: "%s"}) {
                        rating title duration file image firstrun description
                        clips {
                            time text
                        }
                        subtitles {
                            name value
                        }
                    }
                }
            }''' % (series_id, display_id)}).encode(), headers={
                'Content-Type': 'application/json',
            })['data']['Program']  # noqa: UP031
        episode = traverse_obj(program, ('episodes', 0, {dict}))
        if not episode:
            raise ExtractorError('Episode is unavailable', expected=True)

        subs = {}
        for trk in episode.get('subtitles') or []:
            if trk.get('name') and trk.get('value'):
                subs.setdefault(trk['name'], []).append({'url': trk['value'], 'ext': 'vtt'})

        media_url = episode.get('file')
        if not media_url:
            raise ExtractorError('No media URL available', expected=True)
        if determine_ext(media_url) == 'm3u8':
            formats = self._extract_m3u8_formats(media_url, display_id)
        else:
            formats = [{'url': media_url}]

        clips = [
            {'start_time': parse_duration(c.get('time')), 'title': c.get('text')}
            for c in episode.get('clips') or []]

        return {
            'id': display_id,
            'title': traverse_obj(program, ('episodes', 0, 'title'), 'title'),
            'description': traverse_obj(
                program, ('episodes', 0, 'description'), 'description', 'short_description',
                expected_type=lambda x: x or None),
            'subtitles': subs,
            'thumbnail': (episode.get('image') or '').replace('$$IMAGESIZE$$', '1960') or None,
            'timestamp': unified_timestamp(episode.get('firstrun')),
            'formats': formats,
            'age_limit': episode.get('rating'),
            'chapters': clips,
        }
