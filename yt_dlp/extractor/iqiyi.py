import base64
import itertools
import re
import time
import urllib.parse

from .common import InfoExtractor
from .openload import PhantomJSwrapper
from ..utils import (
    ExtractorError,
    float_or_none,
    format_field,
    int_or_none,
    js_to_json,
    parse_age_limit,
    parse_duration,
    parse_iso8601,
    parse_resolution,
    qualities,
    remove_start,
    str_or_none,
    traverse_obj,
    urljoin,
)


class IqiyiIE(InfoExtractor):
    IE_NAME = 'iqiyi'
    IE_DESC = '爱奇艺'

    _VALID_URL = r'https?://(?:(?:[^.]+\.)?iqiyi\.com|www\.pps\.tv)/.+\.html'

    _TESTS = [{
        'url': 'https://www.iqiyi.com/v_17tea0e85po.html',
        'md5': '2a29a1b8b251d28c0d19648f594d2f6d',
        'info_dict': {
            'id': '4426852504624000',
            'ext': 'mp4',
            'title': '《醒来》一人三面预告',
            'duration': 125,
            'thumbnail': 'http://pic1.iqiyipic.com/image/20260826/50/21/v_216224726_m_601_m1.jpg',
        },
        'expected_warnings': ['format is restricted'],
    }, {
        'url': 'http://www.iqiyi.com/v_19rrojlavg.html',
        'info_dict': {
            'id': '369658400',
            'ext': 'mp4',
            'title': '美国德州空中惊现奇异云团 酷似UFO',
        },
        'skip': 'video gone',
    }, {
        'url': 'http://www.iqiyi.com/v_19rrhnnclk.html',
        'md5': 'b7dc800a4004b1b57749d9abae0472da',
        'info_dict': {
            'id': 'e3f585b550a280af23c98b6cb2be19fb',
            'ext': 'mp4',
            # This can be either Simplified Chinese or Traditional Chinese
            'title': r're:^(?:名侦探柯南 国语版：第752集 迫近灰原秘密的黑影 下篇|名偵探柯南 國語版：第752集 迫近灰原秘密的黑影 下篇)$',
        },
        'skip': 'Geo-restricted to China',
    }, {
        'url': 'http://www.iqiyi.com/w_19rt6o8t9p.html',
        'only_matching': True,
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhbc6kt.html',
        'only_matching': True,
    }, {
        'url': 'http://yule.iqiyi.com/pcb.html',
        'info_dict': {
            'id': '4a0af228fddb55ec96398a364248ed7f',
            'ext': 'mp4',
            'title': '第2017-04-21期 女艺人频遭极端粉丝骚扰',
        },
        'skip': 'video gone',
    }, {
        # VIP-only video. The first 2 parts (6 minutes) are available without login
        # MD5 sums omitted as values are different on Travis CI and my machine
        'url': 'http://www.iqiyi.com/v_19rrny4w8w.html',
        'info_dict': {
            'id': 'f3cf468b39dddb30d676f89a91200dc1',
            'ext': 'mp4',
            'title': '泰坦尼克号',
        },
        'skip': 'Geo-restricted to China',
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhb8ce1.html',
        'info_dict': {
            'id': '202918101',
            'title': '灌篮高手 国语版',
        },
        'playlist_count': 101,
        'skip': 'playlist page changed',
    }, {
        'url': 'http://www.pps.tv/w_19rrbav0ph.html',
        'only_matching': True,
    }]

    _BID_TAGS = {
        '100': '240P',
        '200': '360P',
        '300': '480P',
        '500': '720P',
        '600': '1080P',
        '610': '1080P50',
        '700': '2K',
        '800': '4K',
    }

    @staticmethod
    def _tvid_from_url(url):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        for key in ('shareId', 'positiveId', 'tvid'):
            raw = traverse_obj(query, (key, 0), expected_type=str)
            if not raw:
                continue
            if key == 'tvid' and raw.isdigit():
                return raw
            try:
                tvid = int(base64.b64decode(urllib.parse.unquote(raw)))
            except (ValueError, TypeError, OSError):
                continue
            if tvid:
                return str(tvid)

        slug = urllib.parse.unquote(
            traverse_obj(re.search(r'/[vwp]_([^/?#]+)\.html', url), 1) or '')
        if not slug:
            return None
        try:
            id_bits = format(int(slug, 36), 'b')[::-1]
        except ValueError:
            return None
        key_bits = format(0x75706971676c, 'b')[::-1]
        xored = []
        for i in range(max(len(id_bits), len(key_bits))):
            a = int(id_bits[i]) if i < len(id_bits) else 0
            b = int(key_bits[i]) if i < len(key_bits) else 0
            xored.append(str(a ^ b))
        tvid = int(''.join(reversed(xored)), 2)
        if tvid < 900000:
            tvid = 100 * (tvid + 900000)
        return str(tvid) if tvid else None

    def _extract_playlist(self, webpage):
        PAGE_SIZE = 50

        links = re.findall(
            r'<a[^>]+class="site-piclist_pic_link"[^>]+href="(http://www\.iqiyi\.com/.+\.html)"',
            webpage)
        if not links:
            return

        album_id = self._search_regex(
            r'albumId\s*:\s*(\d+),', webpage, 'album ID')
        album_title = self._search_regex(
            r'data-share-title="([^"]+)"', webpage, 'album title', fatal=False)

        entries = list(map(self.url_result, links))

        # Start from 2 because links in the first page are already on webpage
        for page_num in itertools.count(2):
            pagelist_page = self._download_webpage(
                f'http://cache.video.qiyi.com/jp/avlist/{album_id}/{page_num}/{PAGE_SIZE}/',
                album_id,
                note=f'Download playlist page {page_num}',
                errnote=f'Failed to download playlist page {page_num}')
            pagelist = self._parse_json(
                remove_start(pagelist_page, 'var tvInfoJs='), album_id)
            vlist = pagelist['data']['vlist']
            for item in vlist:
                entries.append(self.url_result(item['vurl']))
            if len(vlist) < PAGE_SIZE:
                break

        return self.playlist_result(entries, album_id, album_title)

    def _extract_program_formats(self, format_data, video_id):
        formats = []
        http_headers = {
            'Referer': 'https://www.iqiyi.com/',
            'Origin': 'https://www.iqiyi.com',
        }
        for video_format in traverse_obj(
                format_data, ('program', 'video', ...), expected_type=dict):
            bid = str_or_none(video_format.get('bid'))
            extracted_formats = []
            if video_format.get('m3u8'):
                ff = video_format.get('ff', 'ts')
                if ff == 'ts':
                    m3u8_formats, _ = self._parse_m3u8_formats_and_subtitles(
                        video_format['m3u8'], ext='mp4', m3u8_id=bid, fatal=False)
                    extracted_formats.extend(m3u8_formats)
                else:
                    self.report_warning(f'{ff} formats are currently not supported')
            if not extracted_formats:
                if video_format.get('s'):
                    self.report_warning(
                        f'{self._BID_TAGS.get(bid, bid)} format is restricted')
                continue
            for f in extracted_formats:
                f.update({
                    'quality': qualities(list(self._BID_TAGS.keys()))(bid),
                    'format_note': self._BID_TAGS.get(bid),
                    'http_headers': {
                        **(f.get('http_headers') or {}),
                        **http_headers,
                    },
                    **parse_resolution(video_format.get('scrsz')),
                })
            formats.extend(extracted_formats)
        return formats

    def _real_extract(self, url):
        tvid = self._tvid_from_url(url)
        if not tvid:
            webpage = self._download_webpage(
                url, 'temp_id', note='download video page')
            playlist_result = self._extract_playlist(webpage)
            if playlist_result:
                return playlist_result
            raise ExtractorError('Can\'t find any video')

        data = self._download_json(
            'https://mesh.if.iqiyi.com/player/lw/lwplay/accelerator.js', tvid,
            note='Downloading video info', errnote='Unable to download video info',
            query={
                'tvid': tvid,
                'ad_cid': '',
                'disableDRM': 'false',
                'cpt': 0,
                'apiVer': 3,
                'format': 'json',
                'timestamp': int(time.time() * 1000),
            }, headers={
                'Referer': url,
                **self.geo_verification_headers(),
            })

        if data.get('offline') or traverse_obj(data, ('videoInfo', 'pagePublishStatus')) == 'PAGE_OFFLINE':
            raise ExtractorError('Video is offline', expected=True)

        ev = data.get('ev')
        if not ev:
            raise ExtractorError('No video formats found')

        ev_data = self._parse_json(''.join(chr(ord(c) ^ 90) for c in ev), tvid)
        if traverse_obj(ev_data, 'code') not in (None, 'A00000'):
            code = ev_data['code']
            if code == 'A00111':
                self.raise_geo_restricted()
            raise ExtractorError(f'Unable to load data. Error code: {code}')

        format_data = ev_data.get('data') or ev_data
        st = int_or_none(format_data.get('st'))
        if st == 111:
            self.raise_geo_restricted()
        formats = self._extract_program_formats(format_data, tvid)
        if not formats:
            raise ExtractorError('No video formats found')

        video_info = data.get('videoInfo') or {}
        return {
            'id': tvid,
            'title': video_info.get('title'),
            'thumbnail': video_info.get('imageUrl'),
            'duration': int_or_none(traverse_obj(
                format_data, ('program', 'video', ..., 'duration'), get_all=False)),
            'formats': formats,
        }


