import base64
import contextlib
import json
import os
import socket
import ssl
import struct
import time
import urllib.parse

from .common import InfoExtractor
from ..downloader import PROTOCOL_MAP
from ..downloader.common import FileDownloader
from ..networking import Request
from ..utils import (
    DownloadError,
    ExtractorError,
    join_nonempty,
    parse_iso8601,
    qualities,
    update_url_query,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class JCBASimulFD(FileDownloader):
    """Download JCBA Internet Simul Radio Ogg Opus from a Radimo WebSocket."""

    FD_NAME = 'jcbasimul'

    _API_URL = 'https://www.jcbasimul.com/api/select_stream'
    _ORIGIN = 'https://www.jcbasimul.com'
    _SUBPROTOCOL = 'listener.fmplapla.com'

    def _select_stream(self, station, quality):
        url = update_url_query(
            self._API_URL,
            {
                'station': station,
                'channel': '0',
                'quality': quality,
                'burst': '5',
            },
        )
        response = self.ydl.urlopen(
            Request(
                url,
                headers={
                    'Origin': self._ORIGIN,
                    'Referer': f'{self._ORIGIN}/',
                },
            ),
        )
        try:
            data = json.loads(response.read())
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            raise DownloadError(f'Invalid JCBA stream JSON: {e}') from e
        location, token = data.get('location'), data.get('token')
        if data.get('code') != 200 or not location or not token:
            raise DownloadError(data.get('error') or 'Unable to obtain JCBA stream token')
        return location, token

    def _open_websocket(self, ws_url, token):
        parsed = urllib.parse.urlparse(ws_url)
        if parsed.scheme not in ('ws', 'wss') or not parsed.hostname:
            raise DownloadError(f'Invalid JCBA WebSocket URL: {ws_url}')
        port = parsed.port or (443 if parsed.scheme == 'wss' else 80)
        path = parsed.path or '/'
        if parsed.query:
            path = f'{path}?{parsed.query}'
        timeout = self.params.get('socket_timeout') or 20
        sock = socket.create_connection((parsed.hostname, port), timeout=timeout)
        try:
            if parsed.scheme == 'wss':
                ctx = ssl.create_default_context()
                if self.params.get('nocheckcertificate'):
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                sock = ctx.wrap_socket(sock, server_hostname=parsed.hostname)
            key = base64.b64encode(os.urandom(16)).decode()
            sock.sendall(
                (
                    f'GET {path} HTTP/1.1\r\n'
                    f'Host: {parsed.hostname}:{port}\r\n'
                    'Upgrade: websocket\r\n'
                    'Connection: Upgrade\r\n'
                    f'Sec-WebSocket-Key: {key}\r\n'
                    'Sec-WebSocket-Version: 13\r\n'
                    f'Sec-WebSocket-Protocol: {self._SUBPROTOCOL}\r\n'
                    f'Origin: {self._ORIGIN}\r\n'
                    '\r\n'
                ).encode(),
            )
            buf = b''
            while b'\r\n\r\n' not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    raise DownloadError('JCBA WebSocket handshake closed')
                buf += chunk
            header, rest = buf.split(b'\r\n\r\n', 1)
            status = header.split(b'\r\n', 1)[0].decode('latin-1', 'replace')
            if b' 101 ' not in header.split(b'\r\n', 1)[0]:
                raise DownloadError(f'JCBA WebSocket handshake failed: {status}')
            conn = _JCBAWebSocket(sock, rest)
            conn.send_text(token)
            return conn
        except BaseException:
            sock.close()
            raise

    def real_download(self, filename, info_dict):
        opts = info_dict.get('downloader_options') or {}
        station, quality = opts.get('station'), opts.get('quality') or 'high'
        if not station:
            self.report_error('Missing JCBA station id')
            return False

        is_test = self.params.get('test', False)
        max_bytes = self._TEST_FILE_SIZE if is_test else None
        tmpfilename = self.temp_name(filename)
        try:
            stream, tmpfilename = self.sanitize_open(tmpfilename, 'wb')
        except OSError as err:
            self.report_error(f'unable to open for writing: {err}')
            return False
        filename = self.undo_temp_name(tmpfilename)
        self.report_destination(filename)

        start = time.time()
        byte_counter = 0
        conn = None
        try:
            location, token = self._select_stream(station, quality)
            self.write_debug(f'JCBA WebSocket: {location}')
            conn = self._open_websocket(location, token)
            for payload in conn.iter_binary():
                if max_bytes is not None:
                    payload = payload[: max_bytes - byte_counter]
                if not payload:
                    break
                stream.write(payload)
                byte_counter += len(payload)
                now = time.time()
                self._hook_progress(
                    {
                        'status': 'downloading',
                        'downloaded_bytes': byte_counter,
                        'tmpfilename': tmpfilename,
                        'filename': filename,
                        'elapsed': now - start,
                        'speed': self.calc_speed(start, now, byte_counter),
                        'eta': None,
                    },
                    info_dict,
                )
                if max_bytes is not None and byte_counter >= max_bytes:
                    break
        except KeyboardInterrupt:
            if not byte_counter:
                raise
        except OSError as err:
            if not byte_counter:
                self.report_error(f'JCBA WebSocket error: {err}')
                return False
        finally:
            if conn:
                conn.close()
            if tmpfilename != '-':
                stream.close()

        if not byte_counter:
            self.report_error('Did not get any data blocks')
            if tmpfilename != '-':
                self.try_remove(tmpfilename)
            return False

        self.try_rename(tmpfilename, filename)
        self._hook_progress(
            {
                'downloaded_bytes': byte_counter,
                'total_bytes': byte_counter,
                'filename': filename,
                'status': 'finished',
                'elapsed': time.time() - start,
            },
            info_dict,
        )
        return True


class _JCBAWebSocket:
    def __init__(self, sock, leftover=b''):
        self.sock = sock
        self._buf = bytearray(leftover)

    def close(self):
        with contextlib.suppress(OSError):
            self.sock.sendall(_ws_frame(0x8, b''))
        with contextlib.suppress(OSError):
            self.sock.close()

    def send_text(self, text):
        self.sock.sendall(_ws_frame(0x1, text.encode()))

    def send_frame(self, opcode, payload):
        self.sock.sendall(_ws_frame(opcode, payload))

    def _read_exact(self, n):
        while len(self._buf) < n:
            chunk = self.sock.recv(max(4096, n - len(self._buf)))
            if not chunk:
                raise OSError('JCBA WebSocket closed')
            self._buf.extend(chunk)
        data = bytes(self._buf[:n])
        del self._buf[:n]
        return data

    def recv_message(self):
        pieces, opcode = [], None
        while True:
            b1, b2 = self._read_exact(2)
            fin, op = b1 >> 7, b1 & 0x0F
            masked, plen = b2 >> 7, b2 & 0x7F
            if plen == 126:
                plen = struct.unpack('!H', self._read_exact(2))[0]
            elif plen == 127:
                plen = struct.unpack('!Q', self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else b''
            payload = self._read_exact(plen)
            if masked:
                payload = bytes(p ^ mask[i % 4] for i, p in enumerate(payload))
            if op == 0x8:
                return 0x8, payload
            if op == 0x9:
                self.send_frame(0xA, payload)
                continue
            if op == 0xA:
                continue
            if op:
                opcode = op
            pieces.append(payload)
            if fin:
                return opcode, b''.join(pieces)

    def iter_binary(self):
        while True:
            opcode, payload = self.recv_message()
            if opcode == 0x8:
                return
            if opcode == 0x2 and payload:
                yield payload


def _ws_frame(opcode, payload):
    if isinstance(payload, str):
        payload = payload.encode()
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    header = bytearray((0x80 | opcode,))
    n = len(payload)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack('!H', n))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack('!Q', n))
    header.extend(mask)
    return bytes(header) + masked


