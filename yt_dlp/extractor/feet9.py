from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    merge_dicts,
    remove_end,
    url_or_none,
    urljoin,
)


class Feet9IE(InfoExtractor):
    IE_DESC = 'Feet9'
    _VALID_URL = (
        r'https?://(?:www\.)?feet9\.com/(?:[a-z]{2}(?:-[a-z]{2})/)?(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?/?(?:[?#]|$)',
        r'https?://(?:www\.)?feet9\.com/modules/video/player/embed\.php\?(?:[^#]*&)?id=(?P<id>\d+)',
    )
    _EMBED_REGEX = [r'<iframe[^>]+\bsrc=["\'](?P<url>https?://(?:www\.)?feet9\.com/modules/video/player/embed\.php\?[^"\']*id=\d+[^"\']*)']
    _TESTS = [{
        'url': 'https://www.feet9.com/22978/cute-girlfriends-foot-worship/',
        'md5': '26579b1b89e485d4df91c0f01b21a2ae',
        'info_dict': {
            'id': '22978',
            'ext': 'mp4',
            'display_id': 'cute-girlfriends-foot-worship',
            'title': 'Cute Girlfriends Foot Worship',
            'description': 'Cute Girlfriends Foot Worship',
            'thumbnail': r're:https?://cdn1s\.feet9\.com/media/videos/tmb/.+\.jpg',
            'duration': 203,
            'timestamp': 1776717780,
            'upload_date': '20260420',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'categories': ['Lesbian feet'],
            'uploader': 'Girlfriends Feet',
            'uploader_id': 'girlfriends-feet',
            'uploader_url': 'https://www.feet9.com/channel/girlfriends-feet/',
            'age_limit': 18,
        },
    }, {
        'url': 'https://www.feet9.com/modules/video/player/embed.php?id=22978',
        'only_matching': True,
    }, {
        'url': 'https://www.feet9.com/22978/',
        'only_matching': True,
    }, {
        'url': 'https://www.feet9.com/fr/22978/filles-mignonnes-adorant-les-pieds/',
        'only_matching': True,
    }, {
        'url': 'https://feet9.com/22978/cute-girlfriends-foot-worship/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.groupdict().get('display_id')

        # Embed pages AES-wrap the JWPlayer URL; the canonical video page
        # exposes a tokened MP4 in JSON-LD and the Video.js <source>.
        if '/embed.php' in url:
            url = f'https://www.feet9.com/{video_id}/'
        webpage = self._download_webpage(url, video_id)

        json_ld = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        video_url = url_or_none(json_ld.pop('url', None))
        json_ld.pop('ext', None)

        if not video_url:
            video_url = url_or_none(self._html_search_regex(
                r'<source[^>]+\bsrc=["\']([^"\']+\.mp4[^"\']*)',
                webpage, 'video url', default=None))
        if not video_url:
            for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
                for fmt in entry.get('formats') or []:
                    video_url = url_or_none(fmt.get('url'))
                    if video_url:
                        break
                if video_url:
                    break
        if not video_url:
            raise ExtractorError('No video source found', expected=True)

        title = (
            json_ld.get('title')
            or self._html_search_regex(
                r'<h1[^>]+id="zonetitle"[^>]*>([^<]+)', webpage, 'title', default=None)
            or remove_end(self._og_search_title(webpage, default=''), ' - Feet9')
            or remove_end(self._html_extract_title(webpage, default=''), ' - Feet9')
            or None)

        if not display_id:
            display_id = self._search_regex(
                rf'/{video_id}/([^/?#]+)',
                self._og_search_url(webpage) or '', 'display id', default=None)

        category = self._html_search_regex(
            r'<div[^>]+id="video-category"[^>]*>\s*<a[^>]*>([^<]+)',
            webpage, 'category', default=None)
        uploader_id, uploader = self._search_regex(
            r'Added [^<]* by <a href="/channel/(?P<id>[^/]+)/">(?P<name>[^<]+)</a>',
            webpage, 'uploader', default=(None, None), group=('id', 'name'))

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'ext': determine_ext(video_url, 'mp4'),
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'categories': [category] if category else None,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': urljoin('https://www.feet9.com/', f'channel/{uploader_id}/') if uploader_id else None,
            'like_count': int_or_none(self._search_regex(
                r'id="nbup">(\d+)', webpage, 'like count', default=None)),
            'dislike_count': int_or_none(self._search_regex(
                r'id="nbdown">(\d+)', webpage, 'dislike count', default=None)),
            'comment_count': int_or_none(self._search_regex(
                r'id="total_comments">\((\d+)\)', webpage, 'comment count', default=None)),
            'age_limit': 18,
            'http_headers': {'Referer': 'https://www.feet9.com/'},
        }, json_ld)
