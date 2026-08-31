#!/usr/bin/env python3

# Allow direct execution
import hashlib
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from yt_dlp.extractor import gen_extractors
from yt_dlp.extractor.doodstream import DoodStreamIE
from yt_dlp.extractor.einthusan import EinthusanIE
from yt_dlp.extractor.filemoon import FilemoonIE
from yt_dlp.extractor.gofile import GofileIE
from yt_dlp.extractor.hentaistigma import HentaiStigmaIE
from yt_dlp.extractor.thisav import ThisAVIE
from yt_dlp.extractor.xanimu import XanimuIE
from yt_dlp.extractor.xfileshare import XFileShareIE, aa_decode
from yt_dlp.extractor.yourporn import YourPornIE
from yt_dlp.extractor.yourupload import YourUploadIE
from yt_dlp.extractor.streamsb import StreamsbIE, streamsb_to_ascii_hex
from yt_dlp.networking.common import Response
from yt_dlp.utils import ExtractorError


RESTORED_URLS = (
    ('http://dood.to/e/5s1wmbdacezb', 'DoodStream'),
    ('http://dood.watch/d/5s1wmbdacezb', 'DoodStream'),
    ('https://dood.so/d/jzrxn12t2s7n', 'DoodStream'),
    ('https://dood.pm/e/5s1wmbdacezb', 'DoodStream'),
    ('https://dood.wf/e/5s1wmbdacezb', 'DoodStream'),
    ('https://dood.re/e/5s1wmbdacezb', 'DoodStream'),
    ('https://viewsb.com/dxfvlu4qanjx', 'viewsb'),
    ('https://filemoon.sx/e/abcd1234efgh', 'filemoon'),
    ('http://hentai.animestigma.com/inyouchuu-etsu-bonus/', 'HentaiStigma'),
    ('http://www.thisav.com/video/47734/just-fit.html', 'ThisAV'),
    ('https://gounlimited.to/abcd1234efgh', 'XFileShare'),
    ('https://highstream.tv/abcd1234efgh', 'XFileShare'),
    ('https://uqload.com/dltx1wztngdz', 'XFileShare'),
    ('https://vedbam.xyz/abcd1234efgh', 'XFileShare'),
    ('https://vadbam.net/abcd1234efgh', 'XFileShare'),
    ('https://vidlo.us/abcd1234efgh', 'XFileShare'),
    ('https://wolfstream.tv/nthme29v9u2x', 'XFileShare'),
    ('http://xvideosharing.com/fq65f94nd2ve', 'XFileShare'),
    ('https://viidshar.com/abcd1234efgh', 'XFileShare'),
    ('https://sxyprn.com/post/57ffcb2e1179b.html', 'YourPorn'),
    ('https://jable.tv/videos/pppd-812/', 'Jable'),
    ('http://91porn.com/view_video.php?viewkey=7e42283b4f5ab36da134', '91porn'),
    ('https://einthusan.tv/movie/watch/9097/', 'Einthusan'),
    ('https://einthusan.com/movie/watch/9097/', 'Einthusan'),
    ('https://einthusan.ca/movie/watch/4E9n/?lang=hindi', 'Einthusan'),
    ('http://yourupload.com/watch/14i14h', 'YourUpload'),
    ('https://xanimu.com/huge-expansion/', 'Xanimu'),
    ('https://www.musicdex.org/track/306/dual-existence', 'MusicdexSong'),
    ('https://w.duboku.io/vodplay/1575-1-1.html', 'duboku'),
    ('https://gofile.io/d/AMZyDw', 'Gofile'),
)

PIRACY_ERROR_SNIPPET = 'primarily used for piracy'


class FixtureYDL(FakeYDL):
    def __init__(self, pages, override=None):
        super().__init__(override)
        self._pages = pages

    def urlopen(self, req):
        url = req.url if hasattr(req, 'url') else str(req)
        for needle, body in self._pages.items():
            if needle in url:
                data = body if isinstance(body, bytes) else body.encode()
                return Response(
                    io.BytesIO(data), url,
                    {'Content-Type': 'text/html; charset=utf-8'})
        raise AssertionError(f'unexpected request: {url}')


