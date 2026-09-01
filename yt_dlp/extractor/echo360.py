import re
import urllib.parse

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    join_nonempty,
    parse_duration,
    traverse_obj,
    update_url,
    url_or_none,
)


class Echo360IE(InfoExtractor):
    IE_NAME = 'echo360'
    IE_DESC = 'Echo360 / EchoVideo'
    _VALID_URL = r'https?://(?:www\.)?echo360\.(?:org|net)(?:\.[a-z]{2})?/(?:public/)?media/(?P<id>[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})(?:/public)?'
    _TESTS = [{
        'url': 'https://echo360.net.au/media/f04960a9-2efc-4b63-87b5-72e629081d15/public',
        'md5': 'dff41b03317f0905d385603b2d7f349a',
        'info_dict': {
            'id': 'f04960a9-2efc-4b63-87b5-72e629081d15',
            'ext': 'mp4',
            'title': 'EXSC634_Online_Workshop_Week_4.mp4',
            'duration': 6659.72,
            'thumbnail': r're:https://thumbnails\.echo360\.net\.au/.+',
        },
        'params': {
            'format': 'bv',
        },
    }, {
        'url': 'https://echo360.net.au/public/media/f04960a9-2efc-4b63-87b5-72e629081d15',
        'only_matching': True,
    }, {
        'url': 'https://echo360.org.au/media/bca6287f-ecb7-4e28-8eba-8cebe1068ae0/public',
        'only_matching': True,
    }, {
        'url': 'https://echo360.org/media/0d046a3e-26e1-4dc1-ba3a-63af2d2734fb/public',
        'only_matching': True,
    }]

    def _signed_query(self, uri, query_strings):
        for item in query_strings or []:
            pattern, query = item.get('uriPattern'), item.get('queryString')
            if not query:
                continue
            if not pattern:
                return query
            try:
                if re.match(pattern, uri):
                    return query
            except re.error:
                continue
        return None

    def _extract_playable_formats(self, playable, query_strings, video_id):
        formats, subtitles = [], {}
        medias = traverse_obj(playable, ('playableMedias', ..., {dict})) or []
        combined = [
            m for m in medias
            if m.get('isHls') and {'Audio', 'Video'} <= set(m.get('trackType') or [])]
        for media in combined or [m for m in medias if m.get('isHls')]:
            uri = url_or_none(media.get('uri'))
            if not uri:
                continue
            query = self._signed_query(uri, query_strings)
            signed_url = update_url(uri, query=query) if query else uri
            track = '-'.join(media.get('trackType') or [])
            m3u8_id = join_nonempty('hls', media.get('sourceIndex'), track)
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                signed_url, video_id, 'mp4', m3u8_id=m3u8_id, fatal=False)
            for fmt in hls_fmts:
                if query:
                    fmt['url'] = update_url(fmt['url'], query=query)
                    fmt['extra_param_to_segment_url'] = query
                m4s_url = re.sub(r'\.m3u8(\?|$)', r'.m4s\1', fmt.get('url') or '')
                if m4s_url and m4s_url != fmt.get('url'):
                    http_fmt = {k: fmt[k] for k in (
                        'width', 'height', 'tbr', 'vcodec', 'acodec', 'fps',
                        'dynamic_range', 'has_drm',
                    ) if fmt.get(k) is not None}
                    http_fmt.update({
                        'url': m4s_url,
                        'ext': 'm4a' if fmt.get('vcodec') == 'none' else 'mp4',
                        'format_id': join_nonempty('http', fmt.get('format_id')),
                        'protocol': 'https',
                    })
                    formats.append(http_fmt)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, video_id)
        if '/login' in (urlh.url or ''):
            self.raise_login_required()

        boot_arg = self._search_regex(
            r'Echo\["(?:echoPlayerV2FullBootstrapApp|mediaPlayerBootstrapApp)"\]\((.+?)\)\s*;',
            webpage, 'player bootstrap')
        bootstrap = self._parse_json(boot_arg, video_id)
        if isinstance(bootstrap, str):
            bootstrap = self._parse_json(bootstrap, video_id)

        media_id = traverse_obj(bootstrap, ('mediaId', {str}))
        session_id = traverse_obj(bootstrap, ('sessionId', {str}))
        public_link_id = traverse_obj(bootstrap, ('publicLinkId', {str})) or video_id
        if not media_id or not session_id:
            raise ExtractorError('Unable to extract Echo360 player bootstrap', expected=True)

        parsed = urllib.parse.urlparse(urlh.url or url)
        base = f'{parsed.scheme}://{parsed.netloc}'

        try:
            token_urlh = self._request_webpage(
                f'{base}/api/ui/sessions/{session_id}', video_id,
                note='Downloading session token')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (401, 403):
                self.raise_login_required()
            raise
        token = token_urlh.get_header('token')
        if not token:
            raise ExtractorError('Unable to extract session token')

        try:
            props = self._download_json(
                f'{base}/api/ui/echoplayer/public-links/{public_link_id}/media/{media_id}/player-properties',
                video_id, note='Downloading player properties',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json',
                })
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (401, 403):
                self.raise_login_required()
            raise

        data = traverse_obj(props, ('data', {dict})) or {}
        if traverse_obj(data, ('copyrightData', 'restrictUnauthenticatedViewing')):
            self.raise_login_required()

        playable = traverse_obj(data, ('playableAudioVideo', {dict})) or {}
        query_strings = traverse_obj(data, ('sourceQueryStrings', 'queryStrings', ..., {dict}))
        formats, subtitles = self._extract_playable_formats(playable, query_strings, video_id)
        if not formats:
            raise ExtractorError('No playable media found', expected=True)

        return {
            'id': video_id,
            'title': data.get('mediaName') or self._html_extract_title(webpage),
            'duration': parse_duration(playable.get('duration')),
            'thumbnail': traverse_obj(playable, ('posterMedia', 0, 'uri', {url_or_none})),
            'formats': formats,
            'subtitles': subtitles,
        }
