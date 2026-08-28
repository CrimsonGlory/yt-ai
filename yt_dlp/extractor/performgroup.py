import urllib.parse

from .common import InfoExtractor
from ..utils import int_or_none, join_nonempty, url_or_none


class PerformGroupIE(InfoExtractor):
    _VALID_URL = r'https?://player\.(?:performgroup|daznservices)\.com/(?:eplayer(?:/eplayer\.html|\.js)|player(?:/player\.html|\.js))#/?(?P<id>[0-9a-f]{26})\.(?P<auth_token>[0-9a-z]{26})'
    _DEAD_MEDIA_HOSTS = {
        'cms.downloadvod.daznservices.com',
        'daznplayervod.daznservices.com',
        'daznplayersp-vh.akamaihd.net',
        'playersp-vh.akamaihd.net',
    }
    _TESTS = [{
        # leftover FAZ embed; Perform Feeds ep3 bootstrap host is gone
        'url': 'http://player.performgroup.com/eplayer/eplayer.html#d478c41c5d192f56b9aa859de8.1w4crrej5w14e1ed4s1ce4ykab',
        'skip': 'Old Perform Feeds ep3 API is gone; media for this clip 404s',
        'md5': '259cb03d142e2e52471e8837ecacb29f',
        'info_dict': {
            'id': 'xgrwobuzumes1lwjxtcdpwgxd',
            'ext': 'mp4',
            'title': 'Liga MX: Keine Einsicht nach Horrorfoul',
            'description': 'md5:7cd3b459c82725b021e046ab10bf1c5b',
            'timestamp': 1511533477,
            'upload_date': '20171124',
        },
    }, {
        # https://www.madeinmotorsport.com/ (eplayer.js embed); vid selects a still-hosted CloudFront MP4
        'url': 'https://player.performgroup.com/eplayer.js#2bd35a1885308c70f6edb804b9.13e9n12gjo4fb156b32gbffgtr$vid=1njd51qu0xzed19i50dxv052uu',
        'md5': '4c354dbadc5c9fc093657d86869cc4a6',
        'info_dict': {
            'id': '1njd51qu0xzed19i50dxv052uu',
            'ext': 'mp4',
            'title': 'CLEAN_WITHOUT_SUBTITLES_PSG_TITLE_DEDICATION_PSG',
            'description': 'English, Portuguese and Spanish versions also available.',
            'duration': 55,
            'timestamp': 1588759200,
            'upload_date': '20200506',
            'thumbnail': r're:https://images\.daznservices\.com/.+',
        },
    }, {
        'url': 'https://player.daznservices.com/player.js#2bd35a1885308c70f6edb804b9.13e9n12gjo4fb156b32gbffgtr',
        'only_matching': True,
    }]

    def _call_api(self, service, auth_token, content_id, referer_url, **kwargs):
        url = f'https://api.daznfeeds.com/{service}/{auth_token}/'
        if content_id:
            url += f'{content_id}/'
        return self._download_json(
            url, content_id or auth_token, headers={
                'Referer': referer_url,
                'Origin': 'https://player.daznservices.com',
                'PF-HOSTPAGE': referer_url.split('#', 1)[0],
            }, query={
                '_fmt': 'json',
                '_rt': 'c',
            }, **kwargs)

    def _media_url_is_playable(self, media_url):
        if not url_or_none(media_url):
            return False
        host = (urllib.parse.urlparse(media_url).hostname or '').lower()
        return host not in self._DEAD_MEDIA_HOSTS

    def _extract_formats(self, media, video_id):
        formats = []
        hls_url = (media.get('hls') or {}).get('url')
        if self._media_url_is_playable(hls_url):
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))

        hds_url = (media.get('hds') or {}).get('url')
        if self._media_url_is_playable(hds_url):
            formats.extend(self._extract_f4m_formats(
                hds_url + '?hdcore', video_id, f4m_id='hds', fatal=False))

        for c in media.get('content') or []:
            c_url = c.get('url')
            if not self._media_url_is_playable(c_url) or c.get('type') == 'thumbnail':
                continue
            tbr = int_or_none(c.get('bitrate'), 1000)
            formats.append({
                'format_id': join_nonempty('http', tbr),
                'url': c_url,
                'tbr': tbr,
                'width': int_or_none(c.get('width')),
                'height': int_or_none(c.get('height')),
                'filesize': int_or_none(c.get('fileSize')),
                'vcodec': c.get('type'),
                'fps': int_or_none(c.get('videoFrameRate')),
                'vbr': int_or_none(c.get('videoRate'), 1000),
                'abr': int_or_none(c.get('audioRate'), 1000),
            })
        return formats

    def _real_extract(self, url):
        player_id, auth_token = self._match_valid_url(url).group('id', 'auth_token')
        fragment = url.split('#', 1)[-1]
        custom = fragment.split('$', 1)[1] if '$' in fragment else ''
        params = urllib.parse.parse_qs(custom)
        video_id = (params.get('vid') or params.get('videoid') or [None])[0]

        vod = self._call_api('vod', auth_token, video_id, url)
        video = vod['videos']['video'][0]
        video_id = video.get('id') or video.get('uuid') or video_id or player_id
        media = video.get('media') or {}
        formats = self._extract_formats(media, video_id)
        if not formats:
            self.raise_no_formats(
                'No playable formats (DAZN Player CDNs for this clip are gone)',
                expected=True, video_id=video_id)

        thumbnails = media.get('thumbnail') or []
        thumbnail = video.get('poster') or (thumbnails[0].get('url') if thumbnails else None)

        return {
            'id': video_id,
            'title': video['title'],
            'description': video.get('description'),
            'thumbnail': thumbnail,
            'duration': int_or_none(video.get('duration')),
            'timestamp': int_or_none(video.get('publishedTime'), 1000),
            'formats': formats,
        }
