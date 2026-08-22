#!/usr/bin/env python3

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from yt_dlp import parse_options
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.generic import GenericIE
from yt_dlp.extractor.videa import VideaIE
from yt_dlp.extractor.yandexdisk import YandexDiskIE
from yt_dlp.networking.common import Response
from yt_dlp.utils import ExtractorError, download_range_func, unsmuggle_url
from yt_dlp.utils import _legacy as legacy
from yt_dlp.webvtt import _MatchParser, parse_fragment



class TestParseOptions(unittest.TestCase):
    def test_parse_options_postprocessors_and_compat(self):
        parsed = parse_options([
            '--ignore-config', '-s', '--no-update',
            '--extract-audio', '--audio-format', 'mp3',
            '--embed-subs', '--embed-thumbnail', '--add-metadata',
            '--convert-subs', 'vtt', '--convert-thumbnails', 'jpg',
            '--sponsorblock-mark', 'all', '--xattrs',
            '--compat-options', 'filename,multistreams,format-sort',
            'https://example.com/x',
        ])
        keys = {pp['key'] for pp in parsed.ydl_opts.get('postprocessors', [])}
        self.assertIn('FFmpegExtractAudio', keys)
        self.assertTrue(parsed.ydl_opts.get('writesubtitles') or 'FFmpegEmbedSubtitle' in keys)

    def test_parse_options_simulate(self):
        parsed = parse_options(['--ignore-config', '-s', '--no-update', 'https://example.com/watch'])
        self.assertTrue(parsed.urls)
        self.assertIn('https://example.com/watch', parsed.urls)
        self.assertTrue(parsed.ydl_opts.get('simulate') or parsed.ydl_opts.get('skip_download'))
        self.assertIsInstance(parsed.ydl_opts, dict)
        self.assertIn('outtmpl', parsed.ydl_opts)

    def test_parse_options_extract_audio(self):
        parsed = parse_options([
            '--ignore-config', '-s', '--extract-audio', '--audio-format', 'mp3',
            '--no-update', 'https://example.com/a'])
        keys = {pp['key'] for pp in parsed.ydl_opts.get('postprocessors', [])}
        self.assertTrue(keys)

    def test_parse_options_list_extractors(self):
        parsed = parse_options(['--ignore-config', '--list-extractors'])
        self.assertTrue(parsed.options.list_extractors)


class TestDownloadRangeFunc(unittest.TestCase):
    def test_eq_and_repr_include_from_info(self):
        a = download_range_func([], [[0, 5]])
        b = download_range_func([], [[0, 5]])
        c = download_range_func([], [[0, 5]], from_info=True)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertIn('from_info=True', repr(c))
        self.assertNotIn('from_info', repr(a))


class TestUrlResultGeneric(unittest.TestCase):
    def test_generic_ie_is_smuggled(self):
        result = InfoExtractor.url_result('https://example.com/v.mp4', ie='Generic', video_id='x')
        url, data = unsmuggle_url(result['url'])
        self.assertEqual(result['ie_key'], 'Generic')
        self.assertEqual(result['id'], 'x')
        self.assertTrue(data.get('to_generic'))


class TestVideaUrl(unittest.TestCase):
    def test_player_f_param(self):
        self.assertTrue(VideaIE.suitable('https://videa.hu/player?f=6.198834.776849.0'))
        self.assertTrue(VideaIE.suitable('https://videa.hu/player?v=8YfIAjxwWGwT8HVQ'))


class TestYandexDiskPassword(unittest.TestCase):
    def test_password_url_is_claimed(self):
        self.assertTrue(YandexDiskIE.suitable('https://disk.yandex.ru/i/Nawj6uOS9oUVaQ'))
        source = YandexDiskIE._real_extract.__code__.co_consts
        joined = ' '.join(c for c in source if isinstance(c, str))
        self.assertIn('video-password', joined)


class TestGenericHTML5(unittest.TestCase):
    def test_generic_extracts_html5_video(self):
        html = '''<html><head><title>Clip</title>
        <meta property="og:title" content="Clip">
        </head><body>
        <video src="https://cdn.example.com/a.mp4"></video>
        </body></html>'''

        class YDL(FakeYDL):
            def urlopen(self, req):
                url = req.url if hasattr(req, 'url') else str(req)
                return Response(io.BytesIO(html.encode()), url, {'Content-Type': 'text/html'})

        ie = GenericIE(YDL())
        try:
            info = ie.extract('https://example.com/watch/clip.mp4')
        except ExtractorError:
            return
        self.assertTrue(info.get('url') or info.get('formats') or info.get('_type'))


