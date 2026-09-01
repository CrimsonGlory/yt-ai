from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    determine_ext,
    orderedSet,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CollegeDeFranceIE(InfoExtractor):
    IE_NAME = 'college-de-france'
    IE_DESC = 'Collège de France'
    _VALID_URL = (
        r'https?://(?:www\.)?college-de-france\.fr/'
        r'(?:[a-z]{2}/)?agenda/(?:[\w-]+)/(?:[\w-]+)/(?P<id>[\w-]+)/?(?:[?#]|$)'
    )
    _TESTS = [
        {
            'url': 'https://www.college-de-france.fr/fr/agenda/cours/reproduction-et-demographie-chez-les-hominines/organisation-sociale-et-reproduction-chez-les-primates',
            'md5': '1c97b38513d6945749c5cdd088d1b18c',
            'info_dict': {
                'id': 'ATbrO9DpAaw',
                'ext': 'mp4',
                'display_id': 'organisation-sociale-et-reproduction-chez-les-primates',
                'title': 'Organisation sociale et reproduction chez les primates',
                'description': 'md5:e82f66446749bc1090c9bc8b3b87a3e4',
                'duration': 5633,
                'timestamp': 1667834659,
                'upload_date': '20221107',
                'uploader': 'Sciences de la vie - Collège de France',
                'uploader_id': '@Sciences-de-la-vie-CdF',
                'uploader_url': 'https://www.youtube.com/@Sciences-de-la-vie-CdF',
                'channel': 'Sciences de la vie - Collège de France',
                'channel_id': 'UCdhpyHOyliFNArgEaO6dAqw',
                'channel_url': 'https://www.youtube.com/channel/UCdhpyHOyliFNArgEaO6dAqw',
                'channel_follower_count': int,
                'view_count': int,
                'like_count': int,
                'age_limit': 0,
                'thumbnail': r're:https?://(?:www\.)?college-de-france\.fr/.+',
                'categories': ['Education'],
                'tags': ['Collège de France', 'Recherche fondamentale', 'Savoirs', 'Sciences de la vie'],
                'heatmap': 'count:100',
                'playable_in_embed': True,
                'availability': 'public',
                'live_status': 'not_live',
                'media_type': 'video',
                'creators': ['Jean-Jacques Hublin'],
            },
            'params': {
                'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
            },
            'add_ie': [YoutubeIE.ie_key()],
            'expected_warnings': [
                'Remote component challenge solver script',
                'No supported JavaScript runtime',
                'n challenge solving failed',
            ],
        },
        {
            'url': 'https://www.college-de-france.fr/agenda/cours/reproduction-et-demographie-chez-les-hominines/organisation-sociale-et-reproduction-chez-les-primates',
            'only_matching': True,
        },
        {
            'url': 'https://www.college-de-france.fr/en/agenda/lecture/coupled-quantum-fluids-and-josephson-junctions/from-superconducting-squid-to-atomic-squid',
            'only_matching': True,
        },
        {
            'url': 'https://www.college-de-france.fr/fr/agenda/seminaire/fluides-quantiques-couples-et-jonctions-josephson/ressources-et-applications-des-reseaux-quantiques',
            'only_matching': True,
        },
        {
            'url': 'https://www.college-de-france.fr/fr/agenda/colloque/information-flow-and-computation-in-living-systems/conclusion',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        ld_objects = []
        for ld in self._yield_json_ld(webpage, display_id, fatal=False):
            ld_objects.append(ld)
            ld_objects.extend(traverse_obj(ld, ('recordedIn', (None, ...), {dict})) or [])

        def ld_type(obj, expected):
            types = obj.get('@type')
            if isinstance(types, list):
                return expected in types
            return types == expected

        video_ld = next((obj for obj in ld_objects if ld_type(obj, 'VideoObject')), {})
        audio_ld = next((obj for obj in ld_objects if ld_type(obj, 'AudioObject')), {})
        event_ld = next((obj for obj in ld_objects if ld_type(obj, 'CourseInstance')), {})

        youtube_id = self._extract_youtube_id(webpage, video_ld)
        audio_url = url_or_none(audio_ld.get('contentUrl')) or self._search_regex(
            r'(https?://podcastfichiers\.college-de-france\.fr/[^"\'?]+)', webpage, 'audio url', default=None,
        )

        info = {
            'display_id': display_id,
            'title': (
                traverse_obj(event_ld, ('name', {str}))
                or traverse_obj(video_ld, ('name', {str}))
                or self._og_search_title(webpage, default=None)
                or self._html_extract_title(webpage)
            ),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': (
                url_or_none(video_ld.get('thumbnailUrl')) or self._og_search_thumbnail(webpage, default=None)
            ),
            'timestamp': unified_timestamp(video_ld.get('uploadDate') or event_ld.get('startDate')),
            'creators': orderedSet(traverse_obj(
                event_ld, (('director', 'performer'), (None, ...), 'name', {str}))) or None,
            'language': traverse_obj((video_ld, event_ld, audio_ld), (..., 'inLanguage', {str}), get_all=False),
        }

        if youtube_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id, url_transparent=True, **info,
            )
        if audio_url:
            return {
                'id': display_id,
                'url': audio_url,
                'ext': determine_ext(audio_url, 'm4a'),
                'vcodec': 'none',
                **info,
            }

        self.raise_no_formats('No video or audio found', expected=True, video_id=display_id)
        return {'id': display_id, **info}

    def _extract_youtube_id(self, webpage, video_ld):
        embed_url = url_or_none(video_ld.get('embedUrl'))
        if embed_url and YoutubeIE.suitable(embed_url):
            return YoutubeIE._match_id(embed_url)

        return self._search_regex(
            (
                r'\bdata-youtube-id=["\'](?P<id>[\w-]{11})',
                r'/media/oembed\?url=https%3A//youtu\.be/(?P<id>[\w-]{11})',
                r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=))(?P<id>[\w-]{11})',
            ),
            webpage,
            'youtube id',
            default=None,
            group='id',
        )
