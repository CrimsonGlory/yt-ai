import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    traverse_obj,
    try_call,
    unified_strdate,
    url_or_none,
)


class RuutuIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:www\.)?(?:ruutu|supla)\.fi/(?:video|supla|audio)/|
                            static\.nelonenmedia\.fi/player/misc/embed_player\.html\?.*?\bnid=
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [
        {
            'url': 'https://www.ruutu.fi/video/100276183',
            'md5': '119a568b0f6505d1ea9a9048e45b05c9',
            'info_dict': {
                'id': '100276183',
                'ext': 'mp4',
                'title': '"Moraali alennusmyynnissä" – Tältä näyttää Selviytyjät Suomen 30.8. alkava uusi kausi!',
                'description': 'md5:db4f321d26c6071a568117bc2e71291a',
                'thumbnail': r're:^https?://.*',
                'duration': 232,
                'upload_date': '20260809',
                'series': 'Selviytyjät Suomi',
            },
            'params': {
                'format': 'http',
            },
        },
        {
            'url': 'http://www.ruutu.fi/video/2057306',
            'md5': '420e4fa40462e7d73baf375cbb59d250',
            'info_dict': {
            'id': '2057306',
            'ext': 'mp4',
            'title': 'Superpesis: katso koko kausi Ruudussa',
            'description': 'md5:bfb7336df2a12dc21d18fa696c9f8f23',
            'duration': 40,
            'thumbnail': 'md5:bfa669ac167755ab48b3dc6a0645f9e5',
            'upload_date': '20150507',
            'series': 'Superpesis',
        },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ruutu.fi/video/2058907',
            'skip': 'video gone',
            'info_dict': {
                'id': '2058907',
                'ext': 'mp4',
                'title': 'Oletko aina halunnut tietää mitä tapahtuu vain hetki ennen lähetystä? - Nyt se selvisi!',
            },
        },
        {
            'url': 'http://www.supla.fi/supla/2231370',
            'skip': 'video gone',
            'info_dict': {
                'id': '2231370',
                'ext': 'mp4',
                'title': 'Osa 1: Mikael Jungner',
            },
        },
        {
            # Episode where <SourceFile> is "NOT-USED", but has other
            # downloadable sources available.
            'url': 'http://www.ruutu.fi/video/3193728',
            'only_matching': True,
        },
        {
            # audio podcast
            'url': 'https://www.supla.fi/supla/3382410',
            'skip': 'video gone',
            'info_dict': {
                'id': '3382410',
                'ext': 'mp3',
                'title': 'Mikä ihmeen poltergeist?',
            },
        },
        {
            'url': 'http://www.supla.fi/audio/2231370',
            'only_matching': True,
        },
        {
            'url': 'https://static.nelonenmedia.fi/player/misc/embed_player.html?nid=3618790',
            'only_matching': True,
        },
        {
            # episode
            'url': 'https://www.ruutu.fi/video/3401964',
            'skip': 'video gone',
            'info_dict': {
                'id': '3401964',
                'ext': 'mp4',
                'title': 'Temptation Island Suomi - Kausi 5 - Jakso 17',
            },
        },
        {
            # premium
            'url': 'https://www.ruutu.fi/video/3618715',
            'only_matching': True,
        },
    ]
    _WEBPAGE_TESTS = [
        {
            # FIXME: Broken IE
            'url': 'https://www.hs.fi/maailma/art-2000011353059.html',
            'skip': 'hs.fi embed extraction is broken',
            'info_dict': {
                'id': '4746675',
                'ext': 'mp4',
                'title': 'Yhdysvaltojen Texasin osavaltiota ovat koetelleet tuhoisat tulvat',
            },
        },
    ]
    _API_BASE = 'https://mcc.nm-ovp.nelonenmedia.fi/v2'

    @classmethod
    def _extract_embed_urls(cls, url, webpage):
        # nelonen.fi
        settings = try_call(
            lambda: json.loads(
                re.search(r'jQuery\.extend\(Drupal\.settings, ({.+?})\);', webpage).group(1),
                strict=False,
            ),
        )
        if settings:
            video_id = traverse_obj(
                settings,
                ('mediaCrossbowSettings', 'file', 'field_crossbow_video_id', 'und', 0, 'value'),
            )
            if video_id:
                return [f'http://www.ruutu.fi/video/{video_id}']
        # hs.fi and is.fi
        settings = try_call(
            lambda: json.loads(
                re.search("(?s)<script[^>]+id=['\"]__NEXT_DATA__['\"][^>]*>([^<]+)</script>", webpage).group(1),
                strict=False,
            ),
        )
        if settings:
            video_ids = set(
                traverse_obj(
                    settings,
                    ('props', 'pageProps', 'page', 'assetData', 'splitBody', ..., 'video', 'sourceId'),
                )
                or [],
            )
            if video_ids:
                return [f'http://www.ruutu.fi/video/{v}' for v in video_ids]
            video_id = traverse_obj(settings, ('props', 'pageProps', 'page', 'assetData', 'mainVideo', 'sourceId'))
            if video_id:
                return [f'http://www.ruutu.fi/video/{video_id}']

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(f'{self._API_BASE}/media/{video_id}', video_id, expected_status=404)
        if not traverse_obj(data, 'success'):
            raise ExtractorError(traverse_obj(data, 'message') or 'Video not found', expected=True)

        clip = data['clip']
        playback = clip['playback']
        metadata = clip.get('metadata') or {}
        pv = clip.get('passthroughVariables') or {}
        stream_urls = traverse_obj(playback, ('media', 'streamUrls'), default={})

        if traverse_obj(playback, ('drm', 'enabled')):
            self.report_drm(video_id)

        formats = []
        processed_urls = set()

        def add_stream(stream, format_id):
            video_url = url_or_none(traverse_obj(stream, 'url'))
            if not video_url or video_url in processed_urls:
                return
            processed_urls.add(video_url)
            ext = determine_ext(video_url)
            if ext == 'm3u8':
                formats.extend(
                    self._extract_m3u8_formats(
                        video_url,
                        video_id,
                        'mp4',
                        entry_protocol='m3u8_native',
                        m3u8_id=format_id,
                        fatal=False,
                    ),
                )
            elif ext == 'mpd':
                # video-only and audio-only streams are of different
                # duration resulting in out of sync issue
                return
            elif ext == 'mp3' or format_id == 'audio':
                formats.append(
                    {
                        'format_id': format_id or 'audio',
                        'url': video_url,
                        'vcodec': 'none',
                    },
                )
            else:
                formats.append(
                    {
                        'format_id': format_id or ext,
                        'url': video_url,
                    },
                )

        for key, format_id in (
            ('webHls', 'hls'),
            ('apple', 'hls-apple'),
            ('audioHls', 'hls-audio'),
            ('http', 'http'),
            ('audioMp3', 'audio'),
        ):
            add_stream(stream_urls.get(key), format_id)

        if not formats:
            if metadata.get('paid') or pv.get('paid'):
                raise ExtractorError('This video is paid.', expected=True)
            if traverse_obj(playback, ('geoblock', 'enabled')):
                self.raise_geo_restricted(countries=['FI'])

        themes = pv.get('themes')
        thumbnail = traverse_obj(playback, ('media', 'images', 'thumbnail', '1920x1080'), expected_type=url_or_none)
        if not thumbnail:
            thumbnail = traverse_obj(
                playback,
                ('media', 'images', 'thumbnail', ...),
                get_all=False,
                expected_type=url_or_none,
            )

        return {
            'id': video_id,
            'title': metadata.get('programName') or pv.get('program_name'),
            'description': metadata.get('description'),
            'thumbnail': thumbnail,
            'duration': int_or_none(playback.get('runtime')) or int_or_none(pv.get('runtime')),
            'age_limit': int_or_none(metadata.get('ageLimit')),
            'upload_date': unified_strdate(traverse_obj(metadata, ('online_rights', 0, 'start_date'))),
            'series': metadata.get('seriesName') or pv.get('series_name'),
            'season_number': int_or_none(metadata.get('seasonNumber')),
            'episode_number': int_or_none(metadata.get('episodeNumber')),
            'categories': themes.split(',') if themes else None,
            'formats': formats,
        }
