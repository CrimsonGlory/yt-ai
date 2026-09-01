import functools
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    clean_html,
    orderedSet,
    str_or_none,
    traverse_obj,
    unified_strdate,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class RTHKBaseIE(InfoExtractor):
    _CATCHUP_PAGE_SIZE = 10

    def _player_m3u8s(self, webpage, player_id_re):
        urls = []
        for mobj in re.finditer(rf'jwplayer\("({player_id_re})"\)\.setup\(', webpage):
            start = mobj.end()
            nxt = webpage.find('jwplayer(', start)
            body = webpage[start:nxt if nxt != -1 else start + 2000]
            urls.extend(re.findall(r'file:\s*"([^"]+\.m3u8[^"]*)"', body))
        return [u for u in orderedSet(urls) if url_or_none(u)]

    def _extract_episode_m3u8s(self, webpage, media, channel, programme, video_id):
        # radioEpiPlay / episodePlayer are the episode itself; radioPlay1 is the
        # latest catchup item embedded on the same page.
        m3u8s = self._player_m3u8s(webpage, r'radioEpiPlay\d+|episodePlayer')
        if m3u8s:
            return m3u8s

        if media == 'radio':
            ep_html = self._download_webpage(
                'https://www.rthk.hk/radio/getEpisode', video_id,
                'Downloading episode player', fatal=False,
                query={'c': channel, 'p': programme, 'e': video_id})
            if ep_html:
                m3u8s = self._player_m3u8s(ep_html, r'radioEpiPlay\d+') or [
                    u for u in re.findall(r'file:\s*"([^"]+\.m3u8[^"]*)"', ep_html)
                    if url_or_none(u)]
                if m3u8s:
                    return orderedSet(m3u8s)

        episode_date = self._search_regex(
            r'window\.__curentEpisode_date\s*=\s*"(\d{4}-\d{2}-\d{2})"',
            webpage, 'episode date', default=None)
        if episode_date:
            ymd = episode_date.replace('-', '')
            m3u8s = [
                u for u in re.findall(r'file:\s*"([^"]+\.m3u8[^"]*)"', webpage)
                if url_or_none(u) and ymd in u]
            if m3u8s:
                return orderedSet(m3u8s)

        return []

    def _extract_episode_meta(self, webpage):
        episode_date = self._search_regex(
            r'window\.__curentEpisode_date\s*=\s*"([^"]+)"',
            webpage, 'episode date', default=None)
        title = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage)
        series = self._html_search_regex(
            r'<div class="proTitle[^"]*"[^>]*>\s*(?:<a[^>]*>\s*)?<h1>([^<]+)</h1>',
            webpage, 'series', default=None)
        return {
            'title': title.strip() if title else title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'series': series.strip() if series else series,
            'upload_date': unified_strdate(episode_date),
            'timestamp': unified_timestamp(episode_date),
        }


