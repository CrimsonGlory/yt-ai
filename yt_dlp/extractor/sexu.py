from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    merge_dicts,
    parse_resolution,
    url_or_none,
    urlencode_postdata,
    urljoin,
)
from ..utils.traversal import traverse_obj


class SexuIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?sexu\.com/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://sexu.com/2395662/',
        'md5': 'f31c9ec4ce7bb666b3967f5d67c9e448',
        'info_dict': {
            'id': '2395662',
            'ext': 'mp4',
            'title': 'Ariella Ferrera - MILF Gets Naughty and Plays with Her Hairy Cock Slot',
            'description': 'Free 8 min milf video from All Over 30: Ariella Ferrera - MILF Gets Naughty and Plays with Her Hairy Cock. Watch masturbation, cock & solo porn in HD on Sexu.Com.',
            'thumbnail': r're:https?://.*\.webp',
            'duration': 470,
            'timestamp': 1413749351,
            'upload_date': '20141019',
            'uploader': 'All Over 30',
            'age_limit': 18,
            'categories': list,  # NSFW
            'tags': list,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        },
    }, {
        'url': 'http://sexu.com/961791/',
        'skip': 'video gone',
        'md5': 'ff615aca9691053c94f8f10d96cd7884',
        'info_dict': {
            'id': '961791',
            'ext': 'mp4',
            'title': 'md5:4d05a19a5fc049a63dbbaf05fb71d91b',
            'description': 'md5:2b75327061310a3afb3fbd7d09e2e403',
            'categories': list,  # NSFW
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_info = self._download_json(
            urljoin(url, '/api/video-info'), video_id,
            'Downloading video info',
            data=urlencode_postdata({'videoId': video_id}),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': url,
            }, fatal=False) or {}
        player_data = traverse_obj(video_info, ('playerData', {dict})) or {}

        formats = []
        hls_url = traverse_obj(player_data, ('src', {url_or_none}))
        src_type = player_data.get('type') or ''
        if hls_url and ('mpegurl' in src_type or 'media=hls' in hls_url):
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        for source in traverse_obj(player_data, ('sources', ..., {dict})):
            video_url = self._proto_relative_url(source.get('src'))
            if not video_url:
                continue
            quality = source.get('quality')
            formats.append({
                'url': video_url,
                'format_id': quality,
                'ext': 'mp4',
                # Prefer progressive MP4 over the equivalent HLS renditions
                'preference': 1,
                **parse_resolution(quality),
            })

        json_ld = self._search_json_ld(webpage, video_id, default={})
        if not formats and json_ld.get('url'):
            formats.append({'url': json_ld['url']})
        if not formats:
            raise ExtractorError('No video sources found', expected=True)

        categories_str = self._html_search_meta('keywords', webpage, default=None)
        categories = (
            [c.strip() for c in categories_str.split(',') if c.strip()]
            if categories_str else None)

        info = merge_dicts({
            'id': video_id,
            'formats': formats,
            'age_limit': 18,
            'like_count': int_or_none(video_info.get('likeCount')),
            'dislike_count': int_or_none(video_info.get('dislikeCount')),
            'categories': categories,
        }, json_ld, {
            'title': self._og_search_title(webpage, default=None) or self._html_extract_title(webpage),
        })
        info.pop('url', None)
        tags = [t.strip() for t in info.get('tags') or [] if isinstance(t, str) and t.strip()]
        if tags:
            info['tags'] = tags
            if not info.get('categories'):
                info['categories'] = tags
        return info
