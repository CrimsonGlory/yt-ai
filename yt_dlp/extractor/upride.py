from .common import InfoExtractor
from ..utils import unescapeHTML, url_or_none
from ..utils.traversal import traverse_obj


class UprideIE(InfoExtractor):
    IE_NAME = 'upride'
    IE_DESC = 'UpRide.cc'
    _VALID_URL = r'https?://(?:www\.)?upride\.cc/incident/(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://upride.cc/incident/shoulder-pass-at-light/',
        'md5': 'd137f3318075c09a08fe0b68a0b7cefc',
        'info_dict': {
            'id': 'shoulder-pass-at-light',
            'ext': 'mp4',
            'title': 'Shoulder Pass at Light',
            'description': 'Car riding on shoulder, comes up behind me at red light to make a right turn at frame 4:47 to 5:03.. Caught on the Cycliq Fly6.',
            'duration': 75,
            'timestamp': 1686832761,
            'upload_date': '20230615',
            'thumbnail': 'https://upride.cc/wp-content/uploads/incidents/eaef9dea5159cf968be84241b5cedfe7.jpg',
            'view_count': int,
        },
        'params': {'format': 'http-orig'},
    }, {
        'url': 'https://upride.cc/incident/car-didnt-see-me-2/',
        'only_matching': True,
    }, {
        'url': 'https://www.upride.cc/incident/dog-2/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)

        original_url = None
        for ld in self._yield_json_ld(webpage, video_id, fatal=False):
            original_url = traverse_obj(ld, (
                ('contentURL', 'contentUrl'), {unescapeHTML}, {url_or_none}), get_all=False)
            if original_url:
                break

        cf_id = self._search_regex(
            r'(?:customer-[\w-]+\.)?cloudflarestream\.com/([\da-f]{32})',
            webpage, 'cloudflare stream id', default=None)

        formats, subtitles = [], {}
        if original_url:
            formats.append({
                'url': original_url,
                'format_id': 'http-orig',
                'impersonate': True,
            })
        if cf_id:
            manifest_base = f'https://cloudflarestream.com/{cf_id}/manifest/video.'
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                manifest_base + 'm3u8', video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
            dash_fmts, dash_subs = self._extract_mpd_formats_and_subtitles(
                manifest_base + 'mpd', video_id, mpd_id='dash', fatal=False)
            formats.extend(dash_fmts)
            self._merge_subtitles(dash_subs, target=subtitles)

        if not formats:
            self.raise_no_formats(
                'No Cloudflare Stream embed or original media URL found', expected=True)

        if not json_ld.get('title'):
            json_ld['title'] = self._og_search_title(webpage)
        if not json_ld.get('description'):
            json_ld['description'] = self._og_search_description(webpage)
        if not traverse_obj(json_ld, ('thumbnails', 0, 'url')):
            json_ld['thumbnail'] = self._og_search_thumbnail(webpage)

        return {
            **json_ld,
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        }
