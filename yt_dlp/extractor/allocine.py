from .common import InfoExtractor
from .dailymotion import DailymotionIE
from ..utils import (
    int_or_none,
    qualities,
    remove_end,
    strip_or_none,
    try_get,
    unified_timestamp,
    url_basename,
    urljoin,
)


class AllocineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?allocine\.fr/(?:article|video|film)/(?:fichearticle_gen_carticle=|player_gen_cmedia=|fichefilm_gen_cfilm=|video-)(?P<id>[0-9]+)(?:\.html)?'

    _TESTS = [{
        'url': 'http://www.allocine.fr/article/fichearticle_gen_carticle=18635087.html',
        'info_dict': {
            'id': '19546517',
            'display_id': '18635087',
            'ext': 'mp4',
            'title': 'Astérix - Le Domaine des Dieux Teaser VF',
            'description': 'Astérix - Le Domaine des Dieux Teaser VF',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 39,
            'timestamp': 1404273600,
            'upload_date': '20140702',
            'view_count': int,
            'uploader': 'Allociné',
            'uploader_id': 'x5rjhv',
            'like_count': int,
            'age_limit': 0,
            'tags': list,
        },
        'add_ie': ['Dailymotion'],
    }, {
        'url': 'http://www.allocine.fr/video/player_gen_cmedia=19540403&cfilm=222257.html',
        'info_dict': {
            'id': '19540403',
            'display_id': '19540403',
            'ext': 'mp4',
            'title': 'Planes 2 Bande-annonce VF',
            'description': 'Planes 2 Bande-annonce VF',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 69,
            'timestamp': 1385659800,
            'upload_date': '20131128',
            'view_count': int,
            'uploader': 'Allociné',
            'uploader_id': 'x5rjhv',
            'like_count': int,
            'age_limit': 0,
            'tags': list,
        },
        'add_ie': ['Dailymotion'],
    }, {
        'url': 'http://www.allocine.fr/video/player_gen_cmedia=19544709&cfilm=181290.html',
        'info_dict': {
            'id': '19544709',
            'display_id': '19544709',
            'ext': 'mp4',
            'title': 'Dragons 2 - Bande annonce finale VF',
            'description': 'Dragons 2 - Bande annonce finale VF',
            'thumbnail': r're:https?://.*\.jpg',
            'duration': 144,
            'timestamp': 1397589900,
            'upload_date': '20140415',
            'view_count': int,
            'uploader': 'Allociné',
            'uploader_id': 'x5rjhv',
            'like_count': int,
            'age_limit': 0,
            'tags': list,
        },
        'add_ie': ['Dailymotion'],
    }, {
        'url': 'http://www.allocine.fr/video/video-19550147/',
        'info_dict': {
            'id': '19550147',
            'ext': 'mp4',
            'title': 'Les gaffes de Cliffhanger',
            'description': str,
            'thumbnail': r're:https?://.*\.jpg',
            'uploader': str,
            'uploader_id': str,
            'view_count': int,
            'like_count': int,
            'age_limit': int,
            'duration': int,
            'tags': list,
            'timestamp': int,
            'upload_date': r're:\d{8}',
        },
        'add_ie': ['Dailymotion'],
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        formats = []
        quality = qualities(['ld', 'md', 'hd'])

        model = self._html_search_regex(
            r'data-model="([^"]+)"', webpage, 'data model', default=None)
        if model:
            model_data = self._parse_json(model, display_id)
            video = model_data['videos'][0]
            title = video['title']
            sources = video.get('sources') or {}
            dm_id = video.get('idDailymotion')
            if dm_id and not sources:
                dm_ie = DailymotionIE()
                dm_ie.set_downloader(self._downloader)
                info = dm_ie.extract(f'https://www.dailymotion.com/video/{dm_id}')
                info['id'] = str(video.get('id') or display_id)
                info['display_id'] = display_id
                info['title'] = title
                info['description'] = (video.get('description')
                                       or self._og_search_description(webpage))
                thumb = video.get('image')
                if thumb:
                    info['thumbnail'] = urljoin('http://www.allocine.fr', thumb)
                info['duration'] = int_or_none(video.get('duration'))
                info['timestamp'] = unified_timestamp(try_get(
                    video, lambda x: x['added_at']['date'], str))
                info['view_count'] = int_or_none(video.get('view_count'))
                return info
            for video_url in sources.values():
                video_id, format_id = url_basename(video_url).split('_')[:2]
                formats.append({
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'url': video_url,
                })
            duration = int_or_none(video.get('duration'))
            view_count = int_or_none(video.get('view_count'))
            timestamp = unified_timestamp(try_get(
                video, lambda x: x['added_at']['date'], str))
        else:
            video_id = display_id
            media_data = self._download_json(
                f'http://www.allocine.fr/ws/AcVisiondataV5.ashx?media={video_id}', display_id)
            title = remove_end(strip_or_none(self._html_extract_title(webpage)), ' - AlloCiné')
            for key, value in media_data['video'].items():
                if not key.endswith('Path'):
                    continue
                format_id = key[:-len('Path')]
                formats.append({
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'url': value,
                })
            duration, view_count, timestamp = [None] * 3

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': duration,
            'timestamp': timestamp,
            'view_count': view_count,
            'formats': formats,
        }
