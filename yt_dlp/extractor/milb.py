from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_duration,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class MiLBIE(InfoExtractor):
    IE_NAME = 'milb'
    IE_DESC = 'Minor League Baseball'
    _VALID_URL = r'https?://(?:www\.)?milb\.com/(?:[^/?#]+/)*video/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.milb.com/eugene/video/brett-auerbach-s-acrobatic-catch',
        'md5': 'e7c110a7218a14eb96ce46353ce9a77a',
        'info_dict': {
            'id': 'e5b386a4-6ee784b6-a19d24-prod-milb-diamond-asset',
            'ext': 'mp4',
            'display_id': 'brett-auerbach-s-acrobatic-catch',
            'title': "Brett Auerbach's acrobatic catch",
            'description': 'md5:42877eedba98112c1b2da5a7d73751f1',
            'duration': 67,
            'timestamp': 1689996227,
            'upload_date': '20230722',
            'thumbnail': r're:https?://img\.mlbstatic\.com/.+',
            'tags': ['T461@T419 7/22/2023', 'Eugene Emeralds', 'Brett Auerbach',
                     'Send to News MiLB feed', 'highlight', 'defense', 'five star play',
                     'Giants Affiliate', 'Plays of the Week'],
        },
        'params': {'format': 'mp4Avc'},
    }, {
        'url': 'https://www.milb.com/video/logan-vanwey-in-play-run-s-to-jared-dickey',
        'only_matching': True,
    }, {
        'url': 'https://www.milb.com/eugene/video/hayden-birdsong-s-seven-k-s?t=t461-default-vtp',
        'only_matching': True,
    }]

    def _extract_formats_and_subtitles(self, playbacks, video_id):
        formats, subtitles, urls = [], {}, set()
        for playback in traverse_obj(playbacks, (..., {dict})):
            playback_url = url_or_none(playback.get('url'))
            if not playback_url or playback_url in urls:
                continue
            urls.add(playback_url)
            ext = determine_ext(playback_url)
            format_id = playback.get('name')
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    playback_url, video_id, 'mp4', m3u8_id=format_id, fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext in ('mp4', 'm4a', 'mp3'):
                formats.append({
                    'format_id': format_id,
                    'url': playback_url,
                    'width': int_or_none(playback.get('width')),
                    'height': int_or_none(playback.get('height')),
                })
        return formats, subtitles

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        init_data = self._search_json(
            r'window\.INIT_DATA\s*=', webpage, 'init data', display_id,
            contains_pattern=r'"(?:\\.|[^"\\])*"')
        if isinstance(init_data, str):
            init_data = self._parse_json(init_data, display_id)
        clip = traverse_obj(init_data, ('clip', 'data', {dict}))
        if not clip:
            self.raise_no_formats('Unable to extract clip data', expected=True, video_id=display_id)

        video_id = traverse_obj(clip, (
            ('mediaPlaybackId', 'guid', 'id'), {str}, any)) or display_id
        formats, subtitles = self._extract_formats_and_subtitles(clip.get('playbacks'), video_id)
        if not formats:
            fallback_url = url_or_none(clip.get('url'))
            if fallback_url:
                formats, subtitles = self._extract_formats_and_subtitles(
                    [{'name': 'http', 'url': fallback_url}], video_id)
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(clip, {
                'title': ('title', {str}),
                'description': (('description', 'blurb'), {str}, any),
                'duration': ('duration', {parse_duration}),
                'timestamp': (('date', 'createdOn', 'lastPublish'), {parse_iso8601}, any),
                'thumbnail': ('image', 'cuts', ..., 'src', {url_or_none}, any),
                'tags': ('keywordsDisplay', ..., 'displayName', {str}, all),
            }),
        }
