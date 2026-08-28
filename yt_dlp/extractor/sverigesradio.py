import re

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


class SverigesRadioBaseIE(InfoExtractor):
    _EXT_TO_CODEC_MAP = {
        'mp3': 'mp3',
        'm4a': 'aac',
    }

    def _extract_audio_formats(self, *sources):
        formats, urls = [], set()

        def add(audio_url, format_id=None, bitrate=None):
            audio_url = url_or_none(audio_url)
            if not audio_url or audio_url in urls:
                return
            urls.add(audio_url)
            ext = determine_ext(audio_url, default_ext='m4a')
            formats.append(
                {
                    'abr': int_or_none(bitrate, scale=1000),
                    'acodec': self._EXT_TO_CODEC_MAP.get(ext),
                    'ext': ext,
                    'format_id': format_id or ext,
                    'url': audio_url,
                    'vcodec': 'none',
                },
            )

        for source in sources:
            if not isinstance(source, dict):
                continue
            for quality, quality_data in (source.get('qualities') or {}).items():
                if isinstance(quality_data, dict):
                    add(quality_data.get('url'), quality, quality_data.get('bitrate'))
            for fmt_id, fmt_data in (source.get('formats') or {}).items():
                if isinstance(fmt_data, dict):
                    add(fmt_data.get('url'), fmt_id, fmt_data.get('bitrate'))
            add(source.get('url') or source.get('src'), bitrate=source.get('bitrate'))
        return formats

    def _real_extract(self, url):
        audio_id, display_id = self._match_valid_url(url).group('id', 'slug')
        video_id = audio_id or display_id
        webpage = self._download_webpage(url, video_id)
        item = (
            traverse_obj(
                self._search_nextjs_v13_data(webpage, video_id, fatal=False), (..., ('article', 'episode'), {dict}, any),
            )
            or {}
        )
        audio_id = str(traverse_obj(item, 'id') or audio_id or display_id)

        formats = self._extract_audio_formats(
            traverse_obj(item, ('playAudio', {dict})),
            traverse_obj(item, ('audio', 'podcast', {dict})),
            traverse_obj(item, ('audio', 'broadcast', {dict})),
            traverse_obj(item, ('playerInformation', 'audio', {dict})),
        )

        if not formats and audio_id.isdigit() and self._AUDIO_TYPE == 'episode':
            episode = (
                traverse_obj(
                    self._download_json(
                        'https://api.sr.se/api/v2/episodes/get',
                        audio_id,
                        'Downloading episode JSON metadata',
                        fatal=False,
                        query={'id': audio_id, 'format': 'json'},
                    ),
                    ('episode', {dict}),
                )
                or {}
            )
            if not item:
                item = episode
            formats = self._extract_audio_formats(
                traverse_obj(episode, ('listenpodfile', {dict})),
                traverse_obj(episode, ('downloadpodfile', {dict})),
                *traverse_obj(episode, ('broadcast', 'broadcastfiles', ..., {dict}), default=[]),
            )

        if not formats:
            formats = self._extract_audio_formats(
                *(
                    {'url': audio_url}
                    for audio_url in dict.fromkeys(
                        re.findall(r'https?://(?:www\.)?sverigesradio\.se/topsy/ljudfil/[^\s"\\]+', webpage),
                    )
                ),
            )

        if not formats:
            raise ExtractorError('Unable to extract audio formats', expected=True)

        info = {
            'id': audio_id,
            'formats': formats,
            **traverse_obj(
                item,
                {
                    'title': (('title', 'soundName', 'originalTitle'), any, {str}),
                    'series': (('programName', ('program', 'name')), any, {str}),
                    'duration': (
                        (
                            ('playAudio', 'duration'),
                            'duration',
                            ('audio', 'podcast', 'duration'),
                            ('playerInformation', 'duration'),
                            ('listenpodfile', 'duration'),
                            ('downloadpodfile', 'duration'),
                        ),
                        any,
                        {int_or_none},
                    ),
                    'thumbnail': (
                        (
                            ('images', 0, 'url'),
                            ('images', 0, 'imageUrl'),
                            ('image', 'imageUrl'),
                            ('playerInformation', 'imageSrc'),
                            ('program', 'wideImage', 'imageUrl'),
                            'imageurl',
                        ),
                        any,
                        {url_or_none},
                    ),
                    'description': (
                        (
                            ('textHtml', {clean_html}),
                            ('description', {str}),
                            ('fullDescription', {clean_html}),
                            ('subtitle', {str}),
                            ('text', {str}),
                        ),
                        filter,
                        any,
                    ),
                    'timestamp': (('publishUTC', 'publishUtc'), any, {parse_iso8601}),
                },
            ),
        }
        if not info.get('title'):
            info['title'] = self._og_search_title(webpage, default=None)
        return info