class IqIE(InfoExtractor):
    IE_NAME = 'iq.com'
    IE_DESC = 'International version of iQiyi'
    _VALID_URL = r'https?://(?:www\.)?iq\.com/play/(?:[\w%-]*-)?(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://www.iq.com/play/knot-episode-1-c3hbjhxtcg',
        'md5': 'dc0467fa44cf3d599653cdf132966ec1',
        'info_dict': {
            'ext': 'mp4',
            'id': 'c3hbjhxtcg',
            'title': 'KNOT',
            'description': 'md5:1e49999e85e281867ea8dc78d8345764',
            'duration': 2979,
            'timestamp': 1782863701,
            'upload_date': '20260630',
            'episode_number': 1,
            'episode': 'Episode 1',
            'series': 'KNOT',
            'age_limit': 18,
            'average_rating': float,
            'categories': [],
            'cast': ['Boat Yongyut Termtuo', 'Oat Pasakorn Sanrattana', 'Mintthy Ploychayapa Piyarapeetouch', 'Theme Phubeth Atarunwong', 'Thee Teerawat Tanacom', 'Jame Supawit Wongfu', 'Folk Jakarin Sangruan'],
        },
        'expected_warnings': ['format is restricted'],
    }, {
        'url': 'https://www.iq.com/play/one-piece-episode-1000-1ma1i6ferf4',
        'md5': '2d7caf6eeca8a32b407094b33b757d39',
        'info_dict': {
            'ext': 'mp4',
            'id': '1ma1i6ferf4',
            'title': '航海王 第1000集',
            'description': 'Subtitle available on Sunday 4PM（GMT+8）.',
            'duration': 1430,
            'timestamp': 1637488203,
            'upload_date': '20211121',
            'episode_number': 1000,
            'episode': 'Episode 1000',
            'series': 'One Piece',
            'age_limit': 13,
            'average_rating': float,
        },
        'params': {
            'format': '500',
        },
        'expected_warnings': ['format is restricted'],
        'skip': 'Geo-restricted',
    }, {
        # VIP-restricted video
        'url': 'https://www.iq.com/play/mermaid-in-the-fog-2021-gbdpx13bs4',
        'only_matching': True,
    }]
    _BID_TAGS = {
        '100': '240P',
        '200': '360P',
        '300': '480P',
        '500': '720P',
        '600': '1080P',
        '610': '1080P50',
        '700': '2K',
        '800': '4K',
    }
    _LID_TAGS = {
        '1': 'zh_CN',
        '2': 'zh_TW',
        '3': 'en',
        '4': 'ko',
        '5': 'ja',
        '18': 'th',
        '21': 'my',
        '23': 'vi',
        '24': 'id',
        '26': 'es',
        '27': 'pt',
        '28': 'ar',
    }

    _DASH_JS = '''
        console.log(page.evaluate(function() {
            var tvid = "%(tvid)s"; var vid = "%(vid)s"; var src = "%(src)s";
            var uid = "%(uid)s"; var dfp = "%(dfp)s"; var mode = "%(mode)s"; var lang = "%(lang)s";
            var bid_list = %(bid_list)s; var ut_list = %(ut_list)s; var tm = new Date().getTime();
            var cmd5x_func = %(cmd5x_func)s; var cmd5x_exporter = {}; cmd5x_func({}, cmd5x_exporter, {}); var cmd5x = cmd5x_exporter.cmd5x;
            var authKey = cmd5x(cmd5x('') + tm + '' + tvid);
            var k_uid = Array.apply(null, Array(32)).map(function() {return Math.floor(Math.random() * 15).toString(16)}).join('');
            var dash_paths = {};
            bid_list.forEach(function(bid) {
                var query = {
                    'tvid': tvid,
                    'bid': bid,
                    'ds': 1,
                    'vid': vid,
                    'src': src,
                    'vt': 0,
                    'rs': 1,
                    'uid': uid,
                    'ori': 'pcw',
                    'ps': 1,
                    'k_uid': k_uid,
                    'pt': 0,
                    'd': 0,
                    's': '',
                    'lid': '',
                    'slid': 0,
                    'cf': '',
                    'ct': '',
                    'authKey': authKey,
                    'k_tag': 1,
                    'ost': 0,
                    'ppt': 0,
                    'dfp': dfp,
                    'prio': JSON.stringify({
                        'ff': 'f4v',
                        'code': 2
                    }),
                    'k_err_retries': 0,
                    'up': '',
                    'su': 2,
                    'applang': lang,
                    'sver': 2,
                    'X-USER-MODE': mode,
                    'qd_v': 2,
                    'tm': tm,
                    'qdy': 'a',
                    'qds': 0,
                    'k_ft1': '143486267424900',
                    'k_ft4': '1572868',
                    'k_ft7': '4',
                    'k_ft5': '1',
                    'bop': JSON.stringify({
                        'version': '10.0',
                        'dfp': dfp
                    }),
                };
                var enc_params = [];
                for (var prop in query) {
                    enc_params.push(encodeURIComponent(prop) + '=' + encodeURIComponent(query[prop]));
                }
                ut_list.forEach(function(ut) {
                    enc_params.push('ut=' + ut);
                })
                var dash_path = '/dash?' + enc_params.join('&'); dash_path += '&vf=' + cmd5x(dash_path);
                dash_paths[bid] = dash_path;
            });
            return JSON.stringify(dash_paths);
        }));
        saveAndExit();
    '''

    def _extract_vms_player_js(self, webpage, video_id):
        player_js_cache = self.cache.load('iq', 'player_js')
        if player_js_cache:
            return player_js_cache
        webpack_js_url = self._proto_relative_url(self._search_regex(
            r'<script src="((?:https?:)?//stc\.iqiyipic\.com/_next/static/chunks/webpack-\w+\.js)"', webpage, 'webpack URL'))
        webpack_js = self._download_webpage(webpack_js_url, video_id, note='Downloading webpack JS', errnote='Unable to download webpack JS')

        webpack_map = self._search_json(
            r'["\']\s*\+\s*', webpack_js, 'JS locations', video_id,
            contains_pattern=r'{\s*(?:\d+\s*:\s*["\'][\da-f]+["\']\s*,?\s*)+}',
            end_pattern=r'\[\w+\]\+["\']\.js', transform_source=js_to_json)

        replacement_map = self._search_json(
            r'["\']\s*\+\(\s*', webpack_js, 'replacement map', video_id,
            contains_pattern=r'{\s*(?:\d+\s*:\s*["\'][\w.-]+["\']\s*,?\s*)+}',
            end_pattern=r'\[\w+\]\|\|\w+\)\+["\']\.', transform_source=js_to_json,
            fatal=False) or {}

        for module_index in reversed(webpack_map):
            real_module = replacement_map.get(module_index) or module_index
            module_js = self._download_webpage(
                f'https://stc.iqiyipic.com/_next/static/chunks/{real_module}.{webpack_map[module_index]}.js',
                video_id, note=f'Downloading #{module_index} module JS', errnote='Unable to download module JS', fatal=False) or ''
            if 'vms request' in module_js:
                self.cache.store('iq', 'player_js', module_js)
                return module_js
        raise ExtractorError('Unable to extract player JS')

    def _extract_cmd5x_function(self, webpage, video_id):
        return self._search_regex(r',\s*(function\s*\([^\)]*\)\s*{\s*var _qda.+_qdc\(\)\s*})\s*,',
                                  self._extract_vms_player_js(webpage, video_id), 'signature function')

    def _update_bid_tags(self, webpage, video_id):
        extracted_bid_tags = self._search_json(
            r'function\s*\([^)]*\)\s*\{\s*"use strict";?\s*var \w\s*=\s*',
            self._extract_vms_player_js(webpage, video_id), 'video tags', video_id,
            contains_pattern=r'{\s*\d+\s*:\s*\{\s*nbid\s*:.+}\s*}',
            end_pattern=r'\s*,\s*\w\s*=\s*\{\s*getNewVd', fatal=False, transform_source=js_to_json)
        if not extracted_bid_tags:
            return
        self._BID_TAGS = {
            bid: traverse_obj(extracted_bid_tags, (bid, 'value'), expected_type=str, default=self._BID_TAGS.get(bid))
            for bid in extracted_bid_tags
        }

    def _get_cookie(self, name, default=None):
        cookie = self._get_cookies('https://iq.com/').get(name)
        return cookie.value if cookie else default

    def _extract_program_formats(self, format_data, video_id, video_format):
        bid = str_or_none(video_format.get('bid'))
        extracted_formats = []
        if video_format.get('m3u8Url'):
            extracted_formats.extend(self._extract_m3u8_formats(
                urljoin(format_data.get('dm3u8', 'https://cache-m.iq.com/dc/dt/'), video_format['m3u8Url']),
                video_id, 'mp4', m3u8_id=bid, fatal=False))
        if video_format.get('mpdUrl'):
            # TODO: Properly extract mpd hostname
            extracted_formats.extend(self._extract_mpd_formats(
                urljoin(format_data.get('dm3u8', 'https://cache-m.iq.com/dc/dt/'), video_format['mpdUrl']),
                video_id, mpd_id=bid, fatal=False))
        if video_format.get('m3u8'):
            ff = video_format.get('ff', 'ts')
            if ff == 'ts':
                m3u8_formats, _ = self._parse_m3u8_formats_and_subtitles(
                    video_format['m3u8'], ext='mp4', m3u8_id=bid, fatal=False)
                extracted_formats.extend(m3u8_formats)
            elif ff == 'm4s':
                mpd_data = traverse_obj(
                    self._parse_json(video_format['m3u8'], video_id, fatal=False), ('payload', ..., 'data'), expected_type=str)
                if mpd_data:
                    mpd_formats, _ = self._parse_mpd_formats_and_subtitles(
                        mpd_data, bid, format_data.get('dm3u8', 'https://cache-m.iq.com/dc/dt/'))
                    extracted_formats.extend(mpd_formats)
            else:
                self.report_warning(f'{ff} formats are currently not supported')

        for f in extracted_formats:
            f.update({
                'quality': qualities(list(self._BID_TAGS.keys()))(bid),
                'format_note': self._BID_TAGS.get(bid),
                'http_headers': {
                    **(f.get('http_headers') or {}),
                    'Referer': 'https://www.iq.com/',
                },
                **parse_resolution(video_format.get('scrsz')),
            })
        return extracted_formats

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        next_props = self._search_nextjs_data(webpage, video_id)['props']
        page_data = next_props['initialState']['play']
        video_info = page_data['curVideoInfo']

        # iq.com SSR embeds a signed dash payload on geo-available titles.
        # Use it when present so extraction does not depend on PhantomJS.
        initial_format_data = traverse_obj(
            next_props, ('initialProps', 'pageProps', 'prePlayerData', 'dash', 'data'),
            expected_type=dict) or {}
        ssr_st = int_or_none(initial_format_data.get('st'))
        dash_paths = None
        if not (ssr_st and 100 < ssr_st < 200 and traverse_obj(
                initial_format_data, ('program', 'video', ...), expected_type=dict)):
            self._update_bid_tags(webpage, video_id)

            uid = traverse_obj(
                self._parse_json(
                    self._get_cookie('I00002', '{}'), video_id, transform_source=urllib.parse.unquote, fatal=False),
                ('data', 'uid'), default=0)

            if uid:
                vip_data = self._download_json(
                    'https://pcw-api.iq.com/api/vtype', video_id, note='Downloading VIP data', errnote='Unable to download VIP data', query={
                        'batch': 1,
                        'platformId': 3,
                        'modeCode': self._get_cookie('mod', 'intl'),
                        'langCode': self._get_cookie('lang', 'en_us'),
                        'deviceId': self._get_cookie('QC005', ''),
                    }, fatal=False)
                ut_list = traverse_obj(vip_data, ('data', 'all_vip', ..., 'vipType'), expected_type=str_or_none)
            else:
                ut_list = ['0']

            # bid 0 as an initial format checker
            dash_paths = self._parse_json(PhantomJSwrapper(self, timeout=120_000).get(
                url, note2='Executing signature code (this may take a couple minutes)',
                html='<!DOCTYPE html>', video_id=video_id, jscode=self._DASH_JS % {
                    'tvid': video_info['tvId'],
                    'vid': video_info['vid'],
                    'src': traverse_obj(next_props, ('initialProps', 'pageProps', 'ptid'),
                                        expected_type=str, default='04022001010011000000'),
                    'uid': uid,
                    'dfp': self._get_cookie('dfp', ''),
                    'mode': self._get_cookie('mod', 'intl'),
                    'lang': self._get_cookie('lang', 'en_us'),
                    'bid_list': '[' + ','.join(['0', *self._BID_TAGS.keys()]) + ']',
                    'ut_list': '[' + ','.join(ut_list) + ']',
                    'cmd5x_func': self._extract_cmd5x_function(webpage, video_id),
                })[1].strip(), video_id)

            initial_format_data = self._download_json(
                urljoin('https://cache-video.iq.com', dash_paths['0']), video_id,
                note='Downloading initial video format info', errnote='Unable to download initial video format info')['data']

        preview_time = traverse_obj(
            initial_format_data, ('boss_ts', (None, 'data'), ('previewTime', 'rtime')), expected_type=float_or_none, get_all=False)
        if traverse_obj(initial_format_data, ('boss_ts', 'data', 'prv'), expected_type=int_or_none):
            self.report_warning('This preview video is limited{}'.format(format_field(preview_time, None, ' to %s seconds')))

        formats, subtitles = [], {}
        # TODO: Extract audio-only formats
        if dash_paths:
            for bid in set(traverse_obj(initial_format_data, ('program', 'video', ..., 'bid'), expected_type=str_or_none)):
                dash_path = dash_paths.get(bid)
                if not dash_path:
                    self.report_warning(f'Unknown format id: {bid}. It is currently not being extracted')
                    continue
                format_data = traverse_obj(self._download_json(
                    urljoin('https://cache-video.iq.com', dash_path), video_id,
                    note=f'Downloading format data for {self._BID_TAGS.get(bid, bid)}', errnote='Unable to download format data',
                    fatal=False), 'data', expected_type=dict)
                video_format = traverse_obj(format_data, ('program', 'video', lambda _, v: str(v['bid']) == bid),
                                            expected_type=dict, get_all=False) or {}
                extracted_formats = self._extract_program_formats(format_data, video_id, video_format)
                if not extracted_formats:
                    tag = self._BID_TAGS.get(bid, bid)
                    if video_format.get('s'):
                        self.report_warning(f'{tag} format is restricted')
                    else:
                        self.report_warning(f'Unable to extract {tag} format')
                formats.extend(extracted_formats)
        else:
            for video_format in traverse_obj(
                    initial_format_data, ('program', 'video', ...), expected_type=dict):
                extracted_formats = self._extract_program_formats(
                    initial_format_data, video_id, video_format)
                if not extracted_formats and video_format.get('s'):
                    bid = str_or_none(video_format.get('bid'))
                    self.report_warning(f'{self._BID_TAGS.get(bid, bid)} format is restricted')
                formats.extend(extracted_formats)

        for sub_format in traverse_obj(initial_format_data, ('program', 'stl', ...), expected_type=dict):
            lang = self._LID_TAGS.get(str_or_none(sub_format.get('lid')), sub_format.get('_name'))
            subtitles.setdefault(lang, []).extend([{
                'ext': format_ext,
                'url': urljoin(initial_format_data.get('dstl', 'http://meta.video.iqiyi.com'), sub_format[format_key]),
            } for format_key, format_ext in [('srt', 'srt'), ('webvtt', 'vtt')] if sub_format.get(format_key)])

        extra_metadata = page_data.get('albumInfo') if video_info.get('albumId') and page_data.get('albumInfo') else video_info
        return {
            'id': video_id,
            'title': video_info['name'],
            'formats': formats,
            'subtitles': subtitles,
            'description': video_info.get('mergeDesc'),
            'duration': parse_duration(video_info.get('len')),
            'age_limit': parse_age_limit(video_info.get('rating')),
            'average_rating': traverse_obj(page_data, ('playScoreInfo', 'score'), expected_type=float_or_none),
            'timestamp': parse_iso8601(video_info.get('isoUploadDate')),
            'categories': traverse_obj(extra_metadata, ('videoTagMap', ..., ..., 'name'), expected_type=str),
            'cast': traverse_obj(extra_metadata, ('actorArr', ..., 'name'), expected_type=str),
            'episode_number': int_or_none(video_info.get('order')) or None,
            'series': video_info.get('albumName'),
        }


