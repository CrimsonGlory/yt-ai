from .common import InfoExtractor
from ..utils import ExtractorError


class Sport5IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|vod|m|nba)?\.sport5\.co\.il/.*\b(?:Vi|docID)=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.sport5.co.il/articles.aspx?FolderID=4169&docID=558912',
        'md5': '30880db833ae6b4ba0dc7a98db1f8668',
        'info_dict': {
            'id': '558912',
            'ext': 'mp4',
            'title': 'ענקית: גפן פרימו זכתה בגרנד סלאם לוזאן',
            'description': 'צפו. ההמנון התנגן בשווייץ לאחר הזכייה: \'\'אין דבר יותר מרגש מזה\'\'',
            'thumbnail': r're:https?://.*\.jpg',
            'timestamp': 1787934491,
            'upload_date': '20260828',
        },
    }, {
        'url': 'http://vod.sport5.co.il/?Vc=147&Vi=176331&Page=1',
        'info_dict': {
            'id': 's5-Y59xx1-GUh2',
            'ext': 'mp4',
            'title': 'ולנסיה-קורדובה 0:3',
            'description': 'אלקאסר, גאייה ופגולי סידרו לקבוצה של נונו ניצחון על קורדובה ואת המקום הראשון בליגה',
            'duration': 228,
            'categories': list,
        },
        'skip': 'video gone',
    }, {
        'url': 'http://www.sport5.co.il/articles.aspx?FolderID=3075&docID=176372&lang=HE',
        'info_dict': {
            'id': 's5-SiXxx1-hKh2',
            'ext': 'mp4',
            'title': 'GOALS_CELTIC_270914.mp4',
            'description': '',
            'duration': 87,
            'categories': list,
        },
        'skip': 'video gone',
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)
        webpage = self._download_webpage(url, media_id)

        hls_url = self._search_regex(
            r'(https?://sport5api\.akamaized\.net/[^\'"&\s]+?\.m3u8)',
            webpage, 'hls url', default=None)
        if hls_url:
            json_ld = self._search_json_ld(webpage, media_id, default={})
            return {
                'id': media_id,
                'title': json_ld.get('title') or self._og_search_title(webpage),
                'description': self._og_search_description(webpage) or json_ld.get('description'),
                'thumbnail': self._og_search_thumbnail(webpage),
                'timestamp': json_ld.get('timestamp'),
                'formats': self._extract_m3u8_formats(hls_url, media_id, 'mp4', m3u8_id='hls'),
            }

        video_id = self._html_search_regex(r'clipId=([\w-]+)', webpage, 'video id')

        metadata = self._download_xml(
            f'http://sport5-metadata-rr-d.nsacdn.com/vod/vod/{video_id}/HDS/metadata.xml',
            video_id)

        error = metadata.find('./Error')
        if error is not None:
            raise ExtractorError(
                '{} returned error: {} - {}'.format(
                    self.IE_NAME,
                    error.find('./Name').text,
                    error.find('./Description').text),
                expected=True)

        title = metadata.find('./Title').text
        description = metadata.find('./Description').text
        duration = int(metadata.find('./Duration').text)

        posters_el = metadata.find('./PosterLinks')
        thumbnails = [{
            'url': thumbnail.text,
            'width': int(thumbnail.get('width')),
            'height': int(thumbnail.get('height')),
        } for thumbnail in posters_el.findall('./PosterIMG')] if posters_el is not None else []

        categories_el = metadata.find('./Categories')
        categories = [
            cat.get('name') for cat in categories_el.findall('./Category')
        ] if categories_el is not None else []

        formats = [{
            'url': fmt.text,
            'ext': 'mp4',
            'vbr': int(fmt.get('bitrate')),
            'width': int(fmt.get('width')),
            'height': int(fmt.get('height')),
        } for fmt in metadata.findall('./PlaybackLinks/FileURL')]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'duration': duration,
            'categories': categories,
            'formats': formats,
        }
