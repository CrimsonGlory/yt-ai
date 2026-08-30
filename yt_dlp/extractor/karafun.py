import hashlib
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    encode_data_uri,
    format_field,
    int_or_none,
    url_or_none,
    xpath_text,
)


class KarafunIE(InfoExtractor):
    IE_NAME = 'Karafun'
    IE_DESC = 'KaraFun'
    _VALID_URL = r'https?://(?:www\.)?karafun\.com/web/?\?(?:[^#]*&)?song=(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://www.karafun.com/web/?song=11524',
            'md5': 'f8e08ecb6389367d22a3d959c924c93b',
            'info_dict': {
                'id': '11524',
                'ext': 'ogg',
                'title': 'Last Christmas',
                'track': 'Last Christmas',
                'artists': ['Wham!'],
                'release_year': 1984,
                'duration': 273,
                'thumbnail': r're:https://cdnaws\.recis\.io/i/api/.+\.jpg',
                'description': 'md5:b4fbd784a4af4fcfc4ad832089a39b29',
            },
        },
        {
            'url': 'https://karafun.com/web/?song=11524',
            'only_matching': True,
        },
        {
            'url': 'https://www.karafun.com/web/?song=11524&mod=1',
            'only_matching': True,
        },
    ]
    _API_BASE = 'https://www.karafun.com/api'
    _CLIENT_ID = '7'
    _CLIENT_VERSION = '3.12.1.147'
    _CLIENT_KEY = 'zS@nfy_j'
    _SIG_VERSION = 'kfun-v1.5'
    _KIT_MAGIC = b'\x01\xce\xd7'
    _TRACK_QUALITY = {
        'ins': 10,
        'bv': 5,
        'ld': 1,
    }
    _TRACK_NOTES = {
        'ins': 'Instrumental',
        'bv': 'Backing vocals',
        'ld': 'Lead vocals',
    }

    def _sign_headers(self, url, payload='', session_key=None):
        timestamp = str(int(time.time()))
        blob = '|'.join(part for part in (self._SIG_VERSION, url, payload, timestamp, session_key) if part)
        return {
            'X-Request-Timestamp': timestamp,
            'X-Request-Signature': hashlib.sha256(blob.encode()).hexdigest(),
        }

    def _call_api(self, path, video_id, query=None, session_key=None, note=None, fatal=True):
        url = f'{self._API_BASE}{path}'
        if query:
            url += '?' + urllib.parse.urlencode(query)
        xml = self._download_xml(
            url,
            video_id,
            note=note or f'Downloading {path}',
            headers=self._sign_headers(url, session_key=session_key),
            impersonate=True,
            fatal=fatal,
        )
        if xml is False or xml is None:
            return None
        if xml.get('status') == 'OK':
            return xml
        error = xpath_text(xml, './error', 'error', default='unknown')
        message = xpath_text(xml, './message', 'message', default=error)
        if not fatal:
            self.report_warning(f'KaraFun API error: {message}')
            return None
        raise ExtractorError(f'KaraFun API error: {message}', expected=True)

    def _get_session_key(self, video_id):
        xml = self._call_api(
            '/session/open.php',
            video_id,
            {
                'client': self._CLIENT_ID,
                'client_version': self._CLIENT_VERSION,
                'key': self._CLIENT_KEY,
                'protocol': '1',
                'device_name': 'KaraFun Web',
            },
            note='Opening KaraFun session',
        )
        session_key = xpath_text(xml, './session/key', 'session key')
        if not session_key:
            raise ExtractorError('Unable to open KaraFun session', expected=True)
        return session_key

    def _parse_kit_tracks(self, kit, video_id):
        if not kit.startswith(self._KIT_MAGIC) or len(kit) < 14:
            raise ExtractorError('Unrecognized KaraFun kit container', expected=True)

        offset = 4 + kit[3] * 5
        files = {}
        while offset + 9 <= len(kit):
            file_id = kit[offset]
            size = int.from_bytes(kit[offset + 2 : offset + 5], 'big')
            start, end = offset + 9, offset + 9 + size
            if end > len(kit):
                break
            files.setdefault(file_id, []).append(kit[start:end])
            offset = end

        joined = {file_id: b''.join(chunks) for file_id, chunks in files.items()}
        labels = {}
        xml_blob = joined.get(1)
        if xml_blob:
            kit_xml = self._parse_xml(xml_blob.decode('utf-8', 'replace'), video_id, fatal=False)
            for file_el in kit_xml.findall('.//files/file') if kit_xml is not None else []:
                file_id = int_or_none(file_el.get('index'))
                label = file_el.get('label') or (file_el.text or '').strip()
                if file_id and label:
                    labels[file_id] = label

        tracks = []
        for file_id, data in joined.items():
            if not data.startswith(b'OggS'):
                continue
            label = labels.get(file_id) or f'track{file_id}.ogg'
            format_id = label.rsplit('.', 1)[0]
            tracks.append((format_id, data))
        if not tracks:
            raise ExtractorError('No audio tracks found in KaraFun kit', expected=True)
        return tracks

    def _real_extract(self, url):
        video_id = self._match_id(url)
        session_key = self._get_session_key(video_id)

        song_xml = self._call_api(
            '/song/request.php',
            video_id,
            {
                'song': video_id,
                'offline': '0',
                'sk': session_key,
            },
            session_key=session_key,
            note='Downloading song metadata',
        )
        song = song_xml.find('./song')
        if song is None:
            raise ExtractorError('Song not found', expected=True)

        stream_url = url_or_none(xpath_text(song, './stream', 'stream URL'))
        if not stream_url:
            raise ExtractorError('No KaraFun stream URL', expected=True)

        is_preview = song.get('preview') == '1'
        if is_preview:
            self.report_warning('Only a preview is available without a KaraFun subscription')

        urlh = self._request_webpage(stream_url, video_id, note='Downloading karaoke kit')
        tracks = self._parse_kit_tracks(urlh.read(), video_id)

        formats = []
        for format_id, data in tracks:
            note = self._TRACK_NOTES.get(format_id, format_id)
            if is_preview:
                note = f'Preview, {note}'
            formats.append(
                {
                    'format_id': format_id,
                    'url': encode_data_uri(data, 'audio/ogg'),
                    'ext': 'ogg',
                    'acodec': 'vorbis',
                    'vcodec': 'none',
                    'quality': self._TRACK_QUALITY.get(format_id, -1),
                    'filesize': len(data),
                    'format_note': note,
                },
            )

        title = xpath_text(song, './title', 'title', default=None)
        artist = xpath_text(song, './artist', 'artist', default=None)
        image = song.find('./image')
        image_id = image.get('id') if image is not None else None

        lyrics_xml = self._call_api(
            '/song/lyrics.php',
            video_id,
            {
                'song': video_id,
                'sk': session_key,
            },
            session_key=session_key,
            note='Downloading lyrics',
            fatal=False,
        )
        description = xpath_text(lyrics_xml, './lyrics', 'lyrics', default=None) if lyrics_xml is not None else None

        return {
            'id': video_id,
            'title': title,
            'track': title,
            'artists': [artist] if artist else None,
            'release_year': int_or_none(xpath_text(song, './year', 'year', default=None)),
            'duration': int_or_none(song.get('preview-len') if is_preview else song.get('len')),
            'thumbnail': format_field(image_id, None, 'https://cdnaws.recis.io/i/api/%s/sq500.jpg'),
            'description': description,
            'formats': formats,
        }
