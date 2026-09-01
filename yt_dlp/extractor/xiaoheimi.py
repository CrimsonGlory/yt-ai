import base64
import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    orderedSet,
    url_or_none,
    urljoin,
)


class XiaoHeiMiIE(InfoExtractor):
    IE_NAME = 'xiaoheimi'
    IE_DESC = '小宝影院'
    _VALID_URL = [
        r'https?://(?:www\.)?xiaoheimi\.(?:net|cc)/index\.php/vod/play/id/(?P<id>\d+)/sid/(?P<sid>\d+)/nid/(?P<nid>\d+)(?:\.html)?',
        r'https?://(?:www\.)?xiaoheimi\.(?:net|cc)/index\.php/vod/detail/id/(?P<id>\d+)(?:\.html)?',
    ]
    _TESTS = [{
        'url': 'https://xiaoheimi.net/index.php/vod/play/id/42755/sid/2/nid/1.html',
        'md5': '43cf22b1cfccac9d71f8ed731e3445b2',
        'info_dict': {
            'id': '42755-2-1',
            'ext': 'mp4',
            'title': '炽道-第01集',
            'description': 'md5:1eefb2dfab680ce47c8b0046dd1d8f93',
            'series': '炽道',
            'series_id': '42755',
            'episode': '第01集',
            'episode_number': 1,
        },
    }, {
        'url': 'https://xiaoheimi.net/index.php/vod/play/id/42755/sid/1/nid/1.html',
        'only_matching': True,
    }, {
        'url': 'https://xiaoheimi.cc/index.php/vod/play/id/42755/sid/2/nid/1.html',
        'only_matching': True,
    }, {
        'url': 'https://xiaoheimi.net/index.php/vod/detail/id/42755.html',
        'only_matching': True,
    }]

    def _decode_player_url(self, media_url, encrypt):
        if not media_url:
            return None
        encrypt = str(encrypt or 0)
        try:
            if encrypt == '1':
                media_url = urllib.parse.unquote(media_url)
            elif encrypt == '2':
                media_url = urllib.parse.unquote(base64.b64decode(media_url).decode())
        except (TypeError, ValueError, UnicodeDecodeError):
            pass
        return media_url

    def _extract_playlist(self, url, vod_id):
        webpage = self._download_webpage(url, vod_id, impersonate=True)
        pane = self._search_regex(
            r'<div[^>]+id="playlist\d+"[^>]*>(.*?)</div>',
            webpage, 'playlist', default=webpage, flags=re.DOTALL)
        paths = orderedSet(re.findall(
            rf'/index\.php/vod/play/id/{re.escape(vod_id)}/sid/\d+/nid/\d+(?:\.html)?',
            pane))
        if not paths:
            raise ExtractorError('No episodes found', expected=True)
        return self.playlist_result(
            (self.url_result(urljoin(url, path), ie=self.ie_key()) for path in paths),
            vod_id,
            self._html_search_regex(
                r'<h1[^>]*class="title"[^>]*>([^<]+)', webpage, 'title', default=None),
            self._html_search_meta('description', webpage, default=None))

    def _real_extract(self, url):
        groups = self._match_valid_url(url).groupdict()
        vod_id, sid, nid = groups['id'], groups.get('sid'), groups.get('nid')
        if not sid:
            return self._extract_playlist(url, vod_id)

        video_id = join_nonempty(vod_id, sid, nid, delim='-')
        webpage, urlh = self._download_webpage_handle(
            url, video_id, impersonate=True)
        headers = {'Referer': urlh.url}

        player = self._search_json(
            r'player_(?:aaaa|data)\s*=', webpage, 'player data', video_id)
        media_url = url_or_none(self._decode_player_url(
            player.get('url'), player.get('encrypt')))
        if not media_url:
            self.raise_no_formats('No video URL', expected=True, video_id=video_id)

        if player.get('from') == 'iframe':
            return self.url_result(media_url)

        ext = determine_ext(media_url, 'mp4')
        if ext == 'm3u8' or '.m3u8' in media_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id='hls', headers=headers)
        elif ext == 'mpd':
            formats, subtitles = self._extract_mpd_formats_and_subtitles(
                media_url, video_id, mpd_id='dash', headers=headers)
        else:
            formats, subtitles = [{
                'url': media_url,
                'ext': ext,
                'http_headers': headers,
            }], {}

        title = self._html_search_regex(
            r'<title>([^<]+?)\s*在线播放', webpage, 'title', default=None)
        series = self._html_search_regex(
            r'<h3[^>]+class="title text-fff"[^>]*>([^<]+)',
            webpage, 'series', default=None)
        episode = self._html_search_regex(
            rf'<li[^>]+title="([^"]+)"[^>]*>\s*<a[^>]+href="[^"]*nid/{re.escape(nid)}',
            webpage, 'episode', default=None)

        return {
            'id': video_id,
            'title': title or join_nonempty(series, episode, delim='-'),
            'description': self._html_search_meta('description', webpage, default=None),
            'series': series,
            'series_id': vod_id,
            'episode': episode,
            'episode_number': int_or_none(nid),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
        }