class SverigesRadioPublicationIE(SverigesRadioBaseIE):
    IE_NAME = 'sverigesradio:publication'
    _VALID_URL = r'https?://(?:www\.)?sverigesradio\.se/(?:sida/)?(?:artikel|gruppsida)(?:\.aspx\?.*?\bartikel=(?P<id>[0-9]+)|/(?P<slug>[\w-]+))'
    _TESTS = [
        {
            'url': 'https://sverigesradio.se/sida/artikel.aspx?programid=83&artikel=7038546',
            'skip': 'video gone',
            'md5': '6a4917e1923fccb080e5a206a5afa542',
            'info_dict': {
                'id': '7038546',
                'ext': 'm4a',
                'duration': 132,
                'series': 'Nyheter (Ekot)',
                'title': 'Esa Teittinen: Sanningen har inte kommit fram',
                'description': 'md5:daf7ce66a8f0a53d5465a5984d3839df',
                'thumbnail': r're:^https?://.*\.jpg',
            },
        },
        {
            'url': 'https://sverigesradio.se/artikel/tysk-fotbollsfeber-bayern-munchens-10-ariga-segersvit-kan-brytas',
            'md5': 'f8a914ad50f491bb74eed403ab4bfef6',
            'info_dict': {
                'id': '8360345',
                'ext': 'm4a',
                'title': 'Tysk fotbollsfeber när Bayern Münchens 10-åriga segersvit kan brytas',
                'series': 'Radiosporten',
                'description': 'md5:868e8e184e6c3c5a83d5e3d254674928',
                'duration': 72,
                'thumbnail': r're:^https?://.*\.jpg',
                'timestamp': 1685183940,
                'upload_date': '20230527',
            },
        },
        {
            'url': 'https://sverigesradio.se/sida/gruppsida.aspx?programid=3304&grupp=6247&artikel=7146887',
            'only_matching': True,
        },
    ]
    _AUDIO_TYPE = 'publication'


class SverigesRadioEpisodeIE(SverigesRadioBaseIE):
    IE_NAME = 'sverigesradio:episode'
    _VALID_URL = r'https?://(?:www\.)?sverigesradio\.se/(?:sida/)?avsnitt/(?:(?P<id>\d+)|(?P<slug>[\w-]+))(?:$|[#?])'
    _TESTS = [
        {
            'url': 'https://sverigesradio.se/avsnitt/1140922?programid=1300',
            'md5': '20dc4d8db24228f846be390b0c59a07c',
            'info_dict': {
                'id': '1140922',
                'ext': 'mp3',
                'duration': 3307,
                'series': 'Konflikt',
                'title': 'Metoo och valen',
                'description': 'md5:fcb5c1f667f00badcc702b196f10a27e',
                'thumbnail': r're:^https?://.*\.jpg',
            },
        },
        {
            'url': 'https://sverigesradio.se/avsnitt/p4-live-med-first-aid-kit-scandinavium-mars-2023',
            'skip': 'video gone',
            'md5': 'ce17fb82520a8033dbb846993d5589fe',
            'info_dict': {
                'id': '2160416',
                'ext': 'm4a',
                'title': 'P4 Live med First Aid Kit',
                'description': 'md5:6d5b78eed3d2b65f6de04daa45e9285d',
                'thumbnail': r're:^https?://.*\.jpg',
                'series': 'P4 Live',
                'duration': 5640,
            },
        },
    ]
    _AUDIO_TYPE = 'episode'
