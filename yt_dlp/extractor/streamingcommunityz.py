import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    parse_iso8601,
    str_or_none,
    unescapeHTML,
    unified_strdate,
    update_url_query,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class StreamingCommunityzIE(InfoExtractor):
    IE_NAME = 'streamingcommunityz'
    IE_DESC = 'StreamingCommunity'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?streamingcommunityz\.\w+/
        (?:[a-z]{2}/)?
        (?P<kind>watch|iframe|titles)/
        (?P<id>\d+)
    '''
    _TESTS = [{
        'url': 'https://streamingcommunityz.style/it/watch/60268',
        'md5': '0209984f5297c3baf9b71da853c81dc8',
        'info_dict': {
            'id': '60268',
            'ext': 'mp4',
            'title': 'Oceania',
            'description': 'md5:b951c6c5eb32ad488a71740fadf64ad1',
            'duration': 6900,
            'release_date': '20260708',
            'timestamp': 1780597981,
            'upload_date': '20260604',
            'view_count': int,
        },
    }, {
        'url': 'https://streamingcommunityz.style/it/iframe/60268',
        'only_matching': True,
    }, {
        'url': 'https://streamingcommunityz.style/it/watch/8424?e=61161',
        'only_matching': True,
    }, {
        'url': 'https://streamingcommunityz.style/it/titles/60268-oceania',
        'only_matching': True,
    }, {
        'url': 'https://streamingcommunityz.style/it/titles/8424-dark-matter/season-2',
        'only_matching': True,
    }, {
        'url': 'https://streamingcommunityz.cz/it/watch/60268',
        'only_matching': True,
    }]

    def _site_base(self, url):
        parsed = urllib.parse.urlparse(url)
        parts = parsed.path.split('/')
        lang = ''
        if len(parts) > 1 and len(parts[1]) == 2 and parts[1].isalpha():
            lang = f'/{parts[1]}'
        return f'{parsed.scheme}://{parsed.netloc}{lang}'

    def _watch_url(self, url, title_id, episode_id=None):
        watch_url = f'{self._site_base(url)}/watch/{title_id}'
        if episode_id is not None:
            watch_url = update_url_query(watch_url, {'e': episode_id})
        return watch_url

    def _extract_vixcloud(self, iframe_page_url, video_id, referer):
        iframe_page = self._download_webpage(
            iframe_page_url, video_id, 'Downloading iframe page',
            headers={'Referer': referer})
        vix_url = url_or_none(unescapeHTML(self._search_regex(
            r'<iframe[^>]+\bsrc=["\']([^"\']+)', iframe_page, 'vixcloud url')))
        if not vix_url:
            raise ExtractorError('Unable to extract vixcloud embed URL', expected=True)
        vix_url = urljoin(iframe_page_url, vix_url)
        vix_page = self._download_webpage(
            vix_url, video_id, 'Downloading vixcloud embed',
            headers={'Referer': iframe_page_url})

        master = self._search_json(
            r'window\.masterPlaylist\s*=', vix_page, 'master playlist',
            video_id, transform_source=js_to_json)
        playlist_url = url_or_none(traverse_obj(master, 'url'))
        if not playlist_url:
            raise ExtractorError('Unable to extract vixcloud playlist URL', expected=True)

        params = {
            k: v for k, v in (traverse_obj(master, ('params', {dict})) or {}).items()
            if v not in (None, '')
        }
        if self._search_regex(
                r'window\.canPlayFHD\s*=\s*(true|false)',
                vix_page, 'can play FHD', default='false') == 'true':
            params['h'] = 1
        playlist_url = update_url_query(playlist_url, params)

        parsed_vix = urllib.parse.urlparse(vix_url)
        headers = {
            'Referer': vix_url,
            'Origin': f'{parsed_vix.scheme}://{parsed_vix.netloc}',
        }
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            playlist_url, video_id, 'mp4', m3u8_id='hls', headers=headers)
        return formats, subtitles, headers

    def _extract_watch(self, url, video_id, page, referer):
        if traverse_obj(page, ('props', 'redirectToLogin', {bool})):
            self.raise_login_required()

        title = traverse_obj(page, ('props', 'title', {dict})) or {}
        episode = traverse_obj(page, ('props', 'episode', {dict})) or {}
        episode_id = traverse_obj(episode, ('id', {int_or_none}))
        embed_url = url_or_none(traverse_obj(page, ('props', 'embedUrl', {str})))
        if not embed_url:
            embed_url = f'{self._site_base(url)}/iframe/{video_id}'
            if episode_id is not None:
                embed_url = update_url_query(embed_url, {'episode_id': episode_id})

        display_id = video_id
        if episode_id is not None:
            display_id = f'{video_id}_{episode_id}'

        formats, subtitles, headers = self._extract_vixcloud(
            embed_url, display_id, referer)

        title_name = traverse_obj(title, ('name', {str}))
        episode_name = traverse_obj(episode, ('name', {str}))
        season_number = traverse_obj(episode, ('season', 'number', {int_or_none}))
        episode_number = traverse_obj(episode, ('number', {int_or_none}))
        video_title = title_name
        if episode_name or episode_number is not None:
            sn_en = ''
            if season_number is not None and episode_number is not None:
                sn_en = f'S{season_number:02d}E{episode_number:02d}'
            video_title = ' - '.join(filter(None, (title_name, sn_en, episode_name)))

        runtime = traverse_obj(
            (episode, title), (..., 'duration', {int_or_none}), get_all=False)
        if runtime is None:
            runtime = traverse_obj(title, ('runtime', {int_or_none}))
        duration = runtime * 60 if runtime else None

        return {
            'id': display_id,
            'title': video_title,
            'description': traverse_obj(
                (episode, title), (..., 'plot', {str}), get_all=False),
            'duration': duration,
            'release_date': unified_strdate(traverse_obj(title, ('release_date', {str}))),
            'timestamp': parse_iso8601(traverse_obj(
                (episode, title), (..., 'created_at', {str}), get_all=False)),
            'view_count': traverse_obj(title, ('views', {int_or_none})),
            'age_limit': traverse_obj(title, ('age', {int_or_none})),
            'series': title_name if episode_id is not None else None,
            'series_id': video_id if episode_id is not None else None,
            'season_number': season_number,
            'season_id': str_or_none(traverse_obj(episode, ('season', 'id', {int_or_none}))),
            'episode': episode_name,
            'episode_number': episode_number,
            'episode_id': str_or_none(episode_id),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
        }

    def _extract_title_page(self, url, video_id, page):
        title = traverse_obj(page, ('props', 'title', {dict})) or {}
        title_name = traverse_obj(title, ('name', {str}))
        if traverse_obj(title, ('type', {str})) != 'tv':
            return self.url_result(
                self._watch_url(url, video_id), self.ie_key(),
                video_id, title_name)

        parsed = urllib.parse.urlparse(url)
        loaded = traverse_obj(page, ('props', 'loadedSeason', {dict})) or {}
        if re.search(r'/season-\d+', parsed.path):
            season_number = traverse_obj(loaded, ('number', {int_or_none}))
            playlist_title = title_name
            if season_number is not None:
                playlist_title = f'{title_name} - S{season_number:02d}'
            entries = []
            for ep in traverse_obj(loaded, ('episodes', ..., {dict})) or []:
                ep_id = traverse_obj(ep, ('id', {int_or_none}))
                if ep_id is None:
                    continue
                entries.append(self.url_result(
                    self._watch_url(url, video_id, ep_id), self.ie_key(),
                    f'{video_id}_{ep_id}', ep.get('name')))
            return self.playlist_result(entries, video_id, playlist_title)

        slug = traverse_obj(title, ('slug', {str})) or video_id
        base = self._site_base(url)
        entries = []
        for season in traverse_obj(title, ('seasons', ..., {dict})) or []:
            number = traverse_obj(season, ('number', {int_or_none}))
            if number is None:
                continue
            entries.append(self.url_result(
                f'{base}/titles/{video_id}-{slug}/season-{number}',
                self.ie_key(), f'{video_id}_s{number}'))
        if not entries:
            season_number = traverse_obj(loaded, ('number', {int_or_none})) or 1
            return self._extract_title_page(
                f'{base}/titles/{video_id}-{slug}/season-{season_number}',
                video_id, page)
        return self.playlist_result(entries, video_id, title_name)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id, kind = mobj.group('id', 'kind')

        if kind == 'iframe':
            formats, subtitles, headers = self._extract_vixcloud(url, video_id, url)
            return {
                'id': video_id,
                'title': video_id,
                'formats': formats,
                'subtitles': subtitles,
                'http_headers': headers,
            }

        webpage = self._download_webpage(url, video_id)
        page = self._parse_json(
            self._search_regex(r'data-page="([^"]+)"', webpage, 'page data'),
            video_id, transform_source=unescapeHTML)

        if kind == 'titles':
            return self._extract_title_page(url, video_id, page)
        return self._extract_watch(url, video_id, page, url)
