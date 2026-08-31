from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    url_or_none,
    urljoin,
)
from ..utils.traversal import require, traverse_obj


class CablecastIE(InfoExtractor):
    IE_NAME = 'cablecast'
    IE_DESC = 'Cablecast'
    _VALID_URL = [
        r'https?://(?P<host>[\w.-]+)/(?:[Cc]ablecast[Aa]pi/embed(?:\.html)?\?(?:[^#]*&)?show_id=|CablecastPublicSite/show/)(?P<id>\d+)',
        r'https?://(?P<host>[\w.-]*cablecast\.tv)/internetchannel/(?:watch-vod-embed\?(?:[^#]*&)?showId=|show/)(?P<id>\d+)',
    ]
    _EMBED_REGEX = [
        r'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://[^"\']+/(?:[Cc]ablecast[Aa]pi/embed\?(?:[^"\']*&)?show_id=|internetchannel/watch-vod-embed\?(?:[^"\']*&)?showId=)\d+[^"\']*)\1',
    ]
    _TESTS = [{
        'url': 'https://reflect-wctv-village-willmette.cablecast.tv/cablecastapi/embed?show_id=532',
        'md5': 'eb6dc0c761be272c0879c9e8997be2e4',
        'info_dict': {
            'id': '532',
            'ext': 'mp4',
            'title': 'Village Board Meeting 4/24/24',
            'thumbnail': 'https://reflect-wctv-village-willmette.cablecast.tv/cablecastapi/dynamicthumbnails/2248',
            'duration': 12784,
            'timestamp': 1713934800,
            'upload_date': '20240424',
            'view_count': int,
            'age_limit': 0,
            'subtitles': 'count:1',
        },
        'params': {'format': 'http'},
    }, {
        'url': 'https://reflect-wctv-village-willmette.cablecast.tv/internetchannel/show/532',
        'only_matching': True,
    }, {
        'url': 'https://reflect-wctv-village-willmette.cablecast.tv/internetchannel/watch-vod-embed?showId=532',
        'only_matching': True,
    }, {
        'url': 'https://wctv.wilmette.com/CablecastPublicSite/show/532',
        'only_matching': True,
    }, {
        'url': 'https://wctv.wilmette.com/cablecastapi/embed?show_id=532',
        'only_matching': True,
    }]

    def _call_api(self, url, path, video_id, **kwargs):
        return self._download_json(
            urljoin(url, f'/cablecastapi/v1/{path}'), video_id, **kwargs)

    def _extract_vod_formats(self, media_url, video_id, has_captions=False):
        formats, subtitles = [], {}
        ext = determine_ext(media_url)
        hls_url = media_url
        if ext == 'mp4':
            formats.append({
                'url': media_url,
                'ext': 'mp4',
                'format_id': 'http',
            })
            hls_url = f'{media_url[:-3]}m3u8'
        if determine_ext(hls_url) == 'm3u8':
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
        if has_captions:
            caption_url = urljoin(media_url, 'captions.en.vtt')
            if caption_url and caption_url != media_url:
                self._merge_subtitles(
                    {'en': [{'url': caption_url, 'ext': 'vtt'}]}, target=subtitles)
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        show = traverse_obj(
            self._call_api(url, f'shows/{video_id}', video_id),
            ('show', {dict}, {require('show data')}))

        if show.get('restrictAccessToMembers'):
            self.raise_login_required('This video is restricted to members')

        vod = None
        for vod_id in traverse_obj(show, ('vods', ..., {int_or_none})):
            candidate = traverse_obj(
                self._call_api(url, f'vods/{vod_id}', vod_id, fatal=False),
                ('vod', {dict}))
            if not candidate or candidate.get('disabled'):
                continue
            if candidate.get('isWatchable') is False:
                continue
            if url_or_none(candidate.get('url') or candidate.get('localUrl')):
                vod = candidate
                break
        if not vod:
            self.raise_no_formats(
                'No VOD available for this show', expected=True, video_id=video_id)

        media_url = url_or_none(vod.get('url') or vod.get('localUrl'))
        formats, subtitles = self._extract_vod_formats(
            media_url, video_id, has_captions=bool(show.get('hasCaptions')))
        if not formats:
            self.raise_no_formats('No playable formats', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'view_count': traverse_obj(vod, ('views', {int_or_none})),
            **traverse_obj(show, {
                'title': (('title', 'cgTitle'), {str}, any),
                'description': ('comments', {str}),
                'thumbnail': ('thumbnailImage', 'url', {url_or_none}),
                'duration': ('totalRunTime', {int_or_none}),
                'timestamp': (('eventDate', 'created'), {parse_iso8601}, any),
                'age_limit': ('ageRating', {int_or_none}),
            }),
        }