class RTHKIE(RTHKBaseIE):
    IE_NAME = 'rthk'
    IE_DESC = 'RTHK'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?rthk\.hk/
        (?P<media>radio|tv)/(?P<channel>[^/?#]+)/programme/(?P<programme>[^/?#]+)/
        episode/(?P<id>\d+)
    '''
    _TESTS = [{
        'url': 'https://www.rthk.hk/radio/radio2/programme/albertau/episode/1123704',
        'md5': '3147852ca1a20a881f9d85b20af641ab',
        'info_dict': {
            'id': '1123704',
            'ext': 'mp4',
            'title': '香港電台第二台 Albert Au 區瑞強 - Albert Au 區瑞強',
            'description': '天籟之音，媲美發燒天碟，絕對靚聲節目\n時間﹕逢星期一至五，晚上7:00-8:00\n主持﹕區瑞強',
            'thumbnail': r're:https://webstatic\.rthk\.hk/.+',
            'series': 'Albert Au 區瑞強',
            'channel_id': 'radio2',
            'upload_date': '20260828',
            'timestamp': 1787875200,
        },
    }, {
        'url': 'https://www.rthk.hk/tv/dtt31/programme/talkabout/episode/1110672',
        'info_dict': {
            'id': '1110672',
            'ext': 'mp4',
            'title': '港台電視 31 千禧年代 - 千禧年代 9月1日',
            'description': r're:主題：季節性流感疫苗接種計劃',
            'thumbnail': r're:https?://(?:www\.)?rthk\.hk/.+',
            'series': '千禧年代',
            'channel_id': 'dtt31',
            'upload_date': '20260901',
            'timestamp': 1788220800,
        },
    }, {
        'url': 'https://www.rthk.hk/radio/radio2/programme/albertau/episode/1124199/archive/0',
        'only_matching': True,
    }, {
        'url': 'https://www.rthk.hk/radio/radio2/programme/albertau/episode/847572',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        media, channel, programme, video_id = self._match_valid_url(url).group(
            'media', 'channel', 'programme', 'id')
        webpage = self._download_webpage(url, video_id)
        m3u8s = self._extract_episode_m3u8s(webpage, media, channel, programme, video_id)
        if not m3u8s:
            raise ExtractorError('No media source found', expected=True)

        formats, subtitles = [], {}
        for i, m3u8_url in enumerate(m3u8s):
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4',
                m3u8_id='hls' if len(m3u8s) == 1 else f'hls-{i}',
                fatal=not formats)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'channel_id': channel,
            **self._extract_episode_meta(webpage),
        }


class RTHKProgrammeIE(RTHKBaseIE):
    IE_NAME = 'rthk:programme'
    IE_DESC = 'RTHK programmes'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?rthk\.hk/
        (?P<media>radio|tv)/(?P<channel>[^/?#]+)/programme/(?P<id>[^/?#]+)/?(?:[?#]|$)
    '''
    _TESTS = [{
        'url': 'https://www.rthk.hk/radio/radio2/programme/albertau',
        'info_dict': {
            'id': 'albertau',
            'title': '香港電台第二台 Albert Au 區瑞強',
            'description': '天籟之音，媲美發燒天碟，絕對靚聲節目\n時間﹕逢星期一至五，晚上7:00-8:00\n主持﹕區瑞強',
            'thumbnail': r're:https://webstatic\.rthk\.hk/.+',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://www.rthk.hk/tv/dtt31/programme/talkabout',
        'info_dict': {
            'id': 'talkabout',
            'title': '香港電台電視 千禧年代',
            'description': r're:.+',
            'thumbnail': r're:https?://.+',
        },
        'playlist_mincount': 10,
    }]

    def _fetch_catchup_page(self, media, channel, programme, pagenum):
        data = self._download_json(
            f'https://www.rthk.hk/{media}/catchUp', programme,
            f'Downloading catchup page {pagenum + 1}', fatal=False,
            query={'c': channel, 'p': programme, 'page': pagenum + 1})
        if not isinstance(data, dict) or str(data.get('status')) != '1':
            return []
        entries = []
        for ep in traverse_obj(data, ('content', ..., {dict})):
            ep_id = str_or_none(ep.get('id'))
            if not ep_id:
                continue
            entries.append(self.url_result(
                f'https://www.rthk.hk/{media}/{channel}/programme/{programme}/episode/{ep_id}',
                ie=RTHKIE, video_id=ep_id,
                video_title=clean_html(ep.get('title'))))
        return entries

    def _real_extract(self, url):
        media, channel, programme = self._match_valid_url(url).group('media', 'channel', 'id')
        webpage = self._download_webpage(url, programme)

        first_page = self._fetch_catchup_page(media, channel, programme, 0)
        if first_page:
            entries = OnDemandPagedList(
                functools.partial(self._fetch_catchup_page, media, channel, programme),
                self._CATCHUP_PAGE_SIZE)
        else:
            entries = [
                self.url_result(
                    f'https://www.rthk.hk/{media}/{channel}/programme/{programme}/episode/{ep_id}',
                    ie=RTHKIE, video_id=ep_id)
                for ep_id in orderedSet(
                    group[0] or group[1]
                    for group in re.findall(
                        r'data-episode="(\d+)"|/programme/[^/]+/episode/(\d+)', webpage))
            ]

        return self.playlist_result(
            entries, programme,
            self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
            self._og_search_description(webpage, default=None),
            thumbnail=urljoin(url, self._og_search_thumbnail(webpage, default=None)))
