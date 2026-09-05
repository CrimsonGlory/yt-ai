import base64

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_id,
    int_or_none,
    js_to_json,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class IxiguaIE(InfoExtractor):
    IE_DESC = '西瓜视频'
    _VALID_URL = r'https?://(?:\w+\.)?ixigua\.com/(?:video/)?(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.ixigua.com/6996881461559165471',
        'info_dict': {
            'id': '6996881461559165471',
            'ext': 'mp4',
            'title': '盲目涉水风险大，亲身示范高水位行车注意事项',
            'description': '本期《懂车帝评测》，我们将尝试验证一个夏日大家可能会遇到的关键性问题：如果突发暴雨，我们不得不涉水行车，如何做才能更好保障生命安全。',
            'uploader': '懂车帝原创',
            'uploader_id': '6480145787',
            'duration': 1030,
            # Signed ByteDance image CDN host/query rotate between requests
            'thumbnail': r're:https?://.+',
            'timestamp': 1629088414,
            'upload_date': '20210816',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'tags': list,
        },
        # 10KiB test-mode Range fetches from rotating xgwap CDNs flake under load
        'params': {'skip_download': True},
    }]
    _GOOGLEBOT_USER_AGENT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

    @staticmethod
    def _decode_play_url(encoded):
        if not encoded:
            return None
        if encoded.startswith('http'):
            return encoded
        try:
            decoded = base64.b64decode(encoded).decode()
        except (ValueError, UnicodeDecodeError):
            return None
        return decoded if decoded.startswith('http') else None

    def _get_json_data(self, webpage, video_id):
        js_data = get_element_by_id('SSR_HYDRATED_DATA', webpage)
        if not js_data:
            if self._cookies_passed:
                raise ExtractorError('Failed to get SSR_HYDRATED_DATA')
            raise ExtractorError('Cookies (not necessarily logged in) are needed', expected=True)

        js_data = js_data.replace('window._SSR_HYDRATED_DATA=', '')
        return self._parse_json(js_data, video_id, transform_source=js_to_json)

    def _media_selector(self, json_data):
        for path, override in (
            (('video_list', ), {}),
            (('dynamic_video', 'dynamic_video_list'), {'acodec': 'none'}),
            (('dynamic_video', 'dynamic_audio_list'), {'vcodec': 'none', 'ext': 'm4a'}),
        ):
            for media in traverse_obj(json_data, (..., *path, lambda _, v: v['main_url'])):
                url = self._decode_play_url(media['main_url'])
                if not url:
                    continue
                yield {
                    'url': url,
                    'width': int_or_none(media.get('vwidth')),
                    'height': int_or_none(media.get('vheight')),
                    'fps': int_or_none(media.get('fps')),
                    'vcodec': media.get('codec_type'),
                    'format_id': str_or_none(media.get('quality_type') or media.get('definition')),
                    'filesize': int_or_none(media.get('size')),
                    'ext': media.get('vtype') or 'mp4',
                    **override,
                }

    def _formats_from_play_info(self, play_info, video_id):
        if isinstance(play_info, str):
            play_info = self._parse_json(play_info, video_id, fatal=False)
        formats = []
        for media in traverse_obj(play_info, ('video_list', ..., {dict})):
            for url_key in ('main_url', 'backup_url_1', 'backup_url'):
                url = self._decode_play_url(media.get(url_key))
                if not url:
                    continue
                formats.append({
                    'url': url,
                    'format_id': str_or_none(media.get('definition') or media.get('quality_type')),
                    'width': int_or_none(media.get('vwidth')),
                    'height': int_or_none(media.get('vheight')),
                    'fps': int_or_none(media.get('fps')),
                    'vcodec': media.get('codec_type'),
                    'filesize': int_or_none(media.get('size')),
                    'tbr': int_or_none(media.get('bitrate') or media.get('real_bitrate'), scale=1000),
                    'ext': media.get('vtype') or 'mp4',
                    'quality': -1 if url_key != 'main_url' else None,
                    'http_headers': {'Referer': 'https://www.ixigua.com/'},
                })
        return formats

    def _find_video_item(self, obj, video_id):
        if isinstance(obj, dict):
            ids = {str(obj[k]) for k in ('gid', 'item_id', 'group_id') if obj.get(k) is not None}
            if video_id in ids and obj.get('video_play_info'):
                return obj
            for value in obj.values():
                found = self._find_video_item(value, video_id)
                if found:
                    return found
        elif isinstance(obj, list):
            for value in obj:
                found = self._find_video_item(value, video_id)
                if found:
                    return found
        return None

    def _extract_from_ssr_data(self, webpage, video_id):
        ssr_data = self._search_json(
            r'window\._SSR_DATA\s*=', webpage, 'SSR data', video_id,
            end_pattern=r';?\s*</script>', default=None)
        if not ssr_data:
            return None

        item = self._find_video_item(ssr_data, video_id)
        result = traverse_obj(ssr_data, (
            'data', 'storeState', 'detail', 'videoData', 'result', {dict})) or {}
        formats = self._formats_from_play_info(
            traverse_obj(item, 'video_play_info'), video_id) if item else []
        if not formats:
            return None

        return {
            'id': video_id,
            'formats': formats,
            'title': traverse_obj(item, 'title') or result.get('title'),
            'description': (
                traverse_obj(item, 'abstract')
                or result.get('abstract') or result.get('video_abstract')),
            'duration': (
                int_or_none(traverse_obj(item, 'video_duration'))
                or int_or_none(result.get('duration'))),
            'timestamp': (
                int_or_none(traverse_obj(item, 'publish_time'))
                or int_or_none(result.get('publish_time'))),
            'like_count': int_or_none(traverse_obj(
                item, 'video_like_count', 'digg_count',
                default=result.get('video_like_count'))),
            'dislike_count': int_or_none(traverse_obj(
                item, 'bury_count', default=result.get('video_unlike_count'))),
            'view_count': int_or_none(traverse_obj(
                item, ('video_detail_info', 'video_watch_count'),
                default=result.get('play_count'))),
            'comment_count': int_or_none(traverse_obj(
                item, 'comment_count', default=result.get('comment_count'))),
            'uploader': traverse_obj(
                item, ('user_info', 'name'), 'media_name', 'source',
                default=traverse_obj(result, ('media_user', 'screen_name'))),
            'uploader_id': str_or_none(traverse_obj(
                item, ('user_info', 'user_id'), ('media_info', 'user_id'),
                default=traverse_obj(result, ('media_user', 'id')))),
            'thumbnail': url_or_none(traverse_obj(
                item, ('large_image_list', 0, 'url'), ('middle_image', 'url'),
                default=result.get('cover_image_url'))),
            'tags': traverse_obj(result, ('video_tags', ..., {str})) or [
                traverse_obj(item, 'tag') or result.get('tag')],
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers={
            # ByteDance serves an interstitial JS VM challenge to ordinary browser
            # clients; search-engine crawlers get SSR JSON with playable URLs
            'User-Agent': self._GOOGLEBOT_USER_AGENT,
        })

        info = self._extract_from_ssr_data(webpage, video_id)
        if info and info.get('formats'):
            return info

        json_data = self._get_json_data(webpage, video_id)['anyVideo']['gidInformation']['packerData']['video']
        formats = list(self._media_selector(json_data.get('videoResource')))
        return {
            'id': video_id,
            'title': json_data.get('title'),
            'description': json_data.get('video_abstract'),
            'formats': formats,
            'like_count': json_data.get('video_like_count'),
            'duration': int_or_none(json_data.get('duration')),
            'tags': [json_data.get('tag')],
            'uploader_id': traverse_obj(json_data, ('user_info', 'user_id')),
            'uploader': traverse_obj(json_data, ('user_info', 'name')),
            'view_count': json_data.get('video_watch_count'),
            'dislike_count': json_data.get('video_unlike_count'),
            'timestamp': int_or_none(json_data.get('video_publish_time')),
        }