class IqAlbumIE(InfoExtractor):
    IE_NAME = 'iq.com:album'
    _VALID_URL = r'https?://(?:www\.)?iq\.com/album/(?:[\w%-]*-)?(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://www.iq.com/album/knot-2026-f5unp9qy15',
        'info_dict': {
            'id': 'f5unp9qy15',
            'title': 'KNOT',
            'description': 'md5:50805b750c76d5fb751c5d8142fe33fd',
        },
        'playlist_mincount': 8,
    }, {
        'url': 'https://www.iq.com/album/one-piece-1999-1bk9icvr331',
        'info_dict': {
            'id': '1bk9icvr331',
            'title': 'One Piece',
            'description': 'Subtitle available on Sunday 4PM（GMT+8）.',
        },
        'playlist_mincount': 238,
        'skip': 'Geo-restricted',
    }, {
        # Movie/single video
        'url': 'https://www.iq.com/album/九龙城寨-2021-22yjnij099k',
        'info_dict': {
            'ext': 'mp4',
            'id': '22yjnij099k',
            'title': '九龙城寨',
            'description': 'md5:8a09f50b8ba0db4dc69bc7c844228044',
            'duration': 5000,
            'timestamp': 1641911371,
            'upload_date': '20220111',
            'series': '九龙城寨',
            'cast': ['Shi Yan Neng', 'Yu Lang', 'Peter  lv', 'Sun Zi Jun', 'Yang Xiao Bo'],
            'age_limit': 13,
            'average_rating': float,
        },
        'expected_warnings': ['format is restricted'],
        'skip': 'Geo-restricted',
    }]

    def _entries(self, album_id_num, page_ranges, album_id=None, mode_code='intl', lang_code='en_us'):
        for page_range in page_ranges:
            page = self._download_json(
                f'https://pcw-api.iq.com/api/episodeListSource/{album_id_num}', album_id,
                note=f'Downloading video list episodes {page_range.get("msg", "")}',
                errnote='Unable to download video list', query={
                    'platformId': 3,
                    'modeCode': mode_code,
                    'langCode': lang_code,
                    'endOrder': page_range['to'],
                    'startOrder': page_range['from'],
                })
            for video in page['data']['epg']:
                yield self.url_result('https://www.iq.com/play/%s' % (video.get('playLocSuffix') or video['qipuIdStr']),
                                      IqIE.ie_key(), video.get('qipuIdStr'), video.get('name'))

    def _real_extract(self, url):
        album_id = self._match_id(url)
        webpage = self._download_webpage(url, album_id)
        next_data = self._search_nextjs_data(webpage, album_id)
        album_data = next_data['props']['initialState']['album']['videoAlbumInfo']

        if album_data.get('videoType') == 'singleVideo':
            return self.url_result(f'https://www.iq.com/play/{album_id}', IqIE.ie_key())
        return self.playlist_result(
            self._entries(album_data['albumId'], album_data['totalPageRange'], album_id,
                          traverse_obj(next_data, ('props', 'initialProps', 'pageProps', 'modeCode')),
                          traverse_obj(next_data, ('props', 'initialProps', 'pageProps', 'langCode'))),
            album_id, album_data.get('name'), album_data.get('desc'))
