import json

from .common import InfoExtractor
from ..utils import (
    bug_reports_message,
    clean_html,
    get_element_by_class,
    js_to_json,
    mimetype2ext,
    strip_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class BTVPlusIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?btvplus\.bg/(?:produkt/(?:predavaniya|seriali|novini)/(?P<id>\d+)|(?P<live>live)/?)')
    # Product pages are behind a Cloudflare managed challenge. The public
    # livestream is served via Google DAI APIs that do not require the webpage.
    _LIVE_PROJECT = '239117298520'
    _LIVE_REGION = 'europe-west1'
    _LIVE_EVENT_ID = 'btv-rmt-dai'
    _LIVE_NETWORK = '120344282'
    _TESTS = [{
        'url': 'https://btvplus.bg/live/',
        'info_dict': {
            'id': 'live',
            'ext': 'mp4',
            'title': r're:^bTV \d{4}-\d{2}-\d{2} \d{2}:\d{2}$',
            'live_status': 'is_live',
            'is_live': True,
        },
    }, {
        'url': 'https://btvplus.bg/produkt/predavaniya/67271/btv-reporterite/btv-reporterite-12-07-2025-g',
        'skip': 'Cloudflare managed challenge',
        'info_dict': {
            'ext': 'mp4',
            'id': '67271',
            'title': 'bTV Репортерите - 12.07.2025 г.',
            'thumbnail': 'https://cdn.btv.bg/media/images/940x529/Jul2025/2113606319.jpg',
        },
    }, {
        'url': 'https://btvplus.bg/produkt/seriali/66942/sezon-2/plen-sezon-2-epizod-55',
        'skip': 'Cloudflare managed challenge',
        'info_dict': {
            'ext': 'mp4',
            'id': '66942',
            'title': 'Плен - сезон 2, епизод 55',
            'thumbnail': 'https://cdn.btv.bg/media/images/940x529/Jun2025/2113595104.jpg',
        },
    }, {
        'url': 'https://btvplus.bg/produkt/novini/67270/btv-novinite-centralna-emisija-12-07-2025',
        'only_matching': True,
    }, {
        'url': 'https://btvplus.bg/live',
        'only_matching': True,
    }]

    def _extract_live(self):
        video_id = 'live'
        access_token = self._download_json(
            'https://dai-api.bweb.bg:3000/get-token', video_id,
            note='Downloading access token')['access_token']
        project, region, event_id = self._LIVE_PROJECT, self._LIVE_REGION, self._LIVE_EVENT_ID
        asset_key = f'{project}-{region}-{event_id}'
        stream_id_url = (
            'https://pubads.g.doubleclick.net/ssai/pods/api/v1/network/'
            f'{self._LIVE_NETWORK}/custom_asset/{asset_key}/stream')
        stream_id = self._download_json(
            stream_id_url, video_id, note='Downloading stream ID', data=b'')['stream_id']
        session = self._download_json(
            f'https://videostitcher.googleapis.com/v1/projects/{project}/locations/{region}/liveSessions',
            video_id, note='Creating live session',
            data=json.dumps({
                'live_config': f'projects/{project}/locations/{region}/liveConfigs/{event_id}',
                'gam_settings': {'stream_id': stream_id},
            }).encode(),
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            })
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            session['playUri'], video_id, 'mp4', m3u8_id='hls', live=True)
        return {
            'id': video_id,
            'title': 'bTV',
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        if mobj.group('live'):
            return self._extract_live()

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id, impersonate=True)

        player_url = self._search_regex(
            r'var\s+videoUrl\s*=\s*[\'"]([^\'"]+)[\'"]',
            webpage, 'player URL')

        player_config = self._download_json(
            urljoin('https://btvplus.bg', player_url), video_id, impersonate=True)['config']

        videojs_data = self._search_json(
            r'videojs\(["\'][^"\']+["\'],', player_config, 'videojs data',
            video_id, transform_source=js_to_json)
        formats = []
        subtitles = {}
        for src in traverse_obj(videojs_data, ('sources', lambda _, v: url_or_none(v['src']))):
            ext = mimetype2ext(src.get('type'))
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src['src'], video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                self.report_warning(f'Unknown format type {ext}{bug_reports_message()}')

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (
                strip_or_none(self._og_search_title(webpage, default=None))
                or clean_html(get_element_by_class('product-title', webpage))),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'description': self._og_search_description(webpage, default=None),
        }