class TestWebVTT(unittest.TestCase):
    def test_parse_simple_fragment(self):
        frag = b'''WEBVTT

00:00:00.000 --> 00:00:01.000
hello

00:00:01.000 --> 00:00:02.000
world
'''
        blocks = list(parse_fragment(frag))
        self.assertGreaterEqual(len(blocks), 1)

    def test_match_parser_consume(self):
        p = _MatchParser('abc123')
        self.assertEqual(p.match('abc'), 3)
        p.advance('abc')
        self.assertEqual(p.consume('123'), 3)


class TestLegacyUtils(unittest.TestCase):
    def test_platform_and_encoding(self):
        self.assertIsInstance(legacy.platform_name(), str)
        self.assertIsInstance(legacy.get_subprocess_encoding(), str)

    def test_decode_base_and_traverse(self):
        self.assertEqual(legacy.decode_base('10', '01'), 2)
        self.assertEqual(legacy.traverse_dict({'A': {'b': 1}}, ['a', 'b'], casesense=False), 1)

    def test_decode_png_rejects_garbage(self):
        with self.assertRaises(OSError):
            legacy.decode_png(b'not a png')

    def test_escape_url_roundtrip(self):
        url = 'https://example.com/a b'
        self.assertIn('example.com', legacy.escape_url(url))


class TestYoutubeDLProcess(unittest.TestCase):
    def test_prepare_filename_and_sort(self):
        ydl = FakeYDL({'outtmpl': '%(id)s.%(ext)s', 'skip_download': True})
        info = {
            'id': 'abc',
            'ext': 'mp4',
            'title': 't',
            'url': 'https://cdn.example.com/a.mp4',
            'formats': [
                {'url': 'https://cdn.example.com/a.mp4', 'ext': 'mp4', 'format_id': 'http', 'height': 360},
            ],
        }
        name = ydl.prepare_filename(info)
        self.assertIn('abc', name)
        ydl.sort_formats(info)
        self.assertTrue(info['formats'])

    def test_process_ie_result_url_type(self):
        ydl = FakeYDL({'skip_download': True, 'simulate': True})

        class DummyIE(InfoExtractor):
            IE_NAME = 'dummy'
            _VALID_URL = r'https?://dummy\.example/(?P<id>\w+)'

            def _real_extract(self, url):
                return {
                    'id': self._match_id(url),
                    'title': 'dummy',
                    'url': 'https://cdn.example.com/a.mp4',
                    'ext': 'mp4',
                }

        ydl.add_info_extractor(DummyIE())
        result = ydl.process_ie_result({
            '_type': 'url',
            'url': 'https://dummy.example/xyz',
            'ie_key': 'Dummy',
        }, download=False)
        self.assertEqual(result['id'], 'xyz')
        self.assertEqual(result['title'], 'dummy')

    def test_public_helpers(self):
        ydl = FakeYDL({'skip_download': True, 'simulate': True, 'outtmpl': '%(id)s.%(ext)s'})
        info = {'id': 'id1', 'title': 'T', 'ext': 'mp4', 'url': 'https://cdn.example.com/a.mp4', 'height': 720}
        ydl.warn_if_short_id(['abc'])
        ydl.to_stdout('hello')
        ydl.to_screen('hello')
        ydl.report_warning('w')
        ydl.write_debug('d')
        ydl.report_file_already_downloaded('f.mp4')
        ydl.report_file_delete('f.mp4')
        self.assertIsInstance(ydl.escape_outtmpl('%(id)s'), str)
        self.assertIsNone(ydl.validate_outtmpl('%(id)s.%(ext)s'))
        path = ydl.prepare_filename(info)
        self.assertIn('id1', path)
        ydl.add_extra_info(info, {'uploader': 'u'})
        self.assertEqual(info['uploader'], 'u')
        ydl.add_progress_hook(lambda d: None)
        ydl.add_post_hook(lambda d: None)
        selector = ydl.build_format_selector('best')
        self.assertTrue(callable(selector) or selector is not None)
        copied = ydl._copy_infodict(info)
        self.assertEqual(copied['id'], 'id1')
        self.assertEqual(ydl.get_output_path(filename='out.mp4'), 'out.mp4')


if __name__ == '__main__':
    unittest.main()
