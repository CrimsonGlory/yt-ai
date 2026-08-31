from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class HypedditIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hypeddit\.com/(?:track/)?(?P<id>[0-9a-z]{6})(?:[/?#]|$)'
    _TESTS = [{
        'url': 'https://hypeddit.com/ct3t1y',
        'md5': '9267a58a9d037a53cd137abab943bc01',
        'info_dict': {
            'id': 'ct3t1y',
            'ext': 'mp3',
            'title': 'Hardgroove Makes Me Horny',
            'track': 'Hardgroove Makes Me Horny',
            'uploader': 'TRANQUILITY',
            'artists': ['TRANQUILITY'],
            'genres': ['Techno'],
            'description': 'Grab your free download of Hardgroove Makes Me Horny by TRANQUILITY on Hypeddit',
            'thumbnail': 'https://hypeddit-gates-prod.s3.amazonaws.com/ct3t1y_coverartmanual',
            'duration': 90.0,
            'vcodec': 'none',
        },
    }, {
        'url': 'https://hypeddit.com/track/scdpms',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        hidden = self._hidden_inputs(webpage)
        gate = self._search_json(
            r'\bjsonGateData\s*=', webpage, 'gate data', video_id, fatal=False)

        preview_url = url_or_none(unescapeHTML(hidden.get('preview_url') or ''))
        if not preview_url:
            preview_url = url_or_none(unescapeHTML(self._html_search_regex(
                r'\baudiourl=(["\'])(?P<url>https?://.+?)\1',
                webpage, 'preview url', default='', group='url')))
        if not hidden.get('current_download_file_listner') and not preview_url:
            raise ExtractorError(
                'This page does not contain a public Hypeddit track preview', expected=True)

        title = (
            traverse_obj(gate, ('title', {str}))
            or self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._og_search_title(webpage))
        artist = (
            traverse_obj(gate, ('artist_name', {str}))
            or self._html_search_regex(r'<h2[^>]*>([^<]+)', webpage, 'artist', default=None))
        genre = hidden.get('genre') or traverse_obj(gate, ('genre', {str}))
        sample_rate = float_or_none(hidden.get('preview_sample_rate'))
        duration = float_or_none(
            hidden.get('preview_length'), scale=sample_rate) if sample_rate else None

        return {
            'id': video_id,
            'title': title,
            'track': title,
            'uploader': artist,
            'artists': [artist] if artist else None,
            'genres': [genre] if genre else None,
            'description': (
                self._og_search_description(webpage, default=None)
                or self._html_search_meta('description', webpage)),
            'thumbnail': (
                self._og_search_thumbnail(webpage, default=None)
                or f'https://hypeddit-gates-prod.s3.amazonaws.com/{video_id}_coverartmanual'),
            'duration': duration,
            # Full-length `_main` objects are private; the player uses this public preview.
            'url': f'https://hypeddit-gates-prod.s3.amazonaws.com/{video_id}_preview',
            'ext': 'mp3',
            'vcodec': 'none',
            'acodec': 'mp3',
        }
