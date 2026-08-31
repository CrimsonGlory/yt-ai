from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    parse_resolution,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class WeltIE(InfoExtractor):
    IE_NAME = 'welt'
    IE_DESC = 'WELT Mediathek'
    _VALID_URL = r'https?://(?:www\.)?welt\.de/(?:[^?#]+/)?(?:sendung|video)(?P<id>[0-9a-f]{24}|\d+)'
    _TESTS = [{
        'url': 'https://www.welt.de/mediathek/dokumentation/space/strip-the-cosmos/sendung218509518/Strip-the-Cosmos-Geheimnisvoller-Jupiter.html',
        'md5': '6570fa1d1a2bdbb92d445a5a2889430c',
        'info_dict': {
            'id': '218509518',
            'ext': 'mp4',
            'title': 'Strip the Cosmos: Geheimnisvoller Jupiter',
            'description': 'Auf dem Gasriesen Jupiter wüten gigantische Stürme und monströse Magnetfelder, sein Kern ist heißer als die Oberfläche der Sonne. Neue Erkenntnisse über den planetaren Platzhirsch.',
            'thumbnail': r're:https?://images\.welt\.de/.+',
            'duration': 2823,
            'timestamp': 1604657386,
            'upload_date': '20201106',
            'uploader': 'WELT TV',
            'series': 'Strip the Cosmos',
        },
    }, {
        'url': 'https://www.welt.de/mediathek/serie/sendung218509518/Strip-the-Cosmos-Geheimnisvoller-Jupiter.html',
        'only_matching': True,
    }, {
        'url': 'https://www.welt.de/videos/video6a8e6606c3692834ff6dcc8f/auch-auf-produkte-mit-suessungsmitteln-streit-um-zuckersteuer-ricarda-lang-nennt-plaene-schwachsinn-klingbeil-rudert-zurueck.html',
        'only_matching': True,
    }, {
        'url': 'https://www.welt.de/mediathek/dokumentation/history/sendung256240590/video-geheimakte-atombombe-luegen-und-verrat.html',
        'only_matching': True,
    }]

    def _extract_player_sources(self, sources, video_id, is_live):
        formats, subtitles = [], {}
        for src in traverse_obj(sources, (..., 'src', {url_or_none})):
            ext = determine_ext(src)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', m3u8_id='hls', fatal=False, live=is_live)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                continue
            tbr = int_or_none(self._search_regex(
                r'_(\d+)\.(?:mp4|webm)', src, 'tbr', default=None))
            height = parse_resolution(src).get('height') or int_or_none(
                self._search_regex(r'v(\d+)p', src, 'height', default=None))
            formats.append({
                'url': src,
                'ext': ext or 'mp4',
                'tbr': tbr,
                'height': height,
                'format_id': join_nonempty('http', tbr or height),
            })
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player = self._search_json(
            r'<script[^>]+data-internal-ref="WeltVideoPlayer[^"]*"[^>]*>',
            webpage, 'player', video_id, end_pattern=r'</script>', default={})
        welt_config = self._search_json(
            r'window\["weltConfig"\]\s*=', webpage, 'welt config',
            video_id, end_pattern=r'</script>', default={})
        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld_url = json_ld.pop('url', None)
        json_ld.pop('formats', None)

        video_type = traverse_obj(player, ('trackingConfig', 'videoType', {dict})) or {}
        is_live = any(video_type.get(key) for key in (
            'isEventLivestream', 'isTelevisionLivestream',
            'isN24DokuLivestream', 'isWeltNachrichtenImTvStream',
        )) or bool(traverse_obj(player, ('trackingData', 'livestreamType')))

        formats, subtitles = self._extract_player_sources(
            traverse_obj(player, ('sources', ..., {dict})) or [], video_id, is_live)

        if not formats:
            for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
                formats.extend(entry.get('formats') or [])
                if entry.get('url'):
                    formats.append({'url': entry['url']})
                self._merge_subtitles(entry.get('subtitles') or {}, target=subtitles)

        if not formats and json_ld_url:
            formats.append({'url': json_ld_url})

        if not formats:
            if traverse_obj(player, ('trackingData', 'isPremium', {bool})) or welt_config.get('isPremium'):
                self.raise_login_required(
                    'This video is only available for WELT subscribers', metadata_available=True)
            if 'lizenzrechtlichen Gründen nicht verfügbar' in webpage:
                self.raise_no_formats(
                    'This program is currently unavailable due to licensing reasons',
                    expected=True, video_id=video_id)
            self.raise_no_formats('No video sources found', expected=True, video_id=video_id)

        tracking = traverse_obj(player, ('trackingData', {dict})) or {}
        return {
            **json_ld,
            'id': video_id,
            'title': (traverse_obj(player, ('title', {str}))
                      or traverse_obj(tracking, ('title', {str}))
                      or json_ld.get('title')
                      or self._og_search_title(webpage, default=None)),
            'description': json_ld.get('description') or self._og_search_description(webpage),
            'thumbnail': (url_or_none(player.get('poster'))
                          or json_ld.get('thumbnail')),
            'duration': (int_or_none(tracking.get('durationInSeconds'))
                         or json_ld.get('duration')),
            'timestamp': (parse_iso8601(tracking.get('publicationDate'))
                          or json_ld.get('timestamp')),
            'uploader': tracking.get('source') or json_ld.get('uploader'),
            'series': welt_config.get('section') or json_ld.get('series'),
            'formats': formats,
            'subtitles': subtitles or json_ld.get('subtitles'),
            'is_live': True if is_live else None,
        }
