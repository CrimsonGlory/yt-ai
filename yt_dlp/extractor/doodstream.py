import random
import string
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import ExtractorError


class DoodStreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:dood(?:stream)?\.(?:com|to|watch|so|pm|wf|re|la|li|ws)|playmogo\.com)/[ed]/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        'url': 'https://dood.to/e/zn9kojocfiey',
        'md5': '18e078b4ab135be470aeb688e87c830c',
        'info_dict': {
            'id': 'zn9kojocfiey',
            'ext': 'mp4',
            'title': 'da-nai-tu-ya-mei-mei-zhua-nai-rou-mao-bi 1080p - DoodStream',
            'thumbnail': 'https://dodoimg.com/splash/ygbnt7ux6xdcy799.jpg',
        },
    }, {
        'url': 'http://dood.to/e/5s1wmbdacezb',
        'skip': 'Video gone',
        'md5': '4568b83b31e13242b3f1ff96c55f0595',
        'info_dict': {
            'id': '5s1wmbdacezb',
            'ext': 'mp4',
            'title': 'Kat Wonders - Monthly May 2020',
            'description': 'Kat Wonders - Monthly May 2020 | DoodStream.com',
            'thumbnail': 'https://img.doodcdn.com/snaps/flyus84qgl2fsk4g.jpg',
        },
    }, {
        'url': 'http://dood.watch/d/5s1wmbdacezb',
        'skip': 'Video gone',
        'md5': '4568b83b31e13242b3f1ff96c55f0595',
        'info_dict': {
            'id': '5s1wmbdacezb',
            'ext': 'mp4',
            'title': 'Kat Wonders - Monthly May 2020',
            'description': 'Kat Wonders - Monthly May 2020 | DoodStream.com',
            'thumbnail': 'https://img.doodcdn.com/snaps/flyus84qgl2fsk4g.jpg',
        },
    }, {
        'url': 'https://dood.to/d/jzrxn12t2s7n',
        'skip': 'Video gone',
        'md5': '3207e199426eca7c2aa23c2872e6728a',
        'info_dict': {
            'id': 'jzrxn12t2s7n',
            'ext': 'mp4',
            'title': 'Stacy Cruz Cute ALLWAYSWELL',
            'description': 'Stacy Cruz Cute ALLWAYSWELL | DoodStream.com',
            'thumbnail': 'https://img.doodcdn.com/snaps/8edqd5nppkac3x8u.jpg',
        },
    }, {
        'url': 'https://dood.so/d/jzrxn12t2s7n',
        'only_matching': True,
    }, {
        'url': 'https://dood.pm/e/5s1wmbdacezb',
        'only_matching': True,
    }, {
        'url': 'https://dood.wf/e/5s1wmbdacezb',
        'only_matching': True,
    }, {
        'url': 'https://dood.re/e/5s1wmbdacezb',
        'only_matching': True,
    }, {
        'url': 'https://doodstream.com/e/5s1wmbdacezb',
        'only_matching': True,
    }, {
        'url': 'https://playmogo.com/e/5s1wmbdacezb',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        host = urllib.parse.urlparse(url).hostname or 'dood.to'
        url = f'https://{host}/e/{video_id}'
        webpage, urlh = self._download_webpage_handle(url, video_id, impersonate=True)
        url = urlh.url

        if 'video not found' in webpage.lower() and 'pass_md5' not in webpage:
            raise ExtractorError('Video not found', expected=True)

        title = self._html_search_meta(
            ('og:title', 'twitter:title'), webpage, default=None) or self._html_extract_title(webpage)
        thumb = self._html_search_meta(['og:image', 'twitter:image'], webpage, default=None)
        token = self._html_search_regex(r'[?&]token=([a-z0-9]+)[&\']', webpage, 'token')
        description = self._html_search_meta(
            ['og:description', 'description', 'twitter:description'], webpage, default=None)

        headers = {'Referer': url}
        pass_md5 = self._html_search_regex(r'(/pass_md5.*?)\'', webpage, 'pass_md5')
        media_prefix = self._download_webpage(
            urllib.parse.urljoin(url, pass_md5), video_id,
            'Downloading video URL', headers=headers, impersonate=True).strip()
        if not media_prefix.startswith('http'):
            media_prefix = urllib.parse.urljoin(url, media_prefix)
        final_url = ''.join((
            media_prefix,
            *(random.choice(string.ascii_letters + string.digits) for _ in range(10)),
            f'?token={token}&expiry={int(time.time() * 1000)}',
        ))

        return {
            'id': video_id,
            'title': title,
            'url': final_url,
            'http_headers': headers,
            'impersonate': True,
            'ext': 'mp4',
            'description': description,
            'thumbnail': thumb,
        }
