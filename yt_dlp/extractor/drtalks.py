from .bunnycdn import BunnyCdnIE
from .common import InfoExtractor
from ..utils import int_or_none, parse_iso8601, smuggle_url, url_or_none
from ..utils.traversal import require, traverse_obj


class DrTalksIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?drtalks\.com/videos/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://drtalks.com/videos/six-pillars-of-resilience-tools-for-managing-stress-and-flourishing/',
        'md5': 'c5e5ab8c5498b23b5ee2b53cabd157ef',
        'info_dict': {
            'id': '79f2a50a-929c-43a2-8643-492384baebd5',
            'ext': 'mp4',
            'title': 'Six Pillars of Resilience: Tools for Managing Stress and Flourishing',
            'description': 'md5:23cb40c0518dde7a733ad28d4d1d6fdf',
            'thumbnail': 'https://account.drtalks.com/wp-content/uploads/2025/12/Episode-82-Eva-Selhub-DrTalks-Thumbs.jpg',
            'duration': 2800,
            'timestamp': 1735639220,
            'upload_date': '20241231',
            'uploader': 'Jen Pfleghaar, DO, ABOIM',
            'view_count': int,
            'tags': ['Burnout', 'Mental Health', 'Mindfulness', 'Resilience', 'Stress', 'Stress Reduction', 'Wellness'],
        },
    }, {
        'url': 'https://drtalks.com/videos/the-pcos-puzzle-mastering-metabolic-health-with-marcelle-pick/',
        'md5': '3852bc321227ae9bc20d88419d6b1bd9',
        'info_dict': {
            'id': '0c1c6e5a-f25c-4db5-b17d-757d9923a537',
            'ext': 'mp4',
            'title': 'The PCOS Puzzle: Mastering Metabolic Health with Marcelle Pick',
            'description': 'md5:6d1459277d3ca3ce13bc9f11485f1275',
            'thumbnail': 'https://account.drtalks.com/wp-content/uploads/2025/12/Episode-34-Marcelle-Pick-OBGYN-NP-DrTalks.jpg',
            'duration': 3515,
            'timestamp': 1732442420,
            'upload_date': '20241124',
            'uploader': 'Cassie Smith, MD',
            'view_count': int,
            'tags': ['Blood Sugar', 'Gut Health', 'Gut Microbiome', 'Hormone Health', 'Inflammatory Response', 'Insulin Resistance', 'Metabolic Health', 'PCOS'],
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        post_data = traverse_obj(self._search_nextjs_v13_data(webpage, video_id), (
            ..., 'postData', {dict}, {lambda v: v if v.get('slug') == video_id else None}, any,
            {require('video data')}))
        embed_url = traverse_obj(post_data, (
            (('iframe', 'url'), 'videoUrl'), {url_or_none}, any, {require('bunny embed URL')}))

        return self.url_result(
            smuggle_url(embed_url, {'Referer': url}), ie=BunnyCdnIE, url_transparent=True,
            **traverse_obj(post_data, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('thumbnail', 'sourceUrl', {url_or_none}),
                'timestamp': ('dateGmt', {parse_iso8601}),
                'duration': ('bunnynetMeta', 'length', {int_or_none}),
                'view_count': ('viewsCount', {int_or_none}),
                'uploader': ('expert', {str}),
                'tags': ('topics', 'nodes', ..., 'name', {str}),
            }))
