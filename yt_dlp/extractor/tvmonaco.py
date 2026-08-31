from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
    str_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class TVMonacoIE(InfoExtractor):
    IE_DESC = 'TVMonaco'
    _VALID_URL = r'https?://(?:www\.)?(?:videos\.)?tvmonaco\.com/content/(?P<id>[^/?#]+)'
    _API_ORIGIN = 'https://videos.tvmonaco.com'
    _TESTS = [
        {
            'url': 'https://videos.tvmonaco.com/content/monaco-mon-histoire-le-musee-danthropologie-prehistorique-de-monaco',
            'md5': 'b1ea8337303456bff2c91cffc877ff9d',
            'info_dict': {
                'id': 'c373fb72-91d6-41f8-a0de-b2b2a88b89e0',
                'ext': 'mp4',
                'display_id': 'monaco-mon-histoire-le-musee-danthropologie-prehistorique-de-monaco',
                'title': "LE MUSÉE D'ANTHROPOLOGIE PRÉHISTORIQUE DE MONACO",
                'description': 'md5:6eeab6b42112963dfb3d0629dc47cf5c',
                'thumbnail': r're:https://production\.content\.okast\.tv/.+',
                'duration': 164,
                'timestamp': 1773486600,
                'upload_date': '20260314',
                'release_date': '20250101',
                'language': 'fr',
                'genres': ['Documentaire'],
                'tags': ['Histoire'],
                'series_id': 'bda359d8-759d-46d4-8e42-0529421f814e',
            },
        },
        {
            'url': 'https://videos.tvmonaco.com/content/c373fb72-91d6-41f8-a0de-b2b2a88b89e0/monaco-mon-histoire-le-musee-danthropologie-prehistorique-de-monaco',
            'only_matching': True,
        },
        {
            'url': 'https://tvmonaco.com/content/monaco-mon-histoire-le-musee-danthropologie-prehistorique-de-monaco',
            'only_matching': True,
        },
    ]

    def _api_headers(self):
        return {
            'Accept': 'application/json',
            'Origin': self._API_ORIGIN,
            'Referer': f'{self._API_ORIGIN}/',
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        media = self._download_json(
            f'{self._API_ORIGIN}/api/media/v7/media/{display_id}', display_id, headers=self._api_headers(),
        )
        video_id = traverse_obj(media, ('uuid', {str})) or display_id
        translation = (
            traverse_obj(media, ('translations', lambda _, v: v.get('default') is True, any))
            or traverse_obj(media, ('translations', 0, {dict}))
            or {}
        )

        if media.get('is_coming_soon'):
            self.raise_no_formats('This video is not yet available', expected=True, video_id=video_id)

        playback = self._download_json(
            f'{self._API_ORIGIN}/api/offer/v4/media/{video_id}/url',
            video_id,
            'Downloading playback JSON',
            headers=self._api_headers(),
            expected_status=(400, 401, 403, 404),
            transform_source=lambda s: s or '{}',
        )
        source = traverse_obj(playback, ('source', {url_or_none}))
        if not source:
            if media.get('free') is False or media.get('is_tvod'):
                self.raise_login_required('This video is not available without a subscription')
            self.raise_no_formats('No video source available', expected=True, video_id=video_id)

        media_type = playback.get('media_type') or media.get('type') or ''
        is_live = media.get('type') == 'live' or str(media_type).endswith('_live')
        is_audio = media.get('audio_only') or str(media_type).startswith('audio')
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            source,
            video_id,
            'm4a' if is_audio else 'mp4',
            m3u8_id='hls',
            live=is_live,
            headers={'Referer': f'{self._API_ORIGIN}/'},
        )

        for subtitle in traverse_obj(playback, ('subtitles', ..., {dict})):
            sub_url = url_or_none(subtitle.get('url') or subtitle.get('src'))
            if not sub_url:
                continue
            subtitles.setdefault(subtitle.get('language') or subtitle.get('lang') or 'und', []).append(
                {
                    'url': sub_url,
                },
            )

        return {
            'id': video_id,
            'display_id': traverse_obj(translation, ('slug', {str})) or display_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            **traverse_obj(
                translation,
                {
                    'title': ('name', {str}),
                    'description': (('description', 'short_description'), {str}, any),
                    'language': ('language', {str}),
                    'thumbnail': (
                        'picture',
                        (
                            'cover_picture_16_9',
                            'cover_picture_16_6',
                            'cover_picture_1_1',
                        ),
                        'url',
                        {url_or_none},
                        any,
                    ),
                },
            ),
            **traverse_obj(
                media,
                {
                    'duration': ('duration', {int_or_none}),
                    'timestamp': (('begin_date', 'publication_date'), {parse_iso8601}, any),
                    'release_date': ('production_date', {unified_strdate}),
                    'genres': ('new_genre', 'translations', lambda _, v: v.get('default') is True, 'title', {str}, all),
                    'tags': ('themes', ..., 'translations', lambda _, v: v.get('default') is True, 'title', {str}),
                    'series_id': ('seasons', 0, {str_or_none}),
                },
            ),
        }
