import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    js_to_json,
    traverse_obj,
    unified_strdate,
    url_or_none,
)


class NovaBaseIE(InfoExtractor):
    IE_DESC = False

    def _is_challenge_page(self, webpage):
        return bool(webpage) and '<title>Just a moment...</title>' in webpage

    def _download_nova_webpage(self, url, video_id, *, fatal=True, allow_snapshot=True):
        webpage = self._download_webpage(
            url, video_id, impersonate=True, expected_status=403, fatal=fatal)
        if webpage and not self._is_challenge_page(webpage):
            return webpage

        # Player embed snapshots contain short-lived signed CDN URLs, so only
        # article pages are fetched from the Wayback Machine.
        if allow_snapshot:
            snapshot = self._download_json(
                'https://archive.org/wayback/available', video_id,
                'Resolving Wayback Machine snapshot', fatal=fatal,
                query={'url': url.split('#')[0]})
            snapshot_url = traverse_obj(
                snapshot, ('archived_snapshots', 'closest', 'url', {url_or_none}))
            if snapshot_url and traverse_obj(
                    snapshot, ('archived_snapshots', 'closest', 'status')) == '200':
                snapshot_url = re.sub(
                    r'(?i)^https?://web\.archive\.org/web/(\d+)/',
                    r'https://web.archive.org/web/\1id_/', snapshot_url)
                webpage = self._download_webpage(
                    snapshot_url, video_id, 'Downloading webpage from Wayback Machine',
                    fatal=fatal)
                if webpage and not self._is_challenge_page(webpage):
                    return webpage

        if not fatal:
            return False
        raise ExtractorError(
            'Unable to download webpage: the live site blocked this request',
            expected=True)

    def _extract_embed_player(self, webpage, video_id):
        has_drm = False
        duration = None
        formats = []

        def process_format_list(format_list, format_id=''):
            nonlocal formats, has_drm
            if not isinstance(format_list, list):
                format_list = [format_list]
            for format_dict in format_list:
                if not isinstance(format_dict, dict):
                    continue
                if (not self.get_param('allow_unplayable_formats')
                        and traverse_obj(format_dict, ('drm', 'keySystem'))):
                    has_drm = True
                    continue
                format_url = url_or_none(format_dict.get('src'))
                format_type = format_dict.get('type')
                ext = determine_ext(format_url)
                if (format_type in ('application/x-mpegURL', 'application/x-mpegurl')
                        or format_id == 'HLS' or ext == 'm3u8'):
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                elif (format_type == 'application/dash+xml'
                      or format_id == 'DASH' or ext == 'mpd'):
                    formats.extend(self._extract_mpd_formats(
                        format_url, video_id, mpd_id='dash', fatal=False))
                elif format_url:
                    formats.append({
                        'url': format_url,
                    })

        player = self._search_json(
            r'player:', webpage, 'player', video_id, fatal=False, end_pattern=r';\s*</script>')
        if player:
            for src in traverse_obj(player, ('lib', 'source', 'sources', ...)):
                process_format_list(src)
            duration = traverse_obj(player, ('sourceInfo', 'duration', {int_or_none}))
        if not formats and not has_drm:
            # older code path, in use before August 2023
            player = self._parse_json(
                self._search_regex(
                    (r'(?:(?:replacePlaceholders|processAdTagModifier).*?:\s*)?(?:replacePlaceholders|processAdTagModifier)\s*\(\s*(?P<json>{.*?})\s*\)(?:\s*\))?\s*,',
                     r'Player\.init\s*\([^,]+,(?P<cndn>\s*\w+\s*\?)?\s*(?P<json>{(?(cndn).+?|.+)})\s*(?(cndn):|,\s*{.+?}\s*\)\s*;)'),
                    webpage, 'player', default='{}', group='json'), video_id)
            if player:
                for format_id, format_list in player['tracks'].items():
                    process_format_list(format_list, format_id)
                duration = int_or_none(player.get('duration'))

        if not formats and has_drm:
            self.report_drm(video_id)

        title = self._og_search_title(
            webpage, default=None) or self._search_regex(
            (r'<value>(?P<value>[^<]+)',
             r'videoTitle\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1'), webpage,
            'title', default=None, group='value')
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._search_regex(
            r'poster\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'thumbnail', fatal=False, group='value')
        duration = int_or_none(self._search_regex(
            r'videoDuration\s*:\s*(\d+)', webpage, 'duration',
            default=duration))

        return {
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }


class NovaEmbedIE(NovaBaseIE):
    _VALID_URL = r'https?://media(?:tn)?\.cms\.nova\.cz/embed/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://media.cms.nova.cz/embed/8o0n0r?autoplay=1',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': '8o0n0r',
            'title': '2180. díl',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 2578,
        },
        'params': {
            'skip_download': True,
            'ignore_no_formats_error': True,
        },
        'expected_warnings': ['DRM protected', 'Requested format is not available'],
    }, {
        'url': 'https://media.cms.nova.cz/embed/KybpWYvcgOa',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': 'KybpWYvcgOa',
            'ext': 'mp4',
            'title': 'Borhyová oslavila 60? Soutěžící z pořadu odboural moderátora Ondřeje Sokola',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 114,
        },
        'params': {'skip_download': 'm3u8'},
    }, {
        'url': 'https://mediatn.cms.nova.cz/embed/EU5ELEsmOHt?autoplay=1',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': 'EU5ELEsmOHt',
            'ext': 'mp4',
            'title': 'Haptické křeslo, bionická ruka nebo roboti. Reportérka se podívala na Týden inovací',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 1780,
        },
        'params': {'skip_download': 'm3u8'},
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_nova_webpage(url, video_id)
        info = self._extract_embed_player(webpage, video_id)
        info['id'] = video_id
        return info


