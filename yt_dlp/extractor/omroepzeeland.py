from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class OmroepZeelandIE(InfoExtractor):
    IE_NAME = 'omroepzeeland'
    IE_DESC = 'Omroep Zeeland'
    _VALID_URL = (
        r'https?://(?:www\.)?omroepzeeland\.nl/'
        r'(?:video|nieuws|sport|zeeuwse-top-40|(?:tv|radio)/aflevering/[^/?#]+)'
        r'/(?P<id>[^/?#]+)'
    )
    _PLAYER_URL = 'https://omroepzeeland.bbvms.com/p/regiogroei_zeeland_web_videoplayer/c/{}.json'
    _TESTS = [
        {
            'url': 'https://www.omroepzeeland.nl/video/ZNO260829YU/den-engelsman-en-hage-over-hun-eerste-maanden-bij-spakenburg',
            'md5': '78522c04c21ffdd8fe10f07b4a5683a8',
            'info_dict': {
                'id': '7400444',
                'ext': 'mp4',
                'display_id': 'ZNO260829YU',
                'title': 'Den Engelsman en Hage over hun eerste maanden bij Spakenburg',
                'description': 'Den Engelsman en Hage over hun eerste maanden bij Spakenburg',
                'thumbnail': r're:https://.+/omroepzeeland/media/.+\.jpg',
                'duration': 179,
                'timestamp': 1788031799,
                'upload_date': '20260829',
                'view_count': int,
            },
            'params': {
                'format': 'best[protocol^=http][ext=mp4]/best',
            },
        },
        {
            'url': 'https://www.omroepzeeland.nl/tv/aflevering/verzeeuwigd/370570352',
            'only_matching': True,
        },
        {
            'url': 'https://www.omroepzeeland.nl/radio/aflevering/zeeuwse-kamer/470564223',
            'only_matching': True,
        },
        {
            'url': 'https://www.omroepzeeland.nl/nieuws/18731977/ijscoman-herman-rijdt-na-40-jaar-zijn-laatste-rondje-op-het-strand',
            'only_matching': True,
        },
        {
            'url': 'https://www.omroepzeeland.nl/video/BBB-en-BVNL-willen-dolgraag-meedoen-aan-St-ZNO220812BJ/bbb-en-bvnl-willen-meedoen-aan-statenverkiezingen-in-zeeland',
            'only_matching': True,
        },
    ]

    def _extract_player_query(self, webpage, display_id):
        source_id = self._search_regex(r'sourceid_string:([^"\'\\]+)', webpage, 'source id', default=None)
        if not source_id:
            source_id = self._search_regex(
                r'asset\s*:\s*\{\s*id\s*:\s*["\'](?:sourceid_string:)?([^"\']+)', webpage, 'asset id', default=None,
            )
        if source_id:
            if source_id.isdigit():
                return source_id
            return source_id if source_id.startswith('sourceid_string:') else f'sourceid_string:{source_id}'

        for ld in self._yield_json_ld(webpage, display_id, fatal=False):
            types = ld.get('@type')
            if types != 'VideoObject' and 'VideoObject' not in (types or []):
                continue
            clip_id = str_or_none(ld.get('@id'))
            if clip_id:
                return clip_id

        return self._search_regex(r'omroepzeeland\.bbvms\.com/mediaclip/(\d+)', webpage, 'mediaclip id', default=None)

    def _asset_url(self, src, media_base):
        if not src:
            return None
        if src.startswith(('http://', 'https://', '//')):
            return url_or_none(src)
        return url_or_none(urljoin(media_base, src)) if media_base else None

    def _extract_formats_and_subtitles(self, clip, media_base, video_id):
        formats, subtitles = [], {}
        for asset in traverse_obj(clip, ('assets', ..., {dict})) or []:
            media_url = self._asset_url(asset.get('src'), media_base)
            if not media_url:
                continue
            ext = determine_ext(media_url)
            mediatype = str_or_none(asset.get('mediatype'))
            height = int_or_none(asset.get('height'))
            width = int_or_none(asset.get('width'))
            tbr = int_or_none(asset.get('bandwidth'))
            if ext == 'm3u8' or (mediatype or '').endswith('HLS'):
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                )
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
                continue
            is_audio = (
                ext == 'mp3'
                or (mediatype or '').startswith('MP3')
                or str(asset.get('mimetype') or '').startswith('audio/')
            )
            formats.append(
                {
                    'url': media_url,
                    'format_id': join_nonempty(mediatype, height, tbr, delim='-'),
                    'ext': ext if ext != 'unknown_video' else ('mp3' if is_audio else 'mp4'),
                    'width': width,
                    'height': height,
                    'tbr': tbr,
                    'vcodec': 'none' if is_audio else None,
                    'quality': -10 if mediatype == 'MP4_PREVIEW' else None,
                    'format_note': 'preview' if mediatype == 'MP4_PREVIEW' else None,
                },
            )

        for sub in traverse_obj(clip, ('subtitles', ..., {dict})) or []:
            sub_url = self._asset_url(sub.get('src'), media_base)
            if not sub_url:
                continue
            lang = str_or_none(sub.get('language') or sub.get('lang')) or 'nl'
            subtitles.setdefault(lang, []).append(
                {
                    'url': sub_url,
                    'ext': determine_ext(sub_url, 'vtt'),
                },
            )
        return formats, subtitles

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        player_query = self._extract_player_query(webpage, display_id)
        if not player_query:
            raise ExtractorError('No BlueBillywig media found', expected=True)

        data = self._download_json(self._PLAYER_URL.format(player_query), display_id)
        clip = traverse_obj(data, ('clipData', {dict})) or {}
        video_id = str_or_none(clip.get('id')) or display_id
        media_base = traverse_obj(data, ('publicationData', 'defaultMediaAssetPath', {url_or_none}))

        formats, subtitles = self._extract_formats_and_subtitles(clip, media_base, video_id)
        if not formats:
            self.raise_no_formats('No media assets found', expected=True, video_id=video_id)

        thumbnail = None
        for thumb in traverse_obj(clip, ('thumbnails', ..., {dict})) or []:
            thumb_url = self._asset_url(thumb.get('src'), media_base)
            if not thumb_url:
                continue
            thumbnail = thumb_url
            if thumb.get('main'):
                break

        json_ld = self._search_json_ld(webpage, display_id, default={})
        info = {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
            'is_live': clip.get('sourcetype') == 'live' or None,
            **traverse_obj(
                clip,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                    'duration': ('length', {int_or_none}),
                    'timestamp': (('publisheddate', 'createddate', 'date'), {parse_iso8601}, any),
                    'view_count': ('views', {int_or_none}),
                    'uploader': ('author', {str}),
                },
            ),
        }
        info['title'] = info.get('title') or json_ld.get('title') or self._og_search_title(webpage)
        info['description'] = (
            info.get('description') or json_ld.get('description') or self._og_search_description(webpage, default=None)
        )
        info['timestamp'] = info.get('timestamp') or json_ld.get('timestamp')
        info['duration'] = info.get('duration') or json_ld.get('duration')
        info['thumbnail'] = info.get('thumbnail') or json_ld.get('thumbnail')
        return info
