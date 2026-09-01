import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CaracolRadioIE(InfoExtractor):
    IE_DESC = 'Caracol Radio'
    _VALID_URL = r'https?://(?:www\.)?caracol\.com\.co/audio/(?:podium/)?(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://caracol.com.co/audio/1787872686_739_cut/',
        'md5': 'ceb375508e2d4884a896cfbf2e3ec659',
        'info_dict': {
            'id': '1787872686_739_cut',
            'ext': 'mp3',
            'title': 'MinHacienda explica aumento de Presupuesto 2027: incluye pagos que gobierno Petro no habría incluido',
            'duration': 52,
            'timestamp': 1787872680,
            'upload_date': '20260827',
            'series': 'La Luciérnaga',
            'series_id': 'a94a355c-fcf1-5d6f-810e-e17752f95a9f',
            'thumbnail': 'https://caracol.com.co/especiales/podcasts/images/podcast-laluciernaga-2024.jpg',
            'vcodec': 'none',
        },
    }, {
        'url': 'https://caracol.com.co/audio/1769462430868/',
        'only_matching': True,
    }, {
        'url': 'https://caracol.com.co/audio/podium/f4fe6bf2-1911-42a2-b902-b45001241bfa/',
        'only_matching': True,
    }, {
        'url': 'https://caracol.com.co/audio/caracol_radio_6amw_20260818_080000_090000/',
        'only_matching': True,
    }]

    def _download_episode(self, url, audio_id):
        is_podium = '/audio/podium/' in url
        query = {
            'uri': f'/audio/{"podium/" if is_podium else ""}{audio_id}/',
            'idrefs': audio_id,
            'accountNameId': 'podium' if is_podium else 'caracol',
            'mediaType': 'audio',
            'arc-site': 'caracol-colombia',
        }
        if is_podium:
            query['mediaId'] = audio_id

        data = self._download_json(
            'https://caracol.com.co/pf/api/v3/content/fetch/mediateca-info',
            audio_id, query={
                'query': json.dumps(query, separators=(',', ':')),
                '_website': 'caracol-colombia',
            }, fatal=False)
        episode = traverse_obj(data, (0, {dict}))
        if episode:
            return episode

        webpage = self._download_webpage(url, audio_id)
        app_data = self._search_json(
            r'window\.appData\s*=', webpage, 'app data', audio_id)
        return traverse_obj(app_data, ('globalContent', '0', {dict})) or {}

    def _extract_formats(self, episode):
        seen, uds, other = set(), [], []
        for asset in traverse_obj(episode, ('asset', ..., {dict})) or []:
            mime = (asset.get('mimetype') or '').lower()
            for media in traverse_obj(asset, ('url', ..., {dict})) or []:
                type_name = traverse_obj(media, ('type_url', 'name', {str})) or ''
                if type_name.upper() == 'IMAGE':
                    continue
                media_url = url_or_none(media.get('url'))
                if not media_url or media_url in seen or 'accessToken=' in media_url:
                    continue
                ext = determine_ext(media_url, 'mp3')
                if not (mime.startswith('audio') or ext in ('mp3', 'm4a', 'aac')):
                    continue
                seen.add(media_url)
                fmt = {
                    'url': media_url,
                    'format_id': type_name.lower() or 'audio',
                    'ext': ext,
                    'vcodec': 'none',
                    'abr': int_or_none(asset.get('bitrate')) or None,
                }
                (uds if type_name.upper() == 'UDS' else other).append(fmt)
        return uds or other

    def _real_extract(self, url):
        audio_id = self._match_id(url)
        episode = self._download_episode(url, audio_id)
        formats = self._extract_formats(episode)
        if not formats:
            raise ExtractorError('Unable to extract audio URL', expected=True)

        return {
            'id': audio_id,
            'formats': formats,
            **traverse_obj(episode, {
                'title': ('name', {str}),
                'description': ('description', {clean_html}),
                'thumbnail': ((
                    'url_thumbnail', 'url_audio_still',
                    ('podcast_data', 'images', ..., 'url'),
                ), {url_or_none}, any),
                'timestamp': ('publication_date_start', {parse_iso8601}),
                'duration': ('length', {int_or_none(scale=1000)}),
                'uploader': ('author', {str}),
                'season_number': ('season', {int_or_none}),
                'episode_number': ('chapter', {int_or_none}),
                'series': ('tags', lambda _, v: v.get('type') == 'P', 'description', {str}, any),
                'series_id': ('podcast_data', 'id', {str}),
            }),
        }
