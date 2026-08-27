import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class LiveJournalIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = [
        r'https?://(?:[^.]+\.)?livejournal\.com/video/album/\d+.+?\bid=(?P<id>\d+)',
        r'https?://vc\.videos\.livejournal\.com/index/player\?(?:[^#]*\b)?(?:record_id|id)=(?P<id>[\w:-]+)',
    ]
    _TESTS = [{
        'url': 'https://vc.videos.livejournal.com/index/player?record_id=1263729',
        'md5': '7079766c3ea0c02b37a8e2af37b84c03',
        'info_dict': {
            'id': '1263729',
            'ext': 'mp4',
            'title': 'Истребители против БПЛА',
            'thumbnail': r're:https?://.*\.(?:jpg|png)',
            'duration': 69.34,
        },
    }, {
        'url': 'https://andrei-bt.livejournal.com/video/album/407/?mode=view&id=51272',
        'skip': 'Journal hosts on 81.19.74.0/24 time out from some networks',
        'info_dict': {
            'id': '1263729',
            'ext': 'mp4',
            'title': 'Истребители против БПЛА',
            'upload_date': '20190624',
            'timestamp': 1561406715,
        },
    }]

    def _extract_player_data(self, video_id, api_params):
        player_data = self._download_json(
            'https://api.vp.rambler.ru/api/v3/records/getPlayerData',
            video_id, query={
                'params': json.dumps(api_params, separators=(',', ':')),
            })
        playlist = traverse_obj(player_data, ('result', 'playList', {dict})) or {}
        m3u8_url = playlist.get('source') or playlist.get('directSource') or playlist.get('old')
        if not m3u8_url:
            raise ExtractorError('No video source found', expected=True)

        media_id = str(playlist.get('id') or video_id)
        formats = self._extract_m3u8_formats(m3u8_url, media_id, 'mp4', m3u8_id='hls')
        title = traverse_obj(playlist, ('title', {str}))
        if title:
            title = title.rsplit('.', 1)[0]
        return {
            'id': media_id,
            'formats': formats,
            'title': title,
            **traverse_obj(playlist, {
                'thumbnail': (('customScreenshotOrig', 'snapshot'), {url_or_none}, any),
            }),
            'duration': float_or_none(playlist.get('duration'), scale=1000),
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        api_params = {
            'checkReferrerCount': True,
            'referrer': url,
        }

        if 'vc.videos.livejournal.com' in url:
            if display_id.isdigit():
                api_params['id'] = int(display_id)
            else:
                api_params['uuid'] = (
                    display_id if display_id.startswith('record::')
                    else f'record::{display_id}')
            return self._extract_player_data(display_id, api_params)

        webpage = self._download_webpage(url, display_id)
        record = self._parse_json(self._search_regex(
            r'Site\.page\s*=\s*({.+?});', webpage,
            'page data'), display_id)['video']['record']
        uuid = record.get('uuid')
        if uuid:
            api_params['uuid'] = uuid if str(uuid).startswith('record::') else f'record::{uuid}'
        else:
            api_params['id'] = int(record['storageid'])
        if record.get('player_template_id') is not None:
            api_params['playerTemplateId'] = record['player_template_id']

        info = self._extract_player_data(display_id, api_params)
        title = record.get('name')
        if title:
            title = title.rsplit('.', 1)[0]
        info.update({
            'title': info.get('title') or title,
            'thumbnail': info.get('thumbnail') or url_or_none(
                record.get('screenshot') or record.get('thumbnail')),
            'timestamp': int_or_none(record.get('timecreate')),
        })
        return info
