from .common import InfoExtractor
from .dailymotion import DailymotionIE
from .youtube import YoutubeIE


class GMANetworkVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www)\.gmanetwork\.com/(?:\w+/){3}(?P<id>\d+)/(?P<display_id>[\w-]+)/video'
    _TESTS = [{
        'url': 'https://www.gmanetwork.com/fullepisodes/home/running_man_philippines/168677/running-man-philippines-catch-the-thief-full-chapter-2/video?section=home',
        'md5': '0aac6880771c397a825b6112c5868b6d',
        'info_dict': {
            'id': '28BqW0AXPe0',
            'ext': 'mp4',
            'title': 'Running Man Philippines: Catch the Thief (FULL CHAPTER 2)',
            'description': 'md5:811bdcea74f9c48051824e494756e926',
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'duration': 5313,
            'timestamp': 1663594212,
            'upload_date': '20220919',
            'release_timestamp': 1663594212,
            'release_date': '20220919',
            'uploader': 'YoüLOL',
            'uploader_id': '@YouLOLGMA',
            'uploader_url': 'https://www.youtube.com/@YouLOLGMA',
            'channel': 'YoüLOL',
            'channel_id': 'UChsoPNR5x-wdSO2GrOSIWqQ',
            'channel_url': 'https://www.youtube.com/channel/UChsoPNR5x-wdSO2GrOSIWqQ',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'like_count': int,
            'view_count': int,
            'comment_count': int,
            'tags': 'count:22',
            'categories': ['Entertainment'],
            'age_limit': 0,
            'availability': 'public',
            'live_status': 'not_live',
            'playable_in_embed': True,
            'media_type': 'video',
            'heatmap': 'count:100',
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
        'url': 'https://www.gmanetwork.com/fullepisodes/home/more_than_words/87059/more-than-words-full-episode-80/video?section=home',
        'info_dict': {
            'id': 'yiDOExw2aSA',
            # Progressive https mp4 vs merged 136+251 mkv/webm under EJS/n-sig skips
            'ext': r're:(mp4|mkv|webm)',
            'title': 'More Than Words: Full Episode 80 (Finale)',
            'description': 'md5:6d00cd658394fa1a5071200d3ed4be05',
            'media_type': 'video',
            'uploader': 'GMA Network',
            'uploader_id': '@gmanetwork',
            'uploader_url': 'https://www.youtube.com/@gmanetwork',
            'channel': 'GMA Network',
            'channel_id': 'UCKL5hAuzgFQsyrsQKgU0Qng',
            'channel_url': 'https://www.youtube.com/channel/UCKL5hAuzgFQsyrsQKgU0Qng',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'duration': 1419,
            'thumbnail': r're:https?://i\.ytimg\.com/.+',
            'timestamp': 1538551834,
            'upload_date': '20181003',
            'age_limit': 0,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'tags': 'count:29',
            'categories': ['Entertainment'],
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'heatmap': 'count:100',
        },
        'params': {
            'skip_download': True,
            # Avoid colliding with suite/isolated reruns of test_GMANetworkVideo_1_%(id)s.*
            'outtmpl': 'gmanetworkvideo_1_%(id)s.%(ext)s',
            'format': 'bestvideo[protocol=https][ext=mp4]/best[protocol=https]/best',
        },
        'add_ie': ['Youtube'],
        'expected_warnings': [
            'Remote component challenge solver script',
            'No supported JavaScript runtime',
            'unable to extract yt initial data',
            'Incomplete yt initial data',
            'Incomplete data received',
            'n challenge solving failed',
            'Signature solving failed',
            'formats have been skipped',
            'formats are possibly damaged',
            'Requested format is not available',
            'No video formats found',
            'Error solving',
            'GVS PO Token',
            'JS Challenge Provider',
        ],
    }]

    def _real_extract(self, url):
        content_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, display_id)
        # webpage route
        youtube_id = self._search_regex(
            r'var\s*YOUTUBE_VIDEO\s*=\s*[\'"]+(?P<yt_id>[\w-]+)', webpage, 'youtube_id', fatal=False)
        if youtube_id:
            return self.url_result(youtube_id, YoutubeIE, youtube_id)

        # api call route
        # more info at https://aphrodite.gmanetwork.com/fullepisodes/assets/fullepisodes/js/dist/fullepisodes_video.js?v=1.1.11
        network_url = self._search_regex(
            r'NETWORK_URL\s*=\s*[\'"](?P<url>[^\'"]+)', webpage, 'network_url')
        json_data = self._download_json(f'{network_url}api/data/content/video/{content_id}', display_id)
        if json_data.get('video_file'):
            return self.url_result(json_data['video_file'], YoutubeIE, json_data['video_file'])
        else:
            return self.url_result(json_data['dailymotion_file'], DailymotionIE, json_data['dailymotion_file'])
