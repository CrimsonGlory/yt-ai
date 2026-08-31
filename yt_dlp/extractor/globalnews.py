import json
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    float_or_none,
    int_or_none,
    merge_dicts,
    parse_iso8601,
    traverse_obj,
    url_or_none,
    urljoin,
)


class GlobalNewsIE(InfoExtractor):
    IE_NAME = 'globalnews'
    IE_DESC = 'Global News'
    _VALID_URL = (
        r'https?://(?:www\.)?globalnews\.ca/(?:video/)?live/(?P<live_id>[^/?#]+)',
        r'https?://(?:www\.)?globalnews\.ca/video/(?:embed/)?(?P<id>\d+)',
    )
    _TESTS = [{
        'url': 'https://globalnews.ca/video/12039677/doctors-caution-extreme-heat-risk-for-heart-attacks-strokes/',
        'md5': '3e803ae4153698b42225dd18b8381682',
        'info_dict': {
            'id': '12039677',
            'ext': 'mp4',
            'title': 'Doctors caution extreme heat risk for heart attacks, strokes',
            'description': 'md5:775aa58eae73843a680ddccba3a49f99',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'duration': 122,
            'timestamp': 1788163200,
            'upload_date': '20260831',
        },
    }, {
        'url': 'https://globalnews.ca/video/embed/12039677/',
        'only_matching': True,
    }, {
        'url': 'https://globalnews.ca/live/national/',
        'only_matching': True,
    }, {
        'url': 'https://globalnews.ca/video/live/national-ott/',
        'only_matching': True,
    }]

    @staticmethod
    def _quote_url(url):
        parts = urllib.parse.urlsplit(url)
        return urllib.parse.urlunsplit((
            parts.scheme, parts.netloc,
            urllib.parse.quote(parts.path, safe='/%'),
            parts.query, parts.fragment))

    def _add_source(self, source, video_id, formats, subtitles, is_live=False):
        src = traverse_obj(source, ('file', {url_or_none}), ('url', {url_or_none}))
        if not src or 'link.theplatform.com' in src:
            return
        src_type = (traverse_obj(source, ('type', {str})) or determine_ext(src) or '').lower()
        if src_type in ('m3u8', 'hls') or 'delivery_protocol=hls' in src or src.endswith('.m3u8'):
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                src, video_id, 'mp4', m3u8_id='hls', fatal=False, live=is_live)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        elif src_type in ('mpd', 'dash') or 'delivery_protocol=dash' in src:
            fmts, subs = self._extract_mpd_formats_and_subtitles(
                src, video_id, mpd_id='dash', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        elif src_type == 'mp4' or determine_ext(src) == 'mp4':
            formats.append({
                'url': src,
                'ext': 'mp4',
            })

    def _extract_feed_entry(self, feed_url, video_id):
        feed = self._download_json(
            self._quote_url(feed_url), video_id,
            'Downloading video entry JSON', fatal=False)
        if isinstance(feed, list):
            return traverse_obj(feed, (0, {dict})) or {}
        return feed if isinstance(feed, dict) else {}

    def _real_extract(self, url):
        groups = self._match_valid_url(url).groupdict()
        video_id = groups.get('id') or groups['live_id']
        webpage = self._download_webpage(url, video_id)
        settings = self._search_json(
            r'window\.gncaVideoPlayerSettings\s*=', webpage,
            'player settings', video_id, default={})

        formats, subtitles = [], {}
        is_live = bool(groups.get('live_id')) or traverse_obj(settings, ('isLive', {bool}))

        for source in traverse_obj(settings, ('jw', 'playlist', 0, 'sources', ..., {dict})):
            self._add_source(source, video_id, formats, subtitles, is_live=is_live)

        feed_url = traverse_obj(settings, ('jw', 'feedUrl', {str}))
        media_id = traverse_obj(settings, ('jw', 'mediaId', {str}))
        entry = {}
        if feed_url and 'video-entry' in feed_url:
            entry = self._extract_feed_entry(urljoin(url, feed_url), video_id)
        elif not formats and media_id:
            quoted = urllib.parse.quote(json.dumps({'id': media_id}, separators=(',', ':')))
            entry = self._extract_feed_entry(
                urljoin(url, f'/gnca-ajax-redesign/video-entry/{quoted}/'), video_id)

        if traverse_obj(entry, ('drm', {bool})):
            self.report_drm(video_id)
        is_live = is_live or traverse_obj(entry, ('metadata', 'liveStream', {bool})) or False
        for source in traverse_obj(entry, ('sources', ..., {dict})):
            self._add_source(source, video_id, formats, subtitles, is_live=is_live)

        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        ld_url = url_or_none(json_ld.pop('url', None))
        if ld_url and not any(f.get('url') == ld_url for f in formats):
            formats.append({
                'url': ld_url,
                'ext': determine_ext(ld_url, 'mp4'),
            })

        if not formats:
            raise ExtractorError('No video formats found', expected=True)

        playlist_item = traverse_obj(settings, ('jw', 'playlist', 0, {dict})) or {}
        keywords = (
            traverse_obj(playlist_item, ('keywords', {str}))
            or traverse_obj(entry, ('keywords', {str})))
        tags = [t.strip() for t in keywords.split(',') if t.strip()] if keywords else None

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live or None,
            'title': (
                traverse_obj(playlist_item, ('title', {str}))
                or traverse_obj(entry, ('title', {str}))),
            'description': (
                traverse_obj(playlist_item, ('description', {str}))
                or traverse_obj(entry, ('description', {str}))),
            'thumbnail': (
                traverse_obj(playlist_item, ('image', {url_or_none}))
                or traverse_obj(
                    entry, (('image', 'defaultThumbnailUrl', 'thumbnail'), {url_or_none}),
                    get_all=False)),
            'duration': (
                float_or_none(traverse_obj(playlist_item, ('metadata', 'duration')))
                or float_or_none(traverse_obj(entry, ('metadata', 'duration'))) or None),
            'timestamp': (
                parse_iso8601(traverse_obj(playlist_item, ('metadata', 'airDate')))
                or int_or_none(traverse_obj(entry, 'pubDate'), scale=1000)),
            'tags': tags,
        }, json_ld)
