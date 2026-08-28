import re

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    parse_iso8601,
    try_get,
    unescapeHTML,
    url_or_none,
)


class RteBaseIE(InfoExtractor):
    def _add_direct_url(self, formats, url, item_id, medium=None):
        media_url = url_or_none(unescapeHTML(url))
        if not media_url:
            return
        ext = determine_ext(media_url, default_ext=None)
        if ext == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                media_url, item_id, 'mp4', m3u8_id='hls', fatal=False))
        elif ext in ('mp3', 'm4a', 'aac', 'mp4', 'flv', 'wav'):
            fmt = {
                'url': media_url,
                'ext': ext,
                'format_id': medium or ext,
            }
            if medium == 'audio' or ext in ('mp3', 'm4a', 'aac', 'wav'):
                fmt['vcodec'] = 'none'
            formats.append(fmt)

    def _real_extract(self, url):
        item_id = self._match_id(url)

        info_dict = {}
        formats = []

        ENDPOINTS = (
            'https://www.rte.ie/rteavgen/getplaylist/?type=web&format=json&id=',
            'https://feeds.rasset.ie/rteavgen/player/playlist?type=iptv&format=json&showId=',
        )

        for num, ep_url in enumerate(ENDPOINTS, start=1):
            try:
                data = self._download_json(ep_url + item_id, item_id)
            except ExtractorError as ee:
                if num < len(ENDPOINTS) or formats:
                    continue
                if isinstance(ee.cause, HTTPError) and ee.cause.status == 404:
                    error_info = self._parse_json(ee.cause.response.read().decode(), item_id, fatal=False)
                    if error_info:
                        raise ExtractorError(
                            '{} said: {}'.format(self.IE_NAME, error_info['message']),
                            expected=True)
                raise

            # NB the string values in the JSON are stored using XML escaping(!)
            show = try_get(data, lambda x: x['shows'][0], dict)
            if not show:
                continue

            if not info_dict:
                title = unescapeHTML(show['title'])
                description = unescapeHTML(show.get('description'))
                thumbnail = show.get('thumbnail')
                duration = float_or_none(show.get('duration'), 1000)
                timestamp = parse_iso8601(show.get('published'))
                info_dict = {
                    'id': item_id,
                    'title': title,
                    'description': description,
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'duration': duration,
                }

            self._add_direct_url(
                formats, show.get('url'), item_id, medium=show.get('medium'))

            mg = try_get(show, lambda x: x['media:group'][0], dict)
            if mg:
                if mg.get('url'):
                    m = re.match(
                        r'(?P<url>rtmpe?://[^/]+)/(?P<app>.+)/(?P<playpath>mp4:.*)',
                        mg['url'])
                    if m:
                        m = m.groupdict()
                        formats.append({
                            'url': m['url'] + '/' + m['app'],
                            'app': m['app'],
                            'play_path': m['playpath'],
                            'player_url': url,
                            'ext': 'flv',
                            'format_id': 'rtmp',
                        })
                    else:
                        self._add_direct_url(
                            formats, mg['url'], item_id, medium=mg.get('medium'))

                hls_formats = []
                if mg.get('hls_server') and mg.get('hls_url'):
                    hls = url_or_none(f'{mg["hls_server"]}{mg["hls_url"]}')
                    if hls:
                        hls_formats = self._extract_m3u8_formats(
                            hls, item_id, 'mp4',
                            entry_protocol='m3u8_native', m3u8_id='hls', fatal=False) or []
                        formats.extend(hls_formats)

                # HTTP HDS (port 80) times out; rtmpe:// is no longer downloadable
                if not hls_formats and mg.get('hds_server') and mg.get('hds_url'):
                    hds = url_or_none(f'{mg["hds_server"]}{mg["hds_url"]}')
                    if hds and hds.startswith('http'):
                        formats.extend(self._extract_f4m_formats(
                            hds, item_id, f4m_id='hds', fatal=False))

            if any((f.get('url') or '').startswith('http') for f in formats):
                break

        info_dict['formats'] = formats
        return info_dict


class RteIE(RteBaseIE):
    IE_NAME = 'rte'
    IE_DESC = 'Raidió Teilifís Éireann TV'
    _VALID_URL = r'https?://(?:www\.)?rte\.ie/player/[^/]{2,3}/show/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.rte.ie/player/ie/show/iwitness-862/10478715/',
        'skip': 'DRM protected',
        'md5': '4a76eb3396d98f697e6e8110563d2604',
        'info_dict': {
            'id': '10478715',
            'ext': 'mp4',
            'title': 'iWitness',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'The spirit of Ireland, one voice and one minute at a time.',
            'duration': 60.046,
            'upload_date': '20151012',
            'timestamp': 1444694160,
        },
    }


class RteRadioIE(RteBaseIE):
    IE_NAME = 'rte:radio'
    IE_DESC = 'Raidió Teilifís Éireann radio'
    # Radioplayer URLs have two distinct specifier formats,
    # the old format #!rii=<channel_id>:<id>:<playable_item_id>:<date>:
    # the new format #!rii=b<channel_id>_<id>_<playable_item_id>_<date>_
    # where the IDs are int/empty, the date is DD-MM-YYYY, and the specifier may be truncated.
    # An <id> uniquely defines an individual recording, and is the only part we require.
    _VALID_URL = [
        r'https?://(?:www\.)?rte\.ie/radio/utils/radioplayer/rteradioweb\.html#!rii=(?:b?[0-9]*)(?:%3A|:|%5F|_)(?P<id>[0-9]+)',
        r'https?://(?:www\.)?rte\.ie/radio/(?:[^/?#]+/){1,3}episodes/(?P<id>[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}|\d+)/?(?:$|[?#])',
    ]

    _TESTS = [{
        'url': 'https://www.rte.ie/radio/radio1/the-history-show/episodes/11800540/',
        'md5': 'd2e0d7e3fe4a8542d70d45eb42e4f43d',
        'info_dict': {
            'id': '11800540',
            'ext': 'mp4',
            'title': 'The History Show',
            'description': 'As the United States prepares to mark its 250th anniversary, Myles Dungan and guests explore the people, the principles, and the institutions that shaped the American Republic. With Daniel Carey, Brian Phillips Murphy, Paul McElhinney and Stewart McLaurin.',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1780855200,
            'upload_date': '20260607',
            'duration': 3009.584,
        },
    }, {
        'url': 'https://www.rte.ie/radio/radio1/liveline/episodes/22a4f16a-07e1-4a8f-8fe3-b4b400e9b67f',
        'only_matching': True,
    }, {
        # Old-style player URL; HLS and RTMPE formats
        'url': 'http://www.rte.ie/radio/utils/radioplayer/rteradioweb.html#!rii=16:10507902:2414:27-12-2015:',
        'skip': 'old radioplayer URL gone',
        'md5': 'c79ccb2c195998440065456b69760411',
        'info_dict': {
            'id': '10507902',
            'ext': 'mp4',
            'title': 'Gloria',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:9ce124a7fb41559ec68f06387cabddf0',
            'timestamp': 1451203200,
            'upload_date': '20151227',
            'duration': 7230.0,
        },
    }, {
        # New-style player URL; RTMPE formats only
        'url': 'http://rte.ie/radio/utils/radioplayer/rteradioweb.html#!rii=b16_3250678_8861_06-04-2012_',
        'skip': 'Unsupported URL / extractor broken',
        'info_dict': {
            'id': '3250678',
            'ext': 'flv',
            'title': 'The Lyric Concert with Paul Herriott',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': '',
            'timestamp': 1333742400,
            'upload_date': '20120406',
            'duration': 7199.016,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }]
