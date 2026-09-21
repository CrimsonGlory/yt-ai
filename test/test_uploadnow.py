#!/usr/bin/env python3

# Allow direct execution
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from yt_dlp.extractor.uploadnow import UploadNowIE
from yt_dlp.networking.common import Response
from yt_dlp.networking.exceptions import HTTPError
from yt_dlp.utils import ExtractorError


class UploadNowFixtureYDL(FakeYDL):
    def __init__(self, pages, override=None):
        super().__init__(override)
        self._pages = pages

    def _response(self, payload, url, status=200):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return Response(
            io.BytesIO(data), url,
            {'Content-Type': 'application/json'}, status=status)

    def urlopen(self, req):
        url = req.url if hasattr(req, 'url') else str(req)
        raw = req.data if hasattr(req, 'data') else None
        body = json.loads(raw.decode()) if raw else {}
        for needle, payload in self._pages.items():
            if needle not in url:
                continue
            if callable(payload):
                payload, status = payload(body)
            elif isinstance(payload, tuple):
                payload, status = payload
            else:
                status = 200
            response = self._response(payload, url, status)
            if status >= 400:
                raise HTTPError(response)
            return response
        raise AssertionError(f'unexpected request: {url} body={body}')


FOLDER_LISTING = {
    'parentFolder': {
        'id': 'TWKzN8d',
        'name': 'jhqzd3tC',
        'description': '',
    },
    'folders': [{
        'id': 'nested1',
        'name': 'clips',
    }],
    'files': [{
        'id': 'file-mp4',
        'name': 'clip.mp4',
        'folderId': 'TWKzN8d',
        'size': 110680,
        'createDate': '2026-09-20T06:26:08.655Z',
    }, {
        'id': 'file-jpg',
        'name': 'photo.jpg',
        'folderId': 'TWKzN8d',
        'size': 124016,
        'createDate': '2026-09-20T06:26:06.363Z',
    }],
}

NESTED_LISTING = {
    'parentFolder': {'id': 'nested1', 'name': 'clips'},
    'folders': [],
    'files': [{
        'id': 'file-nested',
        'name': 'inside.webp',
        'folderId': 'nested1',
        'size': 100844,
        'createDate': '2026-09-20T06:26:05.537Z',
    }],
}

FILE_META = {
    'id': 'file-mp4',
    'name': 'clip.mp4',
    'folderId': 'TWKzN8d',
    'size': 110680,
    'createDate': '2026-09-20T06:26:08.655Z',
}


