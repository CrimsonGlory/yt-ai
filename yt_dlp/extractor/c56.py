from .common import InfoExtractor
from ..utils import ExtractorError, js_to_json


class C56IE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|player)\.)?56\.com/(?:.+?/)?(?:v_|(?:play_album.+-))(?P<textid>.+?)\.(?:html|swf)'
    IE_NAME = '56.com'
    _TESTS = [{
        'url': 'https://www.56.com/u76/v_MjAzMTkwNTY5.html',
        'md5': '6cc69af917e34c1ff7d62e102b85027e',
        'info_dict': {
            'id': '735567287',
            'ext': 'mp4',
            'title': '焦点访谈丨多项重大工程进度条刷新 将这样改变你我生活',
            'uploader': '央广网',
            'duration': 350,
            'timestamp': 1786058100,
            'upload_date': '20260806',
            'thumbnail': r're:https?://.+\.jpg',
            'tags': ['焦点访谈', '工程', '新闻报道'],
        },
        'add_ie': ['Sohu'],
    }, {
        'url': 'http://www.56.com/u39/v_OTM0NDA3MTY.html',
        'md5': 'e59995ac63d0457783ea05f93f12a866',
        'info_dict': {
            'id': '93440716',
            'ext': 'flv',
            'title': '网事知多少 第32期：车怒',
            'duration': 283.813,
        },
        'skip': 'video gone',
    }, {
        'url': 'http://www.56.com/u47/v_MTM5NjQ5ODc2.html',
        'md5': '',
        'info_dict': {
            'id': '82247482',
            'title': '爱的诅咒之杜鹃花开',
        },
        'playlist_count': 7,
        'add_ie': ['Sohu'],
        'skip': 'video gone',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        text_id = mobj.group('textid')

        webpage = self._download_webpage(url, text_id)
        sohu_video_info_str = self._search_regex(
            r'var\s+sohuVideoInfo\s*=\s*({[^}]+});', webpage, 'Sohu video info', default=None)
        if sohu_video_info_str:
            sohu_video_info = self._parse_json(
                sohu_video_info_str, text_id, transform_source=js_to_json)
            return self.url_result(sohu_video_info['url'], 'Sohu')

        page = self._download_json(
            f'http://vxml.56.com/json/{text_id}/', text_id, 'Downloading video info')

        info = page.get('info')
        if not info:
            raise ExtractorError(page.get('msg') or 'Unable to extract video info', expected=True)

        formats = [
            {
                'format_id': f['type'],
                'filesize': int(f['filesize']),
                'url': f['url'],
            } for f in info['rfiles']
        ]

        return {
            'id': info['vid'],
            'title': info['Subject'],
            'duration': int(info['duration']) / 1000.0,
            'formats': formats,
            'thumbnail': info.get('bimg') or info.get('img'),
        }
