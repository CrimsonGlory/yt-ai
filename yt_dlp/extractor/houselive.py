import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_qs,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class HouseLiveIE(InfoExtractor):
    IE_NAME = 'live.house.gov'
    IE_DESC = 'U.S. House of Representatives Floor Proceedings'
    _VALID_URL = r'https?://(?:www\.)?live\.house\.gov/?(?:[?#]|$)'
    _API_BASE = 'https://liveproxy-azapp-prod-eastus2-003.azurewebsites.net'
    _TESTS = [{
        'url': 'https://live.house.gov/?date=20260827',
        'md5': '1fedc6aa3c3f27880895a3733e30bad0',
        'info_dict': {
            'id': '20260827',
            'ext': 'mp4',
            'title': 'LEGISLATIVE DAY OF AUGUST 27, 2026',
            'description': 'Pursuant to Title 17 Section 105 of the United States Code, this file is not subject to copyright protection and is in the public domain.',
            'language': 'en-us',
            'upload_date': '20260827',
            'is_live': False,
            'live_status': 'was_live',
            'subtitles': 'count:1',
        },
        # HLS --test only fetches the fMP4 init fragment (~679B), below the default 10KB check
        'file_minsize': None,
        'params': {'format': 'hls-3128'},
    }, {
        'url': 'https://live.house.gov/?date=2026-08-27',
        'only_matching': True,
    }, {
        'url': 'https://live.house.gov/',
        'only_matching': True,
    }, {
        'url': 'https://live.house.gov',
        'only_matching': True,
    }]

    def _sanitize_date_id(self, value):
        if not value:
            return None
        date_id = value.replace('-', '')
        return date_id if re.fullmatch(r'\d{8}', date_id) else None

    def _media_url(self, files, media_type):
        for file in files:
            if (file.get('type') or '').lower() != media_type:
                continue
            media_url = url_or_none((file.get('url') or '').split('#')[0])
            if media_url:
                return media_url

    def _download_broadcast(self, date_id, video_id):
        events = self._download_json(
            f'{self._API_BASE}/broadcastevents/{date_id}', video_id,
            'Downloading broadcast JSON', fatal=False)
        if isinstance(events, dict):
            return events if events.get('asset') else None
        return traverse_obj(events, (0, {dict}))

    def _resolve_broadcast(self, url):
        date_id = self._sanitize_date_id(traverse_obj(parse_qs(url), ('date', -1)))
        if date_id:
            event = self._download_broadcast(date_id, date_id)
            if not event:
                raise ExtractorError(
                    f'No House floor video is available for {date_id}', expected=True)
            return date_id, event

        floor = self._download_json(
            f'{self._API_BASE}/floor/', 'live', 'Downloading floor JSON')
        history = self._download_json(
            f'{self._API_BASE}/latest/history', 'live',
            'Downloading session status', fatal=False)
        last_id = self._sanitize_date_id(traverse_obj(floor, ('_id', {str})))
        next_start = traverse_obj(floor, ('nextStartDate', {str}))
        next_id = self._sanitize_date_id(next_start[:10] if next_start else None)
        candidates = []
        if history and history.get('inSession') is True and next_id:
            candidates.append(next_id)
        if last_id and last_id not in candidates:
            candidates.append(last_id)
        if not candidates:
            raise ExtractorError(
                'Unable to determine the current House legislative day', expected=True)

        for candidate in candidates:
            event = self._download_broadcast(candidate, candidate)
            if event:
                return candidate, event

        raise ExtractorError(
            'The House floor stream is not currently available', expected=True)

    def _real_extract(self, url):
        video_id, event = self._resolve_broadcast(url)
        files = traverse_obj(event, ('asset', 'files', ..., {dict})) or []
        hls_url = self._media_url(files, 'hls')
        dash_url = self._media_url(files, 'dash')
        caption_url = self._media_url(files, 'webvtt')

        formats, subtitles = [], {}
        if hls_url:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
        if dash_url:
            dash_fmts, dash_subs = self._extract_mpd_formats_and_subtitles(
                dash_url, video_id, mpd_id='dash', fatal=False)
            formats.extend(dash_fmts)
            self._merge_subtitles(dash_subs, target=subtitles)
        if caption_url:
            self._merge_subtitles(
                {'en': [{'url': caption_url, 'ext': 'vtt'}]}, target=subtitles)
        if not formats:
            self.raise_no_formats(
                'No House floor video formats were found', expected=True, video_id=video_id)

        is_live = (event.get('isLiveBroadcast') or '').lower() == 'true'

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            'live_status': 'is_live' if is_live else 'was_live',
            'upload_date': video_id,
            **traverse_obj(event, {
                'title': ('name', {str}),
                'description': ('rights', {str}),
                'language': ('inLanguage', {str}),
            }),
        }