class NovaIE(NovaBaseIE):
    IE_DESC = 'TN.cz, Prásk.tv, Nova.cz, Novaplus.cz, FANDA.tv, Krásná.cz and Doma.cz'
    _VALID_URL = r'https?://(?:[^.]+\.)?(?P<site>tv(?:noviny)?|tn|novaplus|vymena|fanda|krasna|doma|prask)\.nova\.cz/(?:[^/]+/)+(?P<id>[^/]+?)(?:\.html|/|$)'
    _TESTS = [{
        'url': 'https://tn.nova.cz/video/4915-talk/563659-talk',
        'md5': '3e59c22b5677754c0bbcbd74e45ff3b7',
        'info_dict': {
            'id': '7TK5CuXPeZ6',
            'display_id': '563659-talk',
            'ext': 'mp4',
            'title': 'Nové album s hity Miroslava Žbirky: Hudební manažerka odhalila detaily z jeho vytváření',
            'description': 'md5:42069d1e911be5bfa872fda12356bba0',
            'thumbnail': r're:https://nova-ott-images-tn\.ssl\.cdn\.cra\.cz/.+',
            'duration': 1670,
            'timestamp': 1787304600,
            'upload_date': '20260821',
        },
    }, {
        'url': 'http://tn.nova.cz/clanek/tajemstvi-ukryte-v-podzemi-specialni-nemocnice-v-prazske-krci.html#player_13260',
        'skip': 'HTTP Error 403',
        'md5': 'da8f3f1fcdaf9fb0f112a32a165760a3',
        'info_dict': {
            'id': '8OvQqEvV3MW',
            'display_id': '8OvQqEvV3MW',
            'ext': 'mp4',
            'title': 'Podzemní nemocnice v pražské Krči',
            'description': 'md5:f0a42dd239c26f61c28f19e62d20ef53',
            'thumbnail': r're:^https?://.*\.(?:jpg)',
            'duration': 151,
        },
    }, {
        'url': 'http://fanda.nova.cz/clanek/fun-and-games/krvavy-epos-zaklinac-3-divoky-hon-vychazi-vyhrajte-ho-pro-sebe.html',
        'info_dict': {
            'id': '1753621',
            'ext': 'mp4',
            'title': 'Zaklínač 3: Divoký hon',
            'description': 're:.*Pokud se stejně jako my nemůžete.*',
            'thumbnail': r're:https?://.*\.jpg(\?.*)?',
            'upload_date': '20150521',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        'skip': 'gone',
    }, {
        # media.cms.nova.cz embed
        'url': 'https://novaplus.nova.cz/porad/ulice/epizoda/18760-2180-dil',
        'info_dict': {
            'id': '8o0n0r',
            'ext': 'mp4',
            'title': '2180. díl',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 2578,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [NovaEmbedIE.ie_key()],
        'skip': 'CHYBA 404: STRÁNKA NENALEZENA',
    }, {
        'url': 'http://sport.tn.nova.cz/clanek/sport/hokej/nhl/zivot-jde-dal-hodnotil-po-vyrazeni-z-playoff-jiri-sekac.html',
        'only_matching': True,
    }, {
        'url': 'http://fanda.nova.cz/clanek/fun-and-games/krvavy-epos-zaklinac-3-divoky-hon-vychazi-vyhrajte-ho-pro-sebe.html',
        'only_matching': True,
    }, {
        'url': 'http://doma.nova.cz/clanek/zdravi/prijdte-se-zapsat-do-registru-kostni-drene-jiz-ve-stredu-3-cervna.html',
        'only_matching': True,
    }, {
        'url': 'http://prask.nova.cz/clanek/novinky/co-si-na-sobe-nase-hvezdy-nechaly-pojistit.html',
        'only_matching': True,
    }, {
        'url': 'http://tv.nova.cz/clanek/novinky/zivot-je-zivot-bondovsky-trailer.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id')
        site = mobj.group('site')

        webpage = self._download_nova_webpage(url, display_id)

        json_ld = self._search_json_ld(
            webpage, display_id, expected_type='VideoObject', default={})
        description = json_ld.get('description') or clean_html(
            self._og_search_description(webpage, default=None))
        if site == 'novaplus':
            upload_date = unified_strdate(self._search_regex(
                r'(\d{1,2}-\d{1,2}-\d{4})$', display_id, 'upload date', default=None))
        elif site == 'fanda':
            upload_date = unified_strdate(self._search_regex(
                r'<span class="date_time">(\d{1,2}\.\d{1,2}\.\d{4})', webpage, 'upload date', default=None))
        else:
            upload_date = None

        embed_mobj = re.search(
            r'<iframe[^>]+\bsrc=["\'](?:https?:)?//(?P<host>media(?:tn)?\.cms\.nova\.cz)/embed/(?P<id>[^/?#&"\']+)',
            webpage)
        embed_id = embed_mobj.group('id') if embed_mobj else None
        embed_host = embed_mobj.group('host') if embed_mobj else 'media.cms.nova.cz'

        formats = []
        title = json_ld.get('title')
        thumbnail = traverse_obj(json_ld, ('thumbnails', 0, 'url', {url_or_none}))
        duration = json_ld.get('duration')
        video_id = embed_id or display_id

        if embed_id:
            embed_webpage = self._download_nova_webpage(
                f'https://{embed_host}/embed/{embed_id}', embed_id,
                fatal=False, allow_snapshot=False)
            if embed_webpage:
                player = self._extract_embed_player(embed_webpage, embed_id)
                formats.extend(player.get('formats') or [])
                title = title or player.get('title')
                thumbnail = thumbnail or player.get('thumbnail')
                duration = duration or player.get('duration')

        preview_url = url_or_none(self._search_regex(
            r'data-video-preview-url=["\'](https?://[^"\']+\.mp4)',
            webpage, 'preview url', default=None))
        if preview_url:
            formats.append({
                'url': preview_url,
                'ext': 'mp4',
                'format_id': 'preview',
                'quality': -10,
            })

        if formats:
            return {
                'id': video_id,
                'display_id': display_id,
                'title': title or self._og_search_title(webpage),
                'description': description,
                'upload_date': upload_date,
                'thumbnail': thumbnail or self._og_search_thumbnail(webpage, default=None),
                'duration': duration,
                'timestamp': json_ld.get('timestamp'),
                'formats': formats,
            }

        # legacy VideoJS player (pre-CMS embed)
        video_id = self._search_regex(
            [r"(?:media|video_id)\s*:\s*'(\d+)'",
             r'media=(\d+)',
             r'id="article_video_(\d+)"',
             r'id="player_(\d+)"'],
            webpage, 'video id')

        config_url = self._search_regex(
            r'src="(https?://(?:tn|api)\.nova\.cz/bin/player/videojs/config\.php\?[^"]+)"',
            webpage, 'config url', default=None)
        config_params = {}

        if not config_url:
            player = self._parse_json(
                self._search_regex(
                    r'(?s)Player\s*\(.+?\s*,\s*({.+?\bmedia\b["\']?\s*:\s*["\']?\d+.+?})\s*\)', webpage,
                    'player', default='{}'),
                video_id, transform_source=js_to_json, fatal=False)
            if player:
                config_url = url_or_none(player.get('configUrl'))
                params = player.get('configParams')
                if isinstance(params, dict):
                    config_params = params

        if not config_url:
            DEFAULT_SITE_ID = '23000'
            SITES = {
                'tvnoviny': DEFAULT_SITE_ID,
                'novaplus': DEFAULT_SITE_ID,
                'vymena': DEFAULT_SITE_ID,
                'krasna': DEFAULT_SITE_ID,
                'fanda': '30',
                'tn': '30',
                'doma': '30',
            }

            site_id = self._search_regex(
                r'site=(\d+)', webpage, 'site id', default=None) or SITES.get(
                site, DEFAULT_SITE_ID)

            config_url = 'https://api.nova.cz/bin/player/videojs/config.php'
            config_params = {
                'site': site_id,
                'media': video_id,
                'quality': 3,
                'version': 1,
            }

        config = self._download_json(
            config_url, display_id,
            'Downloading config JSON', query=config_params,
            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        mediafile = config['mediafile']
        video_url = mediafile['src']

        m = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>[^/]+?))/&*(?P<playpath>.+)$', video_url)
        if m:
            formats = [{
                'url': m.group('url'),
                'app': m.group('app'),
                'play_path': m.group('playpath'),
                'player_path': 'http://tvnoviny.nova.cz/static/shared/app/videojs/video-js.swf',
                'ext': 'flv',
            }]
        else:
            formats = [{
                'url': video_url,
            }]

        title = mediafile.get('meta', {}).get('title') or self._og_search_title(webpage)
        thumbnail = config.get('poster')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'formats': formats,
        }
