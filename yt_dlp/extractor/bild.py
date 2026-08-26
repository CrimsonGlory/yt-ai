from .common import InfoExtractor
from ..utils import (
    int_or_none,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class BildIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?bild\.de/(?:[^/?#]+/)+(?P<display_id>[^/?#]+)-'
        r'(?P<id>[0-9a-f]{24}|\d+)(?:(?:,auto=true)?\.bild\.html)?')
    IE_DESC = 'Bild.de'
    _TESTS = [{
        'note': 'legacy URL, static MP4 only',
        'url': 'http://www.bild.de/video/clip/apple-ipad-air/das-koennen-die-neuen-ipads-38184146.bild.html',
        'md5': 'dd495cbd99f2413502a1713a1156ac8a',
        'info_dict': {
            'id': '38184146',
            'ext': 'mp4',
            'title': 'Das können die neuen iPads',
            'description': 'Mit dem iPad Air 2 und dem iPad Mini 3 hat Apple zwei neue Tablet-Modelle präsentiert. BILD-Reporter Sven Stein durfte die Geräte bereits testen.',
            'thumbnail': r're:https?://images\.bild\.de/',
            'duration': 196,
        },
    }, {
        'note': 'legacy URL, static MP4 and HLS',
        'url': 'https://www.bild.de/video/clip/news-ausland/deftiger-abgang-vom-10m-turm-bademeister-sorgt-fuer-skandal-85158620.bild.html',
        'md5': '63c4dce5dd2cf819839b43f9c15294b4',
        'params': {'format': 'http-mp4'},
        'info_dict': {
            'id': '85158620',
            'ext': 'mp4',
            'title': 'Der Sprungturm-Skandal',
            'description': 'Riesen Wirbel um dieses Freibad-Video aus Österreich. Ein Bademeister stößt mit einem Tritt in den Rücken einen jungen Mann vom Sprungturm.',
            'thumbnail': r're:https?://images\.bild\.de/',
            'duration': 69,
        },
    }, {
        'note': 'current URL scheme, HLS only',
        'url': 'https://www.bild.de/leben-wissen/digital/hollywood-war-gestern-ki-clips-sehen-erschreckend-echt-aus-6a2d92977e682fc37fbf8ae3',
        'info_dict': {
            'id': '6a2d92977e682fc37fbf8ae3',
            'ext': 'mp4',
            'title': 'Sehen Sie auch ständig solche Videos?',
            'description': 'Früher sahen solche Bilder nach Hollywood aus. Heute tauchen sie ganz selbstverständlich zwischen echten Clips auf.',
            'thumbnail': r're:https?://images\.bild\.de/',
            'duration': 102,
        },
        'params': {'skip_download': True},
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_context = self._search_json(
            r'<script[^>]+\bid="pageContext"[^>]*>', webpage, 'page context', video_id)

        video = traverse_obj(page_context, (
            'CLIENT_STORE_INITIAL_STATE', 'pageAggregation', 'content',
            'children', ..., 'children',
            lambda _, v: v['type'] == 'VIDEO_ELEMENT',
            'props', {dict}, any, {require('video data')}))

        formats = []
        for src_url in dict.fromkeys(traverse_obj(
                video, ('sourceConfig', 'progressive', ..., 'url', {url_or_none}))):
            formats.append({
                'url': src_url,
                'format_id': 'http-mp4',
                'ext': 'mp4',
            })
        if hls_url := traverse_obj(video, ('sourceConfig', 'hls', {url_or_none})):
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        return {
            'id': video_id,
            'formats': formats,
            **traverse_obj(video, {
                'title': (('teaserHeadline', 'title'), {lambda s: ' '.join(s.split())}, filter, any),
                'description': ('description', {str}),
                'thumbnail': ('teaserImageUrl', {url_or_none}),
                'duration': ('duration', {int_or_none}),
            }),
        }
