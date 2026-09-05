import urllib.parse

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    determine_ext,
    int_or_none,
    mimetype2ext,
)


class TweakersIE(InfoExtractor):
    _VALID_URL = r'https?://tweakers\.net/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://tweakers.net/video/20536/alles-wat-we-zagen-in-de-nieuwe-gta-vi-trailer-tweakers.html',
        'skip': 'extractor broken: [youtube] qirME9LGzag: Signature solving failed: Some formats may be missing. En',
        'md5': 'c37fa28c1cbaa6695e9f3e6974889ccf',
        'info_dict': {
            'id': 'qirME9LGzag',
            'ext': 'mp4',
            'title': 'Alles wat we zagen in de nieuwe GTA VI-trailer - Tweakers Update',
            'description': 'md5:4e869b4aecb3b47f69f44beb9fad77d6',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'duration': 377,
            'uploader': 'tweakers',
            'uploader_id': '@tweakers',
            'uploader_url': 'https://www.youtube.com/@tweakers',
            'channel': 'tweakers',
            'channel_id': 'UCRztjeLfNzi2nw2nffMQtGA',
            'channel_url': 'https://www.youtube.com/channel/UCRztjeLfNzi2nw2nffMQtGA',
            'channel_follower_count': int,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'timestamp': 1787901012,
            'upload_date': '20260828',
            'categories': ['Science & Technology'],
            'tags': list,
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
        },
        'params': {
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
        ],
    }, {
        'url': 'https://tweakers.net/video/9926/new-nintendo-3ds-xl-op-alle-fronten-beter.html',
        'skip': 'video gone',
        'md5': 'fe73e417c093a788e0160c4025f88b15',
        'info_dict': {
            'id': '9926',
            'ext': 'mp4',
            'title': 'New Nintendo 3DS XL - Op alle fronten beter',
            'description': 'md5:3789b21fed9c0219e9bcaacd43fab280',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'duration': 386,
            'uploader_id': 's7JeEm',
        },
    }]

    def _download_video_webpage(self, url, video_id):
        webpage = self._download_webpage(url, video_id, impersonate=True)
        if 'youtubeId' in webpage:
            return webpage
        callback = self._search_regex(
            r'callbackUrl\s*=\s*new URL\(decodeURIComponent\((["\'])(?P<url>(?:(?!\1).)+)\1\)',
            webpage, 'privacy gate callback', group='url', default=None)
        if not callback:
            return webpage
        return self._download_webpage(
            urllib.parse.unquote(callback), video_id,
            note='Confirming privacy gate', impersonate=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_video_webpage(url, video_id)

        youtube_id = self._search_regex(
            r'"youtubeId"\s*:\s*"([0-9A-Za-z_-]{11})"',
            webpage, 'youtube id', default=None)
        if youtube_id:
            return self.url_result(
                f'https://www.youtube.com/watch?v={youtube_id}', YoutubeIE, youtube_id)

        video_data = self._download_json(
            f'https://tweakers.net/video/s1playlist/{video_id}/1920/1080/playlist.json',
            video_id, impersonate=True)['items'][0]

        title = video_data['title']

        formats = []
        for location in video_data.get('locations', {}).get('progressive', []):
            format_id = location.get('label')
            width = int_or_none(location.get('width'))
            height = int_or_none(location.get('height'))
            for source in location.get('sources', []):
                source_url = source.get('src')
                if not source_url:
                    continue
                ext = mimetype2ext(source.get('type')) or determine_ext(source_url)
                formats.append({
                    'format_id': format_id,
                    'url': source_url,
                    'width': width,
                    'height': height,
                    'ext': ext,
                })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('poster'),
            'duration': int_or_none(video_data.get('duration')),
            'uploader_id': video_data.get('account'),
            'formats': formats,
        }
