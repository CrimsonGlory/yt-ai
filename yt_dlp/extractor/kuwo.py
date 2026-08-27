import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    InAdvancePagedList,
    clean_html,
    get_element_by_id,
    int_or_none,
    js_to_json,
    remove_start,
    traverse_obj,
    unescapeHTML,
    unified_strdate,
    url_or_none,
)


class KuwoBaseIE(InfoExtractor):
    _FORMATS = [
        {'format': 'ape', 'ext': 'ape', 'preference': 100},
        {'format': 'mp3-320', 'ext': 'mp3', 'br': '320kmp3', 'abr': 320, 'preference': 80},
        {'format': 'mp3-192', 'ext': 'mp3', 'br': '192kmp3', 'abr': 192, 'preference': 70},
        {'format': 'mp3-128', 'ext': 'mp3', 'br': '128kmp3', 'abr': 128, 'preference': 60},
        {'format': 'wma', 'ext': 'wma', 'preference': 20},
        {'format': 'aac', 'ext': 'aac', 'abr': 48, 'preference': 10},
    ]

    def _get_formats(self, song_id, tolerate_ip_deny=False):
        formats = []
        for file_format in self._FORMATS:
            query = {
                'format': file_format['ext'],
                'br': file_format.get('br', ''),
                'rid': f'MUSIC_{song_id}',
                'type': 'convert_url',
                'response': 'url',
            }

            song_url = self._download_webpage(
                'https://antiserver.kuwo.cn/anti.s',
                song_id, note=f'Downloading {file_format["format"]} url info',
                query=query, headers=self.geo_verification_headers(),
                fatal=False)

            if song_url == 'IPDeny' and not tolerate_ip_deny:
                raise ExtractorError('This song is blocked in this region', expected=True)

            song_url = url_or_none((song_url or '').strip())
            if song_url:
                formats.append({
                    'url': song_url,
                    'format_id': file_format['format'],
                    'format': file_format['format'],
                    'ext': file_format['ext'],
                    'vcodec': 'none',
                    'quality': file_format['preference'],
                    'abr': file_format.get('abr'),
                })

        return formats

    def _decode_text(self, value):
        if not value:
            return None
        return unescapeHTML(str(value)).replace('\xa0', ' ').strip() or None


