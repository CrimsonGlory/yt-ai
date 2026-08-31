import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PlanetWissenIE(InfoExtractor):
    IE_NAME = 'planetwissen'
    IE_DESC = 'Planet Wissen'
    _VALID_URL = r'https?://(?:www\.)?planet-wissen\.de/(?:[^/?#]+/)*(?P<id>[^/?#]+)\.html'
    _TESTS = [
        {
            'url': 'https://www.planet-wissen.de/video-die-erfindungen-von-leonardo-da-vinci-100.html',
            'md5': '993c8a76cf0532cf48d929b685cc6f3c',
            'info_dict': {
                'id': 'mdb-2655543',
                'ext': 'mp4',
                'display_id': 'video-die-erfindungen-von-leonardo-da-vinci-100',
                'title': 'Die Erfindungen von Leonardo da Vinci',
                'description': 'Fahrradketten, Autogetriebe, Fallschirme – das alles würde es heutzutage ohne Leonardo da Vinci vermutlich nicht geben. Viele seiner Zeichnungen und Skizzen sind noch erhalten und seine Notizbüchern hat er in Spiegelschrift verfasst. Da Vinci gilt noch heute als Genie.',
                'thumbnail': r're:https?://.+\.jpg',
                'duration': 100,
                'timestamp': 1645525989,
                'upload_date': '20220222',
                'is_live': False,
            },
            'params': {
                'format': 'best[protocol^=http]',
            },
        },
        {
            'url': 'https://www.planet-wissen.de/sendungen/wdr/graffiti-kurz-erklaert-100.html',
            'only_matching': True,
        },
        {
            'url': 'https://www.planet-wissen.de/video-was-ist-die-nato-100.html',
            'only_matching': True,
        },
    ]

    def _extract_media_entry(self, metadata, webpage, display_id, media_id):
        tracker = traverse_obj(metadata, ('trackerData', {dict})) or {}
        video_id = traverse_obj(tracker, ('trackerClipId', {str})) or media_id
        media_resource = traverse_obj(metadata, ('mediaResource', {dict})) or {}

        formats, subtitles = [], {}
        for kind, media in media_resource.items():
            if kind == 'captionsHash' and isinstance(media, dict):
                for ext, caption_url in media.items():
                    caption_url = url_or_none(self._proto_relative_url(caption_url))
                    if not caption_url:
                        continue
                    subtitles.setdefault('de', []).append(
                        {
                            'url': caption_url,
                            'ext': determine_ext(caption_url, None) or ext,
                        },
                    )
                continue
            if kind not in ('dflt', 'alt') or not isinstance(media, dict):
                continue
            for tag_name in ('videoURL', 'audioURL'):
                raw_url = media.get(tag_name)
                if not raw_url:
                    continue
                medium_url = url_or_none(self._proto_relative_url(raw_url))
                if not medium_url:
                    continue
                ext = determine_ext(medium_url)
                if ext == 'm3u8':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        medium_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                    )
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                else:
                    formats.append(
                        {
                            'url': medium_url,
                            'format_id': kind,
                        },
                    )

        json_ld = self._search_json_ld(webpage, video_id, default={})
        return {
            'id': video_id,
            'display_id': display_id,
            'title': traverse_obj(tracker, ('trackerClipTitle', {str})) or json_ld.get('title'),
            'alt_title': traverse_obj(tracker, ('trackerClipSubcategory', {str})),
            'description': json_ld.get('description') or self._og_search_description(webpage, default=None),
            'thumbnail': url_or_none(json_ld.get('thumbnail')) or self._og_search_thumbnail(webpage),
            'duration': int_or_none(media_resource.get('duration')) or json_ld.get('duration'),
            'timestamp': json_ld.get('timestamp'),
            'upload_date': unified_strdate(tracker.get('trackerClipAirTime')) or json_ld.get('upload_date'),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': metadata.get('mediaType') == 'live',
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        entries = []
        for mobj in re.finditer(r'gseaInlineMediaData\["(?P<id>[^"]+)"\]\s*=', webpage):
            metadata = self._parse_json(webpage[mobj.end() :], display_id, fatal=False, ignore_extra=True)
            if not isinstance(metadata, dict):
                continue
            entries.append(self._extract_media_entry(metadata, webpage, display_id, mobj.group('id')))

        if len(entries) == 1:
            if not entries[0].get('formats'):
                self.raise_no_formats('No video formats found', video_id=entries[0].get('id'), expected=True)
            return entries[0]
        if len(entries) > 1:
            return self.playlist_result(entries, display_id)

        json_ld = self._search_json_ld(webpage, display_id, expected_type='VideoObject', default={})
        content_url = url_or_none(json_ld.get('url'))
        if content_url:
            json_ld.update(
                {
                    'id': display_id,
                    'display_id': display_id,
                    'url': content_url,
                },
            )
            return json_ld

        raise ExtractorError('No video found', expected=True)