class TestRestoredSites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ies = gen_extractors()

    def _matching_ies(self, url):
        return [
            ie for ie in self.ies
            if ie.suitable(url) and ie.IE_NAME != 'generic'
        ]

    def test_restored_domains_are_claimed(self):
        for url, ie_name in RESTORED_URLS:
            matching = self._matching_ies(url)
            self.assertTrue(matching, f'{url} was not claimed by a site extractor')
            names = [ie.IE_NAME for ie in matching]
            self.assertIn(ie_name, names, f'{url} matched {names}, expected {ie_name}')
            self.assertNotIn('piracy', names)
            for ie in matching:
                source = ie._real_extract.__func__.__code__.co_consts
                joined = ' '.join(c for c in source if isinstance(c, str))
                self.assertNotIn(PIRACY_ERROR_SNIPPET, joined, f'{ie.IE_NAME} still refuses {url}')

    def test_known_piracy_extractor_is_gone(self):
        names = {ie.IE_NAME for ie in self.ies}
        self.assertNotIn('piracy', names)
        self.assertNotIn('KnownPiracy', names)
        self.assertTrue(any(ie.IE_NAME == 'DRM' for ie in self.ies))
        self.assertTrue(any(ie.IE_NAME == 'Liability' for ie in self.ies))

    def test_yourupload_extract_from_fixture(self):
        html = '''
        <html><head>
        <meta property="og:title" content="BigBuckBunny_320x180.mp4">
        <meta property="og:video" content="http://cdn.example.com/video.mp4">
        <meta property="og:image" content="http://cdn.example.com/thumb.jpg">
        </head></html>
        '''
        ydl = FixtureYDL({'yourupload.com': html})
        info = YourUploadIE(ydl).extract('http://yourupload.com/watch/14i14h')
        self.assertEqual(info['id'], '14i14h')
        self.assertEqual(info['title'], 'BigBuckBunny_320x180.mp4')
        self.assertEqual(info['url'], 'http://cdn.example.com/video.mp4')
        self.assertNotIn(PIRACY_ERROR_SNIPPET, str(info))

    def test_filemoon_extract_from_fixture(self):
        html = '''
        <html><head><title>Sample Clip</title>
        <meta property="og:title" content="Sample Clip">
        </head><body>
        <script>jwplayer("player").setup({file: "https://cdn.example.com/play.mp4"});</script>
        </body></html>
        '''
        ydl = FixtureYDL({'filemoon.sx': html})
        info = FilemoonIE(ydl).extract('https://filemoon.sx/e/abcd1234efgh')
        self.assertEqual(info['id'], 'abcd1234efgh')
        self.assertEqual(info['title'], 'Sample Clip')
        self.assertEqual(info['formats'][0]['url'], 'https://cdn.example.com/play.mp4')

    def test_xfileshare_extract_from_fixture(self):
        html = '''
        <html><head><title>sample</title></head>
        <body>
        <h2 class="video-page-head">sample</h2>
        <script>sources: [{file: "https://cdn.example.com/clip.mp4"}];</script>
        </body></html>
        '''
        ydl = FixtureYDL({'uqload.com': html})
        info = XFileShareIE(ydl).extract('https://uqload.com/dltx1wztngdz')
        self.assertEqual(info['id'], 'dltx1wztngdz')
        self.assertEqual(info['title'], 'sample')
        self.assertEqual(info['formats'][0]['url'], 'https://cdn.example.com/clip.mp4')

    def test_thisav_html5_extract_from_fixture(self):
        html = '''
        <html><head><title>Nerdy 18yo - 視頻 - ThisAV.com-世界第一中文成人娛樂網站</title></head>
        <body>
        <video src="https://cdn.example.com/clip.mp4"></video>
        : <a href="http://www.thisav.com/user/1/cybersluts">cybersluts</a>
        </body></html>
        '''
        ydl = FixtureYDL({'thisav.com': html})
        info = ThisAVIE(ydl).extract(
            'http://www.thisav.com/video/242352/nerdy-18yo-big-ass-tattoos-and-glasses.html')
        self.assertEqual(info['id'], '242352')
        self.assertEqual(info['title'], 'Nerdy 18yo')
        self.assertEqual(info['uploader'], 'cybersluts')
        self.assertEqual(info['formats'][0]['url'], 'https://cdn.example.com/clip.mp4')

    def test_xanimu_extract_from_fixture(self):
        html = '''
        <html><head>
        <title>The Princess + The Frog Hentai</title>
        <meta name="thumbnailUrl" content="https://xanimu.com/thumb.jpg">
        <meta name="description" content="Enjoy The Princess + The Frog Hentai now">
        </head><body>
        <script>
        var videoHigh = "https://cdn.example.com/high.mp4";
        var videoLow = "https://cdn.example.com/low.mp4";
        "headline": "The Princess + The Frog Hentai"
        duration: "207"
        </script>
        </body></html>
        '''
        ydl = FixtureYDL({'xanimu.com': html})
        info = XanimuIE(ydl).extract(
            'https://xanimu.com/51944-the-princess-the-frog-hentai/')
        self.assertEqual(info['id'], '51944-the-princess-the-frog-hentai')
        self.assertEqual(info['age_limit'], 18)
        urls = {f['url'] for f in info['formats']}
        self.assertIn('https://cdn.example.com/high.mp4', urls)
        self.assertIn('https://cdn.example.com/low.mp4', urls)

    def test_hentaistigma_extract_from_fixture(self):
        page = '''
        <html><h2 class="posttitle"><a>Inyouchuu Etsu Bonus</a></h2>
        <iframe src="https://cdn.example.com/wrap.mp4"></iframe>
        </html>
        '''
        wrap = '<script>file : "https://cdn.example.com/bonus.mp4"</script>'
        ydl = FixtureYDL({
            'hentai.animestigma.com': page,
            'cdn.example.com/wrap.mp4': wrap,
        })
        info = HentaiStigmaIE(ydl).extract(
            'http://hentai.animestigma.com/inyouchuu-etsu-bonus/')
        self.assertEqual(info['id'], 'inyouchuu-etsu-bonus')
        self.assertEqual(info['title'], 'Inyouchuu Etsu Bonus')
        self.assertEqual(info['url'], 'https://cdn.example.com/bonus.mp4')
        self.assertEqual(info['age_limit'], 18)

    def test_doodstream_extract_from_fixture(self):
        page = '''
        <html><head>
        <meta property="og:title" content="Kat Wonders">
        <meta property="og:description" content="Kat Wonders | DoodStream.com">
        <meta property="og:image" content="https://img.doodcdn.com/snaps/x.jpg">
        </head><body>
        <script>player?token=abc123def&x='/pass_md5/xyz'</script>
        </body></html>
        '''
        ydl = FixtureYDL({
            'dood.to/e/': page,
            'dood.to/pass_md5/xyz': 'https://cdn.example.com/seg',
        })
        info = DoodStreamIE(ydl).extract('http://dood.to/e/5s1wmbdacezb')
        self.assertEqual(info['id'], '5s1wmbdacezb')
        self.assertEqual(info['title'], 'Kat Wonders')
        self.assertTrue(info['url'].startswith('https://cdn.example.com/seg'))
        self.assertIn('token=abc123def', info['url'])

    def test_yourporn_extract_from_fixture(self):
        vnfo = json.dumps({
            '57ffcb2e1179b': '/cdn/1/2/3/4/10/12/ab',
        })
        html = f'''
        <html>
        <meta property="og:description" content="sample clip">
        <meta property="og:image" content="https://cdn.example.com/t.jpg">
        <div data-vnfo='{vnfo}'></div>
        duration : <span>2:45</span>
        </html>
        '''
        ydl = FixtureYDL({'sxyprn.com': html})
        info = YourPornIE(ydl).extract('https://sxyprn.com/post/57ffcb2e1179b.html')
        self.assertEqual(info['id'], '57ffcb2e1179b')
        self.assertEqual(info['age_limit'], 18)
        self.assertIn('/cdn8/', info['url'])
        self.assertEqual(info['duration'], 165)

    def test_gofile_extract_from_fixture(self):
        account = json.dumps({'data': {'token': 'guest-token'}})
        listing = json.dumps({
            'status': 'ok',
            'data': {
                'children': {
                    'a': {
                        'id': 'file-1',
                        'name': 'clip.mp4',
                        'mimetype': 'video/mp4',
                        'link': 'https://cdn.example.com/clip.mp4',
                        'size': 123,
                        'createTime': 1638338704,
                    },
                    'b': {
                        'id': 'file-2',
                        'name': 'notes.txt',
                        'mimetype': 'text/plain',
                        'link': 'https://cdn.example.com/notes.txt',
                    },
                },
            },
        })
        ydl = FixtureYDL({
            'api.gofile.io/accounts': account,
            'api.gofile.io/contents/AMZyDw': listing,
        })
        info = GofileIE(ydl).extract('https://gofile.io/d/AMZyDw')
        self.assertEqual(info['id'], 'AMZyDw')
        entries = list(info['entries'])
        self.assertEqual(len(entries), 2)
        by_id = {entry['id']: entry for entry in entries}
        self.assertEqual(by_id['file-1']['url'], 'https://cdn.example.com/clip.mp4')
        self.assertEqual(by_id['file-1']['ext'], 'mp4')
        self.assertEqual(by_id['file-2']['url'], 'https://cdn.example.com/notes.txt')
        self.assertEqual(by_id['file-2']['ext'], 'txt')
        self.assertIn('accountToken=guest-token', by_id['file-1']['http_headers']['Cookie'])

    def test_gofile_nested_folder_and_images(self):
        account = json.dumps({'data': {'token': 'guest-token'}})
        listing = json.dumps({
            'status': 'ok',
            'data': {
                'name': 'album',
                'type': 'folder',
                'children': {
                    'img': {
                        'id': 'img-1',
                        'type': 'file',
                        'name': 'photo.jpg',
                        'mimetype': 'image/jpeg',
                        'link': 'https://cdn.example.com/photo.jpg',
                        'size': 10,
                    },
                    'sub': {
                        'id': 'sub-folder',
                        'type': 'folder',
                        'name': 'more',
                    },
                },
            },
            'metadata': {'hasNextPage': False},
        })
        nested = json.dumps({
            'status': 'ok',
            'data': {
                'name': 'more',
                'type': 'folder',
                'children': {
                    'doc': {
                        'id': 'doc-1',
                        'type': 'file',
                        'name': 'readme.txt',
                        'mimetype': 'text/plain',
                        'link': 'https://cdn.example.com/readme.txt',
                    },
                },
            },
        })
        ydl = FixtureYDL({
            'api.gofile.io/accounts': account,
            'api.gofile.io/contents/album1': listing,
            'api.gofile.io/contents/sub-folder': nested,
        })
        info = GofileIE(ydl).extract('https://gofile.io/d/album1')
        self.assertEqual(info['title'], 'album')
        entries = list(info['entries'])
        self.assertEqual({entry['id'] for entry in entries}, {'img-1', 'doc-1'})

    def test_gofile_website_token(self):
        ie = GofileIE(FakeYDL())
        with mock.patch('yt_dlp.extractor.gofile.time.time', return_value=124176 * 14400):
            token = ie._website_token('guest-token')
        raw = '{}::{}::guest-token::124176::{}'.format(
            GofileIE._CLIENT_UA, GofileIE._CLIENT_LANG, GofileIE._WT_SALT)
        self.assertEqual(token, hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(
            ie._extract_wt_salt(r"var x=['\x31\x32\x61\x66\x30\x35\x36\x64\x61\x63\x65\x61\x30\x62'];"),
            '12af056dacea0b')

    def test_gofile_password_required(self):
        account = json.dumps({'data': {'token': 'guest-token'}})
        listing = json.dumps({'status': 'error-passwordRequired'})
        ydl = FixtureYDL({
            'api.gofile.io/accounts': account,
            'api.gofile.io/contents/secret': listing,
        })
        with self.assertRaises(ExtractorError) as ctx:
            list(GofileIE(ydl).extract('https://gofile.io/d/secret')['entries'])
        self.assertIn('password', str(ctx.exception).lower())

    def test_aa_decode(self):
        # ﾟΘﾟ == 1, then (ﾟДﾟ)[ﾟεﾟ]+ delimiter; "1" as octal is chr(1)
        decoded = aa_decode('(ﾟΘﾟ)(ﾟДﾟ)[ﾟεﾟ]+')
        self.assertIsInstance(decoded, str)

    def test_einthusan_decrypt(self):
        payload = {'HLSLink': 'https://cdn.example.com/a.m3u8', 'MP4Link': 'https://cdn.example.com/a.mp4'}
        b64 = __import__('base64').b64encode(json.dumps(payload).encode()).decode()
        # _decrypt reconstructs b64 as data[:10] + data[-1] + data[12:-1]
        encrypted = b64[:10] + 'XY' + b64[11:] + b64[10]
        ie = EinthusanIE(FakeYDL())
        self.assertEqual(ie._decrypt(encrypted, '9097'), payload)

    def test_streamsb_sources_url_shape(self):
        ie = StreamsbIE(FakeYDL())
        url = ie._build_sources_url('viewsb.com', 'dxfvlu4qanjx', '50')
        self.assertTrue(url.startswith('https://viewsb.com/sources50/'))
        hexpart = url.rsplit('/', 1)[-1]
        self.assertTrue(all(c in '0123456789abcdef' for c in hexpart))
        self.assertIn(streamsb_to_ascii_hex('streamsb'), hexpart)

    def test_extract_path_is_not_piracy_refusal(self):
        ydl = FixtureYDL({'example': '<html></html>'})
        for ie_cls in (DoodStreamIE, FilemoonIE, StreamsbIE, XFileShareIE, YourUploadIE):
            ie = ie_cls(ydl)
            try:
                ie._real_extract('https://example.com/x')
            except ExtractorError as e:
                self.assertNotIn(PIRACY_ERROR_SNIPPET, str(e))
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
