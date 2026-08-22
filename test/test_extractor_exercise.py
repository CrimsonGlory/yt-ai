#!/usr/bin/env python3

"""Drive every registered extractor against fixture HTTP responses.

This is an offline structural test of the shipped extractors: URL matching,
initialize, extract, and error handling. It is not a live download test.
"""

import io
import json
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from yt_dlp.extractor import gen_extractors
from yt_dlp.extractor.generic import GenericIE
from yt_dlp.networking.common import Response
from yt_dlp.utils import ExtractorError

M3U8 = '\n'.join((
    '#EXTM3U',
    '#EXT-X-VERSION:3',
    '#EXT-X-TARGETDURATION:1',
    '#EXTINF:1.0,',
    'https://cdn.example.com/seg.ts',
    '#EXT-X-ENDLIST',
    '',
))

RICH_HTML = '''<!DOCTYPE html>
<html data-pageid="page-1">
<head>
<title>Sample Title</title>
<meta property="og:title" content="Sample Title">
<meta property="og:description" content="Sample description">
<meta property="og:image" content="https://cdn.example.com/thumb.jpg">
<meta property="og:video" content="https://cdn.example.com/video.mp4">
<meta property="og:video:url" content="https://cdn.example.com/video.mp4">
<meta name="description" content="Sample description">
<meta name="thumbnailUrl" content="https://cdn.example.com/thumb.jpg">
<script type="application/ld+json">
{"@type":"VideoObject","name":"Sample Title","contentUrl":"https://cdn.example.com/video.mp4","thumbnailUrl":"https://cdn.example.com/thumb.jpg","duration":"PT1M"}
</script>
</head>
<body>
<h1>Sample Title</h1>
<h2 class="posttitle"><a>Sample Title</a></h2>
<h2 class="video-page-head">Sample Title</h2>
<h3>Sample Title</h3>
<video src="https://cdn.example.com/video.mp4" poster="https://cdn.example.com/thumb.jpg">
<source src="https://cdn.example.com/video.mp4" type="video/mp4">
</video>
<iframe src="https://cdn.example.com/embed.mp4"></iframe>
<script>
var hlsUrl = 'https://cdn.example.com/playlist.m3u8';
var videoHigh = "https://cdn.example.com/high.mp4";
var videoLow = "https://cdn.example.com/low.mp4";
jwplayer("player").setup({file: "https://cdn.example.com/video.mp4", image: "https://cdn.example.com/thumb.jpg", title: "Sample Title"});
file: "https://cdn.example.com/video.mp4"
player_data = {"url": "https://cdn.example.com/playlist.m3u8", "encrypt": 0, "from": "local"};
token=abc123def&x='/pass_md5/xyz'
</script>
</body></html>
'''

RICH_JSON = json.dumps({
    'status': 'ok',
    'data': {
        'token': 'guest-token',
        'url': 'https://cdn.example.com/video.mp4',
        'title': 'Sample Title',
        'name': 'Sample Title',
        'file': 'https://cdn.example.com/playlist.m3u8',
        'link': 'https://cdn.example.com/video.mp4',
        'children': {},
        'tracks': [],
        'album': {'name': 'Album', 'artists': [], 'image': 'img.jpg', 'release_date': '2020-01-01'},
        'stream_data': {'title': 'Sample Title', 'file': 'https://cdn.example.com/playlist.m3u8'},
        'EJLinks': 'aaaaaaaaaabccccccccccccccccccccccccccccccccccc',
    },
    'track': {
        'id': 1, 'name': 'Track', 'url': 'x.mp3', 'duration': 1,
        'genres': [], 'artists': [], 'album': {'name': 'A', 'artists': [], 'image': 'i', 'release_date': '2020-01-01'},
    },
    'album': {'name': 'Album', 'tracks': [], 'artists': [], 'genres': [], 'plays': 1, 'image': 'i', 'release_date': '2020-01-01'},
    'artist': {'name': 'Artist', 'plays': 1, 'image_small': 'i'},
    'playlist': {'name': 'Playlist', 'plays': 1, 'description': 'd', 'image': 'i'},
    'pagination': {'data': [], 'next_page_url': None},
    'title': 'Sample Title',
    'url': 'https://cdn.example.com/video.mp4',
    'stream_data': {'title': 'Sample Title', 'file': 'https://cdn.example.com/playlist.m3u8'},
})


class ExerciseYDL(FakeYDL):
    def __init__(self):
        super().__init__({
            'cachedir': False,
            'skip_download': True,
            'ignoreerrors': True,
            'extract_flat': False,
            'socket_timeout': 1,
        })

    def urlopen(self, req):
        url = req.url if hasattr(req, 'url') else str(req)
        if url.endswith('.ts') or 'seg.ts' in url:
            return Response(io.BytesIO(b'\x00' * 32), url, {'Content-Type': 'video/MP2T'})
        if '.m3u8' in url:
            body, ctype = M3U8.encode(), 'application/vnd.apple.mpegurl'
        elif any(token in url for token in ('/api', '/secure/', '/ajax', '/accounts', '/contents', '/sources')):
            body, ctype = RICH_JSON.encode(), 'application/json'
        else:
            body, ctype = RICH_HTML.encode(), 'text/html; charset=utf-8'
        return Response(io.BytesIO(body), url, {'Content-Type': ctype})


class TestExtractorExercise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ies = [ie for ie in gen_extractors() if not isinstance(ie, GenericIE)]

    def test_every_extractor_has_valid_url_or_is_generic_fallback(self):
        named = []
        for ie in self.ies:
            valid = getattr(ie, '_VALID_URL', None)
            urls = getattr(ie, 'URLS', None)
            if valid or urls:
                named.append(type(ie).__name__)
        self.assertGreater(len(named), 1500)

    def test_extract_path_on_fixture_pages(self):
        import signal

        class _Timeout(Exception):
            pass

        def _on_alarm(signum, frame):
            raise _Timeout()

        orig_sleep = time.sleep
        time.sleep = lambda *_a, **_k: None
        piracy_hits = []
        ran = 0
        prev = signal.signal(signal.SIGALRM, _on_alarm)
        try:
            for ie in self.ies:
                tests = list(ie.get_testcases(include_onlymatching=True))
                url = tests[0]['url'] if tests else None
                if not url:
                    continue
                ydl = ExerciseYDL()
                ie.set_downloader(ydl)
                ran += 1
                signal.setitimer(signal.ITIMER_REAL, 0.08)
                try:
                    ie.extract(url)
                except ExtractorError as e:
                    if 'primarily used for piracy' in str(e):
                        piracy_hits.append((ie.IE_NAME, url))
                except Exception:
                    pass
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
        finally:
            signal.signal(signal.SIGALRM, prev)
            time.sleep = orig_sleep
        self.assertGreater(ran, 1000)
        self.assertEqual(piracy_hits, [])

    def test_suitable_and_metadata_helpers(self):
        for ie in self.ies[:50]:
            self.assertIsInstance(ie.suitable('https://example.com/'), bool)
            self.assertTrue(ie.ie_key())
            self.assertTrue(ie.IE_NAME)
            ie.description()


if __name__ == '__main__':
    unittest.main()