class KuwoIE(KuwoBaseIE):
    _WEB_FALLBACK = True
    IE_NAME = 'kuwo:song'
    IE_DESC = '酷我音乐'
    _VALID_URL = r'https?://(?:(?:www|m)\.)?kuwo\.cn/(?:(?:newh5app/)?play_detail|yinyue)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.kuwo.cn/play_detail/639883212',
        'md5': 'a523c65653256f36635e6c924fa828d9',
        'info_dict': {
            'id': '639883212',
            'ext': 'mp3',
            'title': '今生劫换来生缘 (闽南对唱版)',
            'creator': '咏春&еяхат музыка',
            'creators': ['咏春&еяхат музыка'],
            'album': '今生劫换来生缘(闽南对唱版)',
            'duration': 196,
            'upload_date': '20260824',
        },
        'params': {
            'format': 'mp3-128',
        },
    }, {
        'url': 'http://www.kuwo.cn/yinyue/635632/',
        'info_dict': {
            'id': '635632',
            'ext': 'ape',
            'title': '爱我别走',
            'creator': '张震岳',
            'upload_date': '20080122',
            'description': 'md5:ed13f58e3c3bf3f7fd9fbc4e5a7aa75c',
        },
        'skip': 'this song has been offline because of copyright issues',
    }, {
        'url': 'http://www.kuwo.cn/yinyue/6446136/',
        'skip': 'Legacy /yinyue/ pages return HTTP 5xx',
        'info_dict': {
            'id': '6446136',
            'ext': 'mp3',
            'title': '心',
            'description': 'md5:5d0e947b242c35dc0eb1d2fce9fbf02c',
            'creator': 'IU',
            'upload_date': '20150518',
        },
        'params': {
            'format': 'mp3-320',
        },
    }, {
        'url': 'http://www.kuwo.cn/yinyue/3197154?catalog=yueku2016',
        'only_matching': True,
    }, {
        'url': 'https://m.kuwo.cn/newh5app/play_detail/639883212',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        song_id = self._match_id(url)

        # Desktop www.kuwo.cn pages currently 500; metadata is still public
        # via the search API and audio via antiserver.kuwo.cn.
        meta = self._download_json(
            'https://search.kuwo.cn/r.s', song_id,
            'Downloading song metadata',
            query={
                'rid': f'MUSIC_{song_id}',
                'ft': 'music',
                'rformat': 'json',
                'encoding': 'utf8',
                'rn': '1',
                'pn': '0',
            },
            transform_source=js_to_json,
            fatal=False)
        song = traverse_obj(meta, ('abslist', 0, {dict})) or {}
        if str(song.get('id') or '') != song_id:
            song = {}

        formats = self._get_formats(song_id)
        if not formats:
            raise ExtractorError('Unable to extract song URL', expected=True)

        return {
            'id': song_id,
            'title': self._decode_text(song.get('SONGNAME') or song.get('name')) or song_id,
            'creator': self._decode_text(song.get('ARTIST') or song.get('artist')),
            'album': self._decode_text(song.get('ALBUM')),
            'duration': int_or_none(song.get('DURATION')),
            'upload_date': unified_strdate(self._decode_text(song.get('releasedate'))),
            'formats': formats,
        }


class KuwoAlbumIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'kuwo:album'
    IE_DESC = '酷我音乐 - 专辑'
    _VALID_URL = r'https?://(?:www\.)?kuwo\.cn/album/(?P<id>\d+?)/'
    _TEST = {
        'url': 'http://www.kuwo.cn/album/502294/',
        'skip': 'Site returned HTTP 5xx',
        'info_dict': {
            'id': '502294',
            'title': 'Made\xa0Series\xa0《M》',
            'description': 'md5:d463f0d8a0ff3c3ea3d6ed7452a9483f',
        },
        'playlist_count': 2,
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)

        webpage = self._download_webpage(
            url, album_id, note='Download album info',
            errnote='Unable to get album info')

        album_name = self._html_search_regex(
            r'<div[^>]+class="comm"[^<]+<h1[^>]+title="([^"]+)"', webpage,
            'album name')
        album_intro = remove_start(
            clean_html(get_element_by_id('intro', webpage)),
            f'{album_name}简介：')

        entries = [
            self.url_result(song_url, 'Kuwo') for song_url in re.findall(
                r'<p[^>]+class="listen"><a[^>]+href="(http://www\.kuwo\.cn/yinyue/\d+/)"',
                webpage)
        ]
        return self.playlist_result(entries, album_id, album_name, album_intro)


class KuwoChartIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'kuwo:chart'
    IE_DESC = '酷我音乐 - 排行榜'
    _VALID_URL = r'https?://yinyue\.kuwo\.cn/billboard_(?P<id>[^.]+).htm'
    _TEST = {
        'url': 'http://yinyue.kuwo.cn/billboard_香港中文龙虎榜.htm',
        'skip': 'Site returned HTTP 5xx',
        'info_dict': {
            'id': '香港中文龙虎榜',
        },
        'playlist_mincount': 7,
    }

    def _real_extract(self, url):
        chart_id = self._match_id(url)
        webpage = self._download_webpage(
            url, chart_id, note='Download chart info',
            errnote='Unable to get chart info')

        entries = [
            self.url_result(song_url, 'Kuwo') for song_url in re.findall(
                r'<a[^>]+href="(http://www\.kuwo\.cn/yinyue/\d+)', webpage)
        ]
        return self.playlist_result(entries, chart_id)


class KuwoSingerIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'kuwo:singer'
    IE_DESC = '酷我音乐 - 歌手'
    _VALID_URL = r'https?://(?:www\.)?kuwo\.cn/mingxing/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.kuwo.cn/mingxing/bruno+mars/',
        'skip': 'Site returned HTTP 5xx',
        'info_dict': {
            'id': 'bruno+mars',
            'title': 'Bruno\xa0Mars',
        },
        'playlist_mincount': 329,
    }, {
        'url': 'http://www.kuwo.cn/mingxing/Ali/music.htm',
        'info_dict': {
            'id': 'Ali',
            'title': 'Ali',
        },
        'playlist_mincount': 95,
        'skip': 'Regularly stalls travis build',  # See https://travis-ci.org/ytdl-org/youtube-dl/jobs/78878540
    }]

    PAGE_SIZE = 15

    def _real_extract(self, url):
        singer_id = self._match_id(url)
        webpage = self._download_webpage(
            url, singer_id, note='Download singer info',
            errnote='Unable to get singer info')

        singer_name = self._html_search_regex(
            r'<h1>([^<]+)</h1>', webpage, 'singer name')

        artist_id = self._html_search_regex(
            r'data-artistid="(\d+)"', webpage, 'artist id')

        page_count = int(self._html_search_regex(
            r'data-page="(\d+)"', webpage, 'page count'))

        def page_func(page_num):
            webpage = self._download_webpage(
                'http://www.kuwo.cn/artist/contentMusicsAjax',
                singer_id, note=f'Download song list page #{page_num + 1}',
                errnote=f'Unable to get song list page #{page_num + 1}',
                query={'artistId': artist_id, 'pn': page_num, 'rn': self.PAGE_SIZE})

            return [
                self.url_result(urllib.parse.urljoin(url, song_url), 'Kuwo')
                for song_url in re.findall(
                    r'<div[^>]+class="name"><a[^>]+href="(/yinyue/\d+)',
                    webpage)
            ]

        entries = InAdvancePagedList(page_func, page_count, self.PAGE_SIZE)

        return self.playlist_result(entries, singer_id, singer_name)


class KuwoCategoryIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_NAME = 'kuwo:category'
    IE_DESC = '酷我音乐 - 分类'
    _VALID_URL = r'https?://yinyue\.kuwo\.cn/yy/cinfo_(?P<id>\d+?).htm'
    _TEST = {
        'url': 'http://yinyue.kuwo.cn/yy/cinfo_86375.htm',
        'skip': 'Site returned HTTP 5xx',
        'info_dict': {
            'id': '86375',
            'title': '八十年代精选',
            'description': '这些都是属于八十年代的回忆！',
        },
        'playlist_mincount': 24,
    }

    def _real_extract(self, url):
        category_id = self._match_id(url)
        webpage = self._download_webpage(
            url, category_id, note='Download category info',
            errnote='Unable to get category info')

        category_name = self._html_search_regex(
            r'<h1[^>]+title="([^<>]+?)">[^<>]+?</h1>', webpage, 'category name')

        category_desc = remove_start(
            get_element_by_id('intro', webpage).strip(),
            f'{category_name}简介：')
        if category_desc == '暂无':
            category_desc = None

        jsonm = self._parse_json(self._html_search_regex(
            r'var\s+jsonm\s*=\s*([^;]+);', webpage, 'category songs'), category_id)

        entries = [
            self.url_result('http://www.kuwo.cn/yinyue/{}/'.format(song['musicrid']), 'Kuwo')
            for song in jsonm['musiclist']
        ]
        return self.playlist_result(entries, category_id, category_name, category_desc)


class KuwoMvIE(KuwoBaseIE):
    _WEB_FALLBACK = True
    IE_NAME = 'kuwo:mv'
    IE_DESC = '酷我音乐 - MV'
    _VALID_URL = r'https?://(?:www\.)?kuwo\.cn/mv/(?P<id>\d+?)/'
    _TEST = {
        'url': 'http://www.kuwo.cn/mv/6480076/',
        'skip': 'Site returned HTTP 5xx',
        'info_dict': {
            'id': '6480076',
            'ext': 'mp4',
            'title': 'My HouseMV',
            'creator': '2PM',
        },
        # In this video, music URLs (anti.s) are blocked outside China and
        # USA, while the MV URL (mvurl) is available globally, so force the MV
        # URL for consistent results in different countries
        'params': {
            'format': 'mv',
        },
    }
    _FORMATS = [
        *KuwoBaseIE._FORMATS,
        {'format': 'mkv', 'ext': 'mkv', 'preference': 250},
        {'format': 'mp4', 'ext': 'mp4', 'preference': 200}]

    def _real_extract(self, url):
        song_id = self._match_id(url)
        webpage = self._download_webpage(
            url, song_id, note=f'Download mv detail info: {song_id}',
            errnote=f'Unable to get mv detail info: {song_id}')

        mobj = re.search(
            r'<h1[^>]+title="(?P<song>[^"]+)">[^<]+<span[^>]+title="(?P<singer>[^"]+)"',
            webpage)
        if mobj:
            song_name = mobj.group('song')
            singer_name = mobj.group('singer')
        else:
            raise ExtractorError('Unable to find song or singer names')

        formats = self._get_formats(song_id, tolerate_ip_deny=True)

        mv_url = self._download_webpage(
            f'http://www.kuwo.cn/yy/st/mvurl?rid=MUSIC_{song_id}',
            song_id, note=f'Download {song_id} MV URL')
        formats.append({
            'url': mv_url,
            'format_id': 'mv',
        })

        return {
            'id': song_id,
            'title': song_name,
            'creator': singer_name,
            'formats': formats,
        }