PROTOCOL_MAP['jcbasimul_wss'] = JCBASimulFD


class JCBASimulIE(InfoExtractor):
    IE_NAME = 'jcbasimul'
    IE_DESC = 'JCBA Internet Simul Radio'
    _VALID_URL = (
        r'https?://(?:www\.)?jcbasimul\.com/(?P<id>(?!about|faq|kiyaku|policy|rinsai|bookmark)[a-z][a-z0-9]*)'
        r'(?:/rawplayer)?/?(?:[?#]|$)'
    )
    _API_HEADERS = {
        'Origin': 'https://www.jcbasimul.com',
        'Referer': 'https://www.jcbasimul.com/',
    }
    _TESTS = [
        {
            'url': 'https://www.jcbasimul.com/fmhana',
            'info_dict': {
                'id': 'fmhana',
                'ext': 'ogg',
                'title': r're:ＦＭはな',
                'description': '宇宙から見える格子状防風林の中心空とみどりの交流拠点中標津町から繋がる、ひろがる地域情報を発信中',
                'thumbnail': r're:https://radimo\.s3\.amazonaws\.com/logo/.+',
                'channel': 'ＦＭはな',
                'channel_id': 'fmhana',
                'channel_url': 'https://www.jcbasimul.com/fmhana',
                'uploader': 'ＦＭはな',
                'uploader_id': 'fmhana',
                'location': '中標津町, 北海道',
                'is_live': True,
                'live_status': 'is_live',
            },
        },
        {
            'url': 'https://www.jcbasimul.com/fmyamato',
            'only_matching': True,
        },
        {
            'url': 'https://www.jcbasimul.com/fmhana/rawplayer',
            'only_matching': True,
        },
    ]

    def _fetch_stream(self, station_id, quality):
        info = self._download_json(
            'https://www.jcbasimul.com/api/select_stream',
            station_id,
            note=f'Downloading {quality} stream info',
            query={
                'station': station_id,
                'channel': '0',
                'quality': quality,
                'burst': '5',
            },
            headers=self._API_HEADERS,
            fatal=False,
            expected_status=(400, 401, 403, 404),
        )
        code = traverse_obj(info, 'code')
        if code in (401, 403):
            self.raise_geo_restricted(
                msg=traverse_obj(info, 'error', {str}) or 'This radio stream is not available from your location',
                countries=['JP'],
            )
        location = traverse_obj(info, ('location', {url_or_none}))
        if code != 200 or not location:
            return None
        return location

    def _real_extract(self, url):
        station_id = self._match_id(url)
        webpage = self._download_webpage(f'https://www.jcbasimul.com/{station_id}', station_id)
        station = (
            traverse_obj(
                self._search_nextjs_data(webpage, station_id, default={}), ('props', 'pageProps', 'station', {dict}),
            )
            or {}
        )
        if not station and 'station' not in webpage:
            raise ExtractorError('Unable to extract JCBA station', expected=True)

        timetable = self._download_json(
            f'https://www.jcbasimul.com/api/timetable/current/{station_id}',
            station_id,
            'Downloading current program',
            fatal=False,
            expected_status=404,
        )
        program = traverse_obj(timetable, ('current', {dict})) or {}

        quality = qualities(('low', 'high'))
        formats = []
        for qid in ('low', 'high'):
            location = self._fetch_stream(station_id, qid)
            if not location:
                continue
            formats.append(
                {
                    'url': location,
                    'format_id': f'wss-{qid}',
                    'protocol': 'jcbasimul_wss',
                    'ext': 'ogg',
                    'acodec': 'opus',
                    'vcodec': 'none',
                    'quality': quality(qid),
                    'no_resume': True,
                    'downloader_options': {
                        'station': station_id,
                        'quality': qid,
                    },
                },
            )
        if not formats:
            self.raise_no_formats('No JCBA radio stream available', expected=True, video_id=station_id)

        station_name = traverse_obj(station, ('name', {str})) or station_id
        program_title = traverse_obj(program, ('title', {str}))
        performer = traverse_obj(program, ('performer', {str}))
        return {
            'id': station_id,
            'title': join_nonempty(station_name, program_title, delim=' - '),
            'description': traverse_obj(station, ('description', {str})),
            'thumbnail': traverse_obj(station, ('logo_url', {url_or_none})),
            'channel': station_name,
            'channel_id': station_id,
            'channel_url': f'https://www.jcbasimul.com/{station_id}',
            'uploader': station_name,
            'uploader_id': station_id,
            'location': join_nonempty(
                traverse_obj(station, ('city', {str})), traverse_obj(station, ('prefecture', {str})), delim=', ',
            ),
            'cast': [performer] if performer else None,
            'timestamp': traverse_obj(program, ('air_start', {parse_iso8601})),
            'webpage_url': f'https://www.jcbasimul.com/{station_id}',
            'formats': formats,
            'is_live': True,
        }
