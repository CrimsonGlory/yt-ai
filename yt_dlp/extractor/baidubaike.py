import urllib.parse

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_qs,
    qualities,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BaiduBaikeIE(InfoExtractor):
    IE_NAME = 'baidubaike'
    IE_DESC = '百度百科'
    _VALID_URL = r'https?://(?:www\.)?baike\.baidu\.com/item/(?P<slug>[^/?#]+)(?:/(?P<id>\d+))?'
    _API_HEADERS = {
        'Referer': 'https://baike.baidu.com/',
        'Accept': 'application/json, text/plain, */*',
    }
    _TESTS = [
        {
            'url': 'https://baike.baidu.com/item/%E7%A7%92%E6%87%82%E4%BA%94%E5%8D%83%E5%B9%B4?secondId=512408',
            'md5': '19bd85e63bd809e97c55884eea4c74e6',
            'info_dict': {
                'id': '512408',
                'ext': 'mp4',
                'title': '秒懂五千年:四凶都有啥？',
                'alt_title': '秒懂五千年:四凶都有啥？',
                'thumbnail': r're:https?://.+',
                'duration': 148,
                'timestamp': 1579220663,
                'upload_date': '20200117',
                'uploader': '秒懂五千年',
            },
        },
        {
            'url': 'https://baike.baidu.com/item/%E7%A7%92%E6%87%82%E4%BA%94%E5%8D%83%E5%B9%B4',
            'info_dict': {
                'id': '22637356',
                'title': '秒懂五千年',
                'description': 'md5:2705e071bb06bb8189a88963a3ea2ae0',
            },
            'playlist_mincount': 10,
        },
        {
            'url': 'https://baike.baidu.com/item/%E7%A7%92%E6%87%82%E4%BA%94%E5%8D%83%E5%B9%B4/22637356',
            'only_matching': True,
        },
    ]

    def _call_api(self, path, video_id, query, note='Downloading API JSON', fatal=True):
        data = self._download_json(
            f'https://baike.baidu.com/api/{path}',
            video_id,
            note,
            query=query,
            impersonate=True,
            fatal=fatal,
            headers=self._API_HEADERS,
        )
        if not data:
            return {}
        errno = data.get('errno')
        if errno not in (0, None, '0'):
            errmsg = data.get('errmsg') or f'API error {errno}'
            if fatal:
                self.raise_no_formats(errmsg, expected=True, video_id=video_id)
            self.report_warning(errmsg, video_id=video_id)
            return {}
        return data

    def _extract_formats(self, item, video_id):
        formats, urls = [], set()
        quality_key = qualities(('mini', 'sc', 'hd', '1080p'))

        def add_url(media_url, format_id, quality=None, vcodec=None):
            media_url = url_or_none(media_url)
            if not media_url or media_url in urls:
                return
            urls.add(media_url)
            ext = determine_ext(media_url, 'mp4')
            if ext == 'm3u8':
                formats.extend(
                    self._extract_m3u8_formats(media_url, video_id, 'mp4', m3u8_id=format_id or 'hls', fatal=False),
                )
                return
            formats.append(
                {
                    'url': media_url,
                    'format_id': format_id,
                    'ext': ext,
                    'quality': quality,
                    'vcodec': vcodec,
                },
            )

        content = item.get('content') if isinstance(item.get('content'), dict) else {}
        sources = (content, item)
        for src in sources:
            for quality, media_url in (traverse_obj(src, ('playUrls', 'mp4', {dict})) or {}).items():
                add_url(media_url, f'mp4-{quality}', quality_key(quality))
            play_url = src.get('playUrl')
            if isinstance(play_url, dict):
                add_url(play_url.get('mp4'), 'mp4', quality_key('hd'))
                add_url(play_url.get('h265Mp4'), 'mp4-h265', quality_key('hd'), 'hevc')
                add_url(play_url.get('hls'), 'hls')
            elif isinstance(play_url, str):
                add_url(play_url, 'hls' if determine_ext(play_url) == 'm3u8' else 'mp4')
            add_url(src.get('playMp4Url'), 'mp4', quality_key('hd'))

        return formats

    def _parse_video(self, item, fallback_id=None):
        if not isinstance(item, dict):
            return None
        content = item['content'] if isinstance(item.get('content'), dict) else {}
        second_id = int_or_none(item.get('secondId')) or int_or_none(content.get('secondId'))
        video_id = (str(second_id) if second_id else None) or str_or_none(
            traverse_obj(
                content,
                'nid',
                'mediaId',
            )
            or traverse_obj(item, 'nid', 'mediaId')
            or fallback_id,
        )
        if not video_id:
            return None

        formats = self._extract_formats(item, video_id)
        if not formats:
            return None

        title = traverse_obj(content, 'title', {str}) or traverse_obj(item, 'title', {str})
        description = (
            traverse_obj(content, 'description', {str})
            or traverse_obj(content, 'subTitle', {str})
            or traverse_obj(item, 'subTitle', {str})
        )
        if description == title:
            description = None

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'alt_title': traverse_obj(content, 'subTitle', {str}) or traverse_obj(item, 'subTitle', {str}),
            'description': description,
            'thumbnail': traverse_obj(content, ('cover', 'url', {url_or_none}))
            or traverse_obj(item, ('coverPic', 'imageUrl', {url_or_none})),
            'duration': int_or_none(content.get('duration')) or int_or_none(item.get('intPlayTime')),
            'timestamp': int_or_none(item.get('publishTime')) or int_or_none(item.get('createTime')),
            'uploader': traverse_obj(item, 'uname', 'createUname', 'displayname', {str}),
        }

    def _extract_video_info(self, second_id):
        data = self._call_api(
            'second/video/info',
            second_id,
            {'secondIds': second_id},
            'Downloading video JSON',
            fatal=False,
        )
        video = traverse_obj(data, ('data', 'list', 0, {dict}))
        if video:
            return video

        data = self._call_api(
            'wikisecond/playurl',
            second_id,
            {'secondId': second_id},
            'Downloading play URL JSON',
            fatal=False,
        )
        return {
            'secondId': int_or_none(second_id),
            'playMp4Url': traverse_obj(data, ('list', 'mp4Url', {url_or_none})),
            'playUrl': traverse_obj(data, ('list', 'hlsUrl', {url_or_none})),
        }

    def _extract_lemmasecond(self, lemma_id):
        data = self._call_api(
            'wikisecond/lemmasecond',
            lemma_id,
            {'lemmaId': lemma_id},
            'Downloading 秒懂 JSON',
            fatal=False,
        )
        return traverse_obj(data, ('list', ..., ..., {dict})) or []

    def _extract_video_list(self, lemma_id):
        data = self._call_api(
            'second/video/list',
            lemma_id,
            {
                'lemmaId': lemma_id,
                'isSensitive': '0',
                'scene': 'pc_top',
                'rn': '15',
                'strategy': '1',
            },
            'Downloading video list JSON',
            fatal=False,
        )
        return traverse_obj(data, ('data', 'list', ..., {dict})) or []

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        lemma_id, slug = mobj.group('id'), mobj.group('slug')
        display_id = lemma_id or urllib.parse.unquote(slug)
        second_id = traverse_obj(parse_qs(url), ('secondId', 0), ('secondid', 0), {str})
        if second_id == '0':
            second_id = None

        if second_id:
            info = self._parse_video(self._extract_video_info(second_id), second_id)
            if not info:
                self.raise_no_formats('No video formats', expected=True, video_id=second_id)
            return info

        lemma_title = urllib.parse.unquote(slug)
        lemma_desc = None
        if not lemma_id:
            webpage = self._download_webpage(
                url,
                display_id,
                impersonate=True,
                headers={'Referer': 'https://baike.baidu.com/'},
            )
            page_data = self._search_json(r'window\.PAGE_DATA\s*=', webpage, 'page data', display_id, default={})
            lemma_id = self._html_search_regex(
                r'data-lemmaid=["\'](\d+)',
                webpage,
                'lemma id',
                default=None,
            ) or str_or_none(page_data.get('lemmaId'))
            lemma_title = (
                traverse_obj(page_data, 'lemmaTitle', {str})
                or self._og_search_title(webpage, default=None)
                or lemma_title
            )
            lemma_desc = self._og_search_description(webpage, default=None) or traverse_obj(
                page_data, 'description', {str})
            if not lemma_id:
                self.raise_no_formats('Unable to extract lemma id', expected=True, video_id=display_id)
            display_id = lemma_id

        entries = []
        for video in self._extract_lemmasecond(lemma_id) or self._extract_video_list(lemma_id):
            info = self._parse_video(video)
            if info:
                entries.append(info)

        if not entries:
            self.raise_no_formats('No videos found for this lemma', expected=True, video_id=lemma_id)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, lemma_id, lemma_title, lemma_desc)
