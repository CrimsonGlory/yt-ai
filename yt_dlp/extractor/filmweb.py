import json

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    traverse_obj,
)


class FilmwebIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?filmweb\.no/(?:(?:trailere|filmnytt)/article|(?:film|filmnytt)/)(?P<id>[^/?#.]+)(?:\.ece)?'
    _TESTS = [{
        'url': 'https://www.filmweb.no/filmnytt/forste-trailer-markens-grode',
        'md5': '16bd233dd346c486cff93598a349f0d8',
        'info_dict': {
            'id': '130565033',
            'ext': 'mp4',
            'title': 'Markens grøde',
            'timestamp': 1786964554,
            'upload_date': '20260817',
            'uploader_id': '12639962',
            'uploader': 'Ted Sanne',
            'duration': 126,
            'thumbnail': r're:https?://.*',
            'view_count': int,
            'comment_count': int,
        },
        'add_ie': ['TwentyThreeVideo'],
    }, {
        'url': 'http://www.filmweb.no/trailere/article1264921.ece',
        'skip': 'Old article URLs are gone after the site redesign',
        'md5': 'e353f47df98e557d67edaceda9dece89',
        'info_dict': {
            'id': '13033574',
            'ext': 'mp4',
            'title': 'Det som en gang var',
            'upload_date': '20160316',
            'timestamp': 1458140101,
            'uploader_id': '12639966',
            'uploader': 'Live Roaldset',
        },
    }, {
        'url': 'https://www.filmweb.no/film/UIP20241680',
        'only_matching': True,
    }, {
        'url': 'https://www.filmweb.no/filmnytt/dune-part-three-forste-trailer',
        'only_matching': True,
    }]
    _CLIP_QUERY = '''query ($clipId: Int) {
        movieQuery {
            getMovieClip(clipId: $clipId, autoplay: false) {
                clipTitle
                id
                embedCode
            }
        }
    }'''

    def _extract_twentythree(self, clip_id, display_id):
        clip = traverse_obj(self._download_json(
            'https://movieinfoqs.filmweb.no/graphql', display_id,
            data=json.dumps({
                'query': self._CLIP_QUERY,
                'variables': {'clipId': int(clip_id)},
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://www.filmweb.no',
            }), ('data', 'movieQuery', 'getMovieClip', {dict}))
        embed_code = traverse_obj(clip, ('embedCode', {str}))
        if not embed_code:
            raise ExtractorError('Unable to extract trailer embed', expected=True)

        iframe_url = self._proto_relative_url(self._search_regex(
            r'<iframe[^>]+src="([^"]+)', embed_code, 'iframe url'))
        return self.url_result(
            iframe_url, 'TwentyThreeVideo', str(clip.get('id') or clip_id),
            clip.get('clipTitle'), url_transparent=True)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        if '/article' in url:
            if '/filmnytt/' in url:
                webpage = self._download_webpage(url, display_id)
                display_id = self._search_regex(r'data-videoid="(\d+)"', webpage, 'article id')
            embed_code = self._download_json(
                'https://www.filmweb.no/template_v2/ajax/json_trailerEmbed.jsp',
                display_id, query={
                    'articleId': display_id,
                })['embedCode']
            iframe_url = self._proto_relative_url(self._search_regex(
                r'<iframe[^>]+src="([^"]+)', embed_code, 'iframe url'))
            return self.url_result(
                iframe_url, 'TwentyThreeVideo', display_id, url_transparent=True)

        webpage = self._download_webpage(url, display_id)
        clip_id = self._search_regex(
            (r'\\"videoId\\":\\"(\d+)\\"',
             r'"videoId"\s*:\s*"(\d+)"',
             r'twentythreeEmbed[^}]+videoId\\?":(\d+)'),
            webpage, 'clip id', default=None)
        if clip_id:
            return self._extract_twentythree(clip_id, display_id)

        youtube_id = self._search_regex(
            r'youtubeId\\?":\\?"([0-9A-Za-z_-]{11})', webpage, 'youtube id', default=None)
        if youtube_id:
            return self.url_result(youtube_id, YoutubeIE, youtube_id)

        raise ExtractorError('No video found on this page', expected=True)
