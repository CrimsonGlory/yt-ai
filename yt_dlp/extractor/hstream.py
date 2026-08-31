import json
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    orderedSet,
    try_call,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class HstreamIE(InfoExtractor):
    IE_NAME = 'hstream'
    IE_DESC = 'hstream.moe'
    _VALID_URL = r'https?://(?:www\.)?hstream\.moe/hentai/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://hstream.moe/hentai/inaka-ni-wa-kore-kurai-shika-goraku-ga-nai-2',
        'md5': 'dd7e2f724f410aceae906c8700c3b751',
        'info_dict': {
            'id': '2035',
            'ext': 'mp4',
            'display_id': 'inaka-ni-wa-kore-kurai-shika-goraku-ga-nai-2',
            'title': 'Inaka ni wa Kore Kurai Shika Goraku ga Nai - 2',
            'description': 'md5:08f9c0cf0866b9b1f7ac2febc50f9d9e',
            'thumbnail': r're:https?://hstream\.moe/.+\.webp',
            'timestamp': 1788115995,
            'upload_date': '20260830',
            'view_count': int,
            'tags': 'count:9',
            'age_limit': 18,
        },
        # Progressive 720p MP4 yields a full --test byte fetch; DASH init fragments are tiny
        'params': {'format': 'http-720'},
    }, {
        'url': 'https://hstream.moe/hentai/himawari-wa-yoru-ni-saku-1',
        'only_matching': True,
    }, {
        'url': 'https://hstream.moe/hentai/inaka-ni-wa-kore-kurai-shika-goraku-ga-nai',
        'only_matching': True,
    }]
    _API_URL = 'https://hstream.moe/player/api'
    _SITE_URL = 'https://hstream.moe'

    def _extract_playlist(self, webpage, series_id):
        entries = [
            self.url_result(
                f'{self._SITE_URL}/hentai/{ep_id}', HstreamIE, ep_id)
            for ep_id in orderedSet(re.findall(
                rf'href="https?://(?:www\.)?hstream\.moe/hentai/({re.escape(series_id)}-\d+)',
                webpage))
        ]
        if not entries:
            return None
        return self.playlist_result(
            entries, series_id, self._og_search_title(webpage, default=None))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        episode_id = self._search_regex(
            r'<input[^>]+id="e_id"[^>]+value="([^"]+)"',
            webpage, 'episode id', default=None)
        if not episode_id:
            playlist = self._extract_playlist(webpage, display_id)
            if playlist:
                return playlist
            raise ExtractorError('Unable to extract episode id', expected=True)

        xsrf = try_call(lambda: urllib.parse.unquote(
            self._get_cookies(self._SITE_URL)['XSRF-TOKEN'].value))
        headers = {
            'Content-Type': 'application/json',
            'Origin': self._SITE_URL,
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
        }
        if xsrf:
            headers['X-XSRF-TOKEN'] = xsrf

        video = self._download_json(
            self._API_URL, episode_id, 'Downloading player API JSON',
            data=json.dumps({'episode_id': episode_id}).encode(),
            headers=headers)

        stream_path = traverse_obj(video, ('stream_url', {str}))
        cdn = traverse_obj(video, ('stream_domains', 0, {url_or_none}))
        if not stream_path or not cdn:
            raise ExtractorError('No stream URL returned by player API', expected=True)

        stream_path = stream_path.replace('\\', '/').strip('/')
        cdn_base = f'{cdn.rstrip("/")}/{stream_path}'
        cdn_headers = {'Referer': f'{self._SITE_URL}/'}
        formats = [{
            'url': f'{cdn_base}/x264.720p.mp4',
            'format_id': 'http-720',
            'ext': 'mp4',
            'height': 720,
            'vcodec': 'h264',
            'http_headers': cdn_headers,
        }]

        mpd_ids = [('720', 'dash-720'), ('1080', 'dash-1080'), ('2160', 'dash-2160')]
        if video.get('interpolated'):
            mpd_ids.append(('1080i', 'dash-1080-48'))
        if video.get('interpolated_uhd'):
            mpd_ids.append(('2160i', 'dash-2160-48'))
        for path, mpd_id in mpd_ids:
            for f in self._extract_mpd_formats(
                    f'{cdn_base}/{path}/manifest.mpd', episode_id,
                    mpd_id=mpd_id, fatal=False, headers=cdn_headers) or []:
                f.setdefault('http_headers', cdn_headers)
                formats.append(f)

        subtitles = {
            'en': [{
                'url': f'{cdn_base}/eng.ass',
                'ext': 'ass',
            }, {
                'url': f'{cdn_base}/eng.vtt',
                'ext': 'vtt',
            }],
        }
        extra_subs = video.get('extra_subtitles')
        if isinstance(extra_subs, dict):
            for lang in extra_subs:
                if lang and lang != 'en':
                    subtitles[lang] = [{
                        'url': f'{cdn_base}/autotrans/{lang}.ass',
                        'ext': 'ass',
                    }]

        json_ld = self._search_json_ld(webpage, episode_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('id', None)

        ld = self._search_json(
            r'<script[^>]+type="application/ld\+json"[^>]*>', webpage,
            'JSON-LD', episode_id, fatal=False)
        description = clean_html(self._search_regex(
            r'<h2[^>]*>\s*Description\s*</h2>\s*<p[^>]*>(.+?)</p>',
            webpage, 'description', default=None, flags=re.DOTALL))

        return {
            **json_ld,
            'id': episode_id,
            'display_id': display_id,
            'title': video.get('title') or json_ld.get('title'),
            'description': description or json_ld.get('description'),
            'thumbnail': (
                urljoin(self._SITE_URL, video.get('poster'))
                or json_ld.get('thumbnail')
                or self._og_search_thumbnail(webpage, default=None)),
            'tags': traverse_obj(ld, ('genre', ..., {str})) or None,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 18,
        }