class TestUploadNow(unittest.TestCase):
    def test_folder_and_nested_files(self):
        def folder_content(body):
            folder_id = body.get('folderId')
            if folder_id == 'nested1':
                return NESTED_LISTING, 200
            if folder_id == 'TWKzN8d':
                return FOLDER_LISTING, 200
            return {'error': f'folder "{folder_id}" does not exist'}, 404

        def download_links(body):
            file_id = body['folderGroups'][0]['selectedFiles'][0]
            return {'url': f'https://cdn.example/file/{file_id}'}, 201

        ydl = UploadNowFixtureYDL({
            'accounts:signUp': {'idToken': 'guest-token'},
            '/file/search/folder-content': folder_content,
            '/file/downloads/links': download_links,
        })
        info = UploadNowIE(ydl).extract('https://uploadnow.io/files/TWKzN8d')
        self.assertEqual(info['id'], 'TWKzN8d')
        self.assertEqual(info['title'], 'jhqzd3tC')
        entries = list(info['entries'])
        by_id = {entry['id']: entry for entry in entries}
        self.assertEqual(set(by_id), {'file-mp4', 'file-jpg', 'file-nested'})
        self.assertEqual(by_id['file-mp4']['ext'], 'mp4')
        self.assertEqual(by_id['file-mp4']['title'], 'clip')
        self.assertEqual(by_id['file-mp4']['url'], 'https://cdn.example/file/file-mp4')
        self.assertEqual(by_id['file-mp4']['filesize'], 110680)
        self.assertEqual(by_id['file-nested']['ext'], 'webp')
        self.assertEqual(by_id['file-jpg']['http_headers']['Referer'], 'https://uploadnow.io/')

    def test_single_file_url(self):
        ydl = UploadNowFixtureYDL({
            'accounts:signUp': {'idToken': 'guest-token'},
            '/file/search/file': FILE_META,
            '/file/downloads/links': ({'url': 'https://cdn.example/clip.mp4'}, 201),
        })
        info = UploadNowIE(ydl).extract(
            'https://uploadnow.io/s/dfd16b2a-809d-4194-91d2-9a08763bb79b')
        self.assertEqual(info['id'], 'file-mp4')
        self.assertEqual(info['ext'], 'mp4')
        self.assertEqual(info['url'], 'https://cdn.example/clip.mp4')
        self.assertEqual(info['filesize'], 110680)

    def test_missing_folder(self):
        ydl = UploadNowFixtureYDL({
            'accounts:signUp': {'idToken': 'guest-token'},
            '/file/search/folder-content': ({'error': 'folder does not exist'}, 404),
        })
        with self.assertRaises(ExtractorError) as ctx:
            UploadNowIE(ydl).extract('https://uploadnow.io/files/missing')
        self.assertTrue(ctx.exception.expected)
        self.assertIn('not found', str(ctx.exception).lower())

    def test_password_required(self):
        ydl = UploadNowFixtureYDL({
            'accounts:signUp': {'idToken': 'guest-token'},
            '/file/search/folder-content': ({'error': 'Forbidden', 'codes': []}, 403),
        })
        with self.assertRaises(ExtractorError) as ctx:
            UploadNowIE(ydl).extract('https://uploadnow.io/files/secret')
        self.assertTrue(ctx.exception.expected)
        self.assertIn('password', str(ctx.exception).lower())

    def test_locale_and_www_urls_match(self):
        self.assertTrue(UploadNowIE.suitable('https://uploadnow.io/en/files/TWKzN8d'))
        self.assertTrue(UploadNowIE.suitable('https://www.uploadnow.io/files/TWKzN8d'))
        self.assertTrue(UploadNowIE.suitable('https://uploadnow.io/f/g6dMJDT'))
        self.assertTrue(UploadNowIE.suitable('https://uploadnow.io/en/share?utm_source=g6dMJDT'))
        self.assertTrue(UploadNowIE.suitable(
            'https://uploadnow.io/s/dfd16b2a-809d-4194-91d2-9a08763bb79b'))
        self.assertFalse(UploadNowIE.suitable('https://uploadnow.io/faq'))
        self.assertFalse(UploadNowIE.suitable('https://uploadnow.io/files/'))

    def test_short_f_url_is_a_folder(self):
        ydl = UploadNowFixtureYDL({
            'accounts:signUp': {'idToken': 'guest-token'},
            '/file/search/folder-content': {
                'parentFolder': {'id': 'g6dMJDT', 'name': 'SMB0RoUS'},
                'folders': [],
                'files': [FILE_META],
            },
            '/file/downloads/links': ({'url': 'https://cdn.example/clip.mp4'}, 201),
        })
        info = UploadNowIE(ydl).extract('https://uploadnow.io/f/g6dMJDT')
        self.assertEqual(info['id'], 'g6dMJDT')
        self.assertEqual(info['title'], 'SMB0RoUS')
        entries = list(info['entries'])
        self.assertEqual(entries[0]['url'], 'https://cdn.example/clip.mp4')

    def test_share_utm_source_is_a_folder(self):
        ydl = UploadNowFixtureYDL({
            'accounts:signUp': {'idToken': 'guest-token'},
            '/file/search/folder-content': {
                'parentFolder': {'id': 'g6dMJDT', 'name': 'SMB0RoUS'},
                'folders': [],
                'files': [FILE_META],
            },
            '/file/downloads/links': ({'url': 'https://cdn.example/clip.mp4'}, 201),
        })
        info = UploadNowIE(ydl).extract('https://uploadnow.io/en/share?utm_source=g6dMJDT')
        self.assertEqual(info['id'], 'g6dMJDT')
        self.assertEqual(len(list(info['entries'])), 1)


if __name__ == '__main__':
    unittest.main()
