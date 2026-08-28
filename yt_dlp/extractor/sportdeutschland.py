from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    join_nonempty,
    strip_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class SportDeutschlandIE(InfoExtractor):
    IE_NAME = 'sporteurope'
    _VALID_URL = r'https?://(?:player\.)?sporteurope\.tv/(?P<id>(?:[^/?#]+/)?[^?#/&]+)'
    _TESTS = [{
        # Single-part video, direct link
        'url': 'https://sporteurope.tv/rostock-griffins/gfl2-rostock-griffins-vs-elmshorn-fighting-pirates',
        'skip': 'video gone',
        'md5': '35c11a19395c938cdd076b93bda54cde',
        'info_dict': {
            'id': '9f27a97d-1544-4d0b-aa03-48d92d17a03a',
            'ext': 'mp4',
            'title': 'GFL2: Rostock Griffins vs. Elmshorn Fighting Pirates',
            'display_id': 'rostock-griffins/gfl2-rostock-griffins-vs-elmshorn-fighting-pirates',
            'channel': 'Rostock Griffins',
            'channel_url': 'https://sporteurope.tv/rostock-griffins',
            'live_status': 'was_live',
            'description': r're:Video-Livestream des Spiels Rostock Griffins vs\. Elmshorn Fighting Pirates.+',
            'channel_id': '9635f21c-3f67-4584-9ce4-796e9a47276b',
            'timestamp': 1749913117,
            'upload_date': '20250614',
            'duration': 12287.0,
        },
    }, {
        # Single-part video, embedded player link
        'url': 'https://player.sporteurope.tv/9e9619c4-7d77-43c4-926d-49fb57dc06dc',
        'skip': 'video gone',
        'info_dict': {
            'id': '9f27a97d-1544-4d0b-aa03-48d92d17a03a',
            'ext': 'mp4',
            'title': 'GFL2: Rostock Griffins vs. Elmshorn Fighting Pirates',
            'display_id': '9e9619c4-7d77-43c4-926d-49fb57dc06dc',
            'channel': 'Rostock Griffins',
            'channel_url': 'https://sporteurope.tv/rostock-griffins',
            'live_status': 'was_live',
            'description': r're:Video-Livestream des Spiels Rostock Griffins vs\. Elmshorn Fighting Pirates.+',
            'channel_id': '9635f21c-3f67-4584-9ce4-796e9a47276b',
            'timestamp': 1749913117,
            'upload_date': '20250614',
            'duration': 12287.0,
        },
        'params': {'skip_download': True},
    }, {
        # Multi-part video
        'url': 'https://sporteurope.tv/rhine-ruhr-2025-fisu-world-university-games/volleyball-w-japan-vs-brasilien-halbfinale-2',
        'info_dict': {
            'id': '9f63d737-2444-4e3a-a1ea-840df73fd481',
            'display_id': 'rhine-ruhr-2025-fisu-world-university-games/volleyball-w-japan-vs-brasilien-halbfinale-2',
            'title': 'Volleyball w: Japan vs. Braslien - Halbfinale 2',
            'description': 'md5:0a17da15e48a687e6019639c3452572b',
            'channel': 'Rhine-Ruhr 2025 FISU World University Games',
            'channel_id': '9f5216be-a49d-470b-9a30-4fe9df993334',
            'channel_url': 'https://sporteurope.tv/rhine-ruhr-2025-fisu-world-university-games',
            'live_status': 'was_live',
        },
        'playlist_count': 2,
        'playlist': [{
            'info_dict': {
                'id': '9f725a94-d43e-40ff-859d-13da3081bb04',
                'ext': 'mp4',
                'title': 'Volleyball w: Japan vs. Braslien - Halbfinale 2 Part 1',
                'channel': 'Rhine-Ruhr 2025 FISU World University Games',
                'channel_id': '9f5216be-a49d-470b-9a30-4fe9df993334',
                'channel_url': 'https://sporteurope.tv/rhine-ruhr-2025-fisu-world-university-games',
                'duration': 14773.0,
                'timestamp': 1753085197,
                'upload_date': '20250721',
                'live_status': 'was_live',
            },
        }, {
            'info_dict': {
                'id': '9f725a94-370e-4477-89ac-1751098e3217',
                'ext': 'mp4',
                'title': 'Volleyball w: Japan vs. Braslien - Halbfinale 2 Part 2',
                'channel': 'Rhine-Ruhr 2025 FISU World University Games',
                'channel_id': '9f5216be-a49d-470b-9a30-4fe9df993334',
                'channel_url': 'https://sporteurope.tv/rhine-ruhr-2025-fisu-world-university-games',
                'duration': 14773.0,
                'timestamp': 1753128421,
                'upload_date': '20250721',
                'live_status': 'was_live',
            },
        }],
        'skip': '404 Not Found',
    }, {
        # Public VOD (former livestream)
        'url': 'https://sporteurope.tv/dtb/gymnastik-international-tag-1',
        'md5': 'f99c9f5f1f327c0c750e3e9501f52d4c',
        'info_dict': {
            'id': '986bb51d-a251-45a9-8b85-1f6a6c902a81',
            'ext': 'mp4',
            'title': 'Gymnastik International - Tag 1',
            'display_id': 'dtb/gymnastik-international-tag-1',
            'channel_id': '936ecef1-2f4a-4e08-be2f-68073cb7ecab',
            'channel': 'Deutscher Turner-Bund',
            'channel_url': 'https://sporteurope.tv/dtb',
            'description': 'md5:53ff7d266a6f7e5e2200e6eb08635a91',
            'live_status': 'was_live',
            'duration': 36062.0,
            'timestamp': 1677918300,
            'upload_date': '20230304',
            'thumbnail': r're:https://img-cdn\.do\.sporteurope\.tv/.+',
        },
    }]

    def _extract_source(self, source, video_id, is_live):
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            source['hls'], video_id, 'mp4', m3u8_id='hls', live=is_live)
        return {
            'id': source.get('id') or video_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': float_or_none(source.get('duration')),
            'is_live': is_live,
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        meta = self._download_json(
            f'https://api.sporteurope.tv/api/web/public/assets/{display_id}',
            display_id, headers={'Referer': 'https://sporteurope.tv/'})
        asset_id = meta['id']
        is_live = bool(meta.get('currently_live'))

        playback = self._download_json(
            f'https://api.sporteurope.tv/api/web-player/personal/assets/{asset_id}',
            asset_id, headers={
                'Origin': 'https://sporteurope.tv',
                'Referer': 'https://sporteurope.tv/',
                'x-version': '2',
            }, expected_status=(401, 403, 451))

        error = traverse_obj(playback, ('error', {str}))
        if error == 'CONTENT_NOT_ALLOWED_FOR_REGION':
            self.raise_geo_restricted(countries=traverse_obj(
                meta, ('access_only_from_countries', ..., {str})))
        elif error in ('CONTENT_CURRENTLY_NOT_PURCHASED', 'LOGIN_REQUIRED'):
            self.raise_login_required(metadata_available=True)
        elif error:
            raise ExtractorError(
                traverse_obj(playback, ('message', {str})) or error, expected=True)

        info = {
            'display_id': display_id,
            'is_live': is_live,
            **traverse_obj(meta, {
                'id': 'id',
                'title': (('name', 'title'), {strip_or_none}),
                'description': ('description', {clean_html}),
                'channel': ('profile', 'name'),
                'channel_id': ('profile', 'id'),
                'was_live': 'was_live',
                'channel_url': ('profile', 'slug', {lambda x: f'https://sporteurope.tv/{x}'}),
                'duration': ('duration_in_seconds', {float_or_none}),
                'timestamp': ('content_start_date', {unified_timestamp}),
            }, get_all=False),
            'thumbnail': traverse_obj(playback, ('images', -1, 'src', {url_or_none})),
        }

        tracks = traverse_obj(playback, ('tracks', ...)) or []
        primary = next((t for t in tracks if t.get('is_primary')), None) or (
            tracks[0] if tracks else None)
        sources = [s for s in traverse_obj(primary, ('sources', ...)) or [] if url_or_none(s.get('hls'))]
        if not sources:
            self.raise_no_formats('No playable sources', expected=True, video_id=asset_id)

        entries = [{
            'title': source.get('title') or join_nonempty(info.get('title'), f'Part {i}', delim=' '),
            **traverse_obj(info, {
                'channel': 'channel', 'channel_id': 'channel_id',
                'channel_url': 'channel_url', 'was_live': 'was_live',
            }),
            **self._extract_source(source, source.get('id') or f'{asset_id}-{i}', is_live),
        } for i, source in enumerate(sources, 1)]

        return {
            '_type': 'multi_video',
            **info,
            'entries': entries,
        } if len(entries) > 1 else {
            **info,
            **entries[0],
            'id': info.get('id'),
            'title': info.get('title'),
        }
