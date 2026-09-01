import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class CrowdcastBaseIE(InfoExtractor):
    _API_URL = 'https://gql.crowdcast.io/v1/graphql'
    _API_HEADERS = {
        'Content-Type': 'application/json',
        'Origin': 'https://www.crowdcast.io',
        'Referer': 'https://www.crowdcast.io/',
    }

    def _call_api(self, query, variables, video_id, note='Downloading GraphQL JSON'):
        data = self._download_json(
            self._API_URL,
            video_id,
            note,
            data=json.dumps(
                {
                    'query': query,
                    'variables': variables,
                },
            ).encode(),
            headers=self._API_HEADERS,
        )
        if not data.get('data'):
            raise ExtractorError(
                traverse_obj(data, ('errors', 0, 'message', {str})) or 'Crowdcast GraphQL error', expected=True,
            )
        return data['data']

    def _parse_draftjs(self, raw):
        if not raw:
            return None
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (TypeError, ValueError):
                return raw
        texts = traverse_obj(raw, ('blocks', ..., 'text', {str}))
        return '\n'.join(filter(None, texts)) or None


class CrowdcastIE(CrowdcastBaseIE):
    IE_NAME = 'crowdcast'
    IE_DESC = 'Crowdcast'
    _VALID_URL = r'https?://(?:www\.)?crowdcast\.io/(?:[ce])/(?P<id>[\w-]+)(?:/(?P<session>[\w-]+))?(?:[?#]|$)'
    _EVENT_QUERY = '''query Event($code: String!) {
  events(where: {event_code: {_eq: $code}}) {
    id
    title
    event_code
    description
    cover_photo
    access
    private
    password_protected
    organization { name flag_nsfw }
    video_sessions(order_by: {time_scheduled: asc}) {
      id
      url_hash
      title
      description
      duration
      time_scheduled
      time_broadcast_start
      time_broadcast_end
      video_session_state_fkey
      video_session_type_fkey
      streams { live_playback_url vod_playback_url }
    }
  }
}'''
    _TESTS = [
        {
            'url': 'https://www.crowdcast.io/c/bdb-livereveal',
            'md5': '4e01dc14b1729fb3b2d0a2eaeca00035',
            'info_dict': {
                'id': '2766203',
                'ext': 'mp4',
                'display_id': 'bdb-livereveal',
                'title': 'The Billion Dollar Build: Live Reveal',
                'description': 'md5:d755ffc891f05ce54fa695725b6438f7',
                'thumbnail': 'https://images-production-crowdcast-lambdas.s3.amazonaws.com/events/21e4b143-b913-4cd2-8ca1-493d8a38443b/cover-photo-1780356538288.png',
                'uploader': 'Perplexity Fund',
                'duration': 2122,
                'timestamp': 1781020831,
                'upload_date': '20260609',
                'live_status': 'was_live',
            },
            'params': {'format': 'http-1080'},
        },
        {
            'url': 'https://www.crowdcast.io/e/gresham-numbers-cultures',
            'only_matching': True,
        },
        {
            'url': 'https://www.crowdcast.io/c/bdb-livereveal/XnMXU',
            'only_matching': True,
        },
    ]

    def _extract_session(self, event, session, fatal=True):
        session_id = str_or_none(session.get('id'))
        state = session.get('video_session_state_fkey')
        is_live = state == 'broadcasting'
        media_url = traverse_obj(
            session,
            (
                'streams',
                ...,
                ('vod_playback_url', 'live_playback_url') if not is_live else ('live_playback_url', 'vod_playback_url'),
                {url_or_none},
                any,
            ),
        )
        if not media_url:
            if fatal:
                self.raise_no_formats(
                    'This Crowdcast session has no public replay yet', expected=True, video_id=session_id,
                )
            return None

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            media_url, session_id, 'mp4', m3u8_id='hls', live=is_live,
        )
        if not is_live:
            for fmt in list(formats):
                hls_url = fmt.get('url')
                if determine_ext(hls_url) != 'm3u8':
                    continue
                height = fmt.get('height')
                formats.append(
                    {
                        'url': hls_url.rsplit('.', 1)[0] + '.mp4',
                        'ext': 'mp4',
                        'format_id': f'http-{height}' if height else 'http',
                        'width': fmt.get('width'),
                        'height': height,
                        'tbr': fmt.get('tbr'),
                        'vcodec': fmt.get('vcodec'),
                        'acodec': fmt.get('acodec'),
                    },
                )

        start = parse_iso8601(session.get('time_broadcast_start'))
        end = parse_iso8601(session.get('time_broadcast_end'))
        duration = end - start if start and end and end > start else int_or_none(session.get('duration'), invscale=60)

        if state == 'broadcasting':
            live_status = 'is_live'
        elif state in ('ended', 'postevent'):
            live_status = 'was_live'
        elif state in ('scheduled', 'greenroom'):
            live_status = 'is_upcoming'
        else:
            live_status = None

        return {
            'id': session_id,
            'display_id': event.get('event_code'),
            'title': session.get('title') or event.get('title'),
            'description': self._parse_draftjs(session.get('description'))
            or self._parse_draftjs(event.get('description')),
            'formats': formats,
            'subtitles': subtitles,
            'duration': duration,
            'timestamp': start or parse_iso8601(session.get('time_scheduled')),
            'live_status': live_status,
            **traverse_obj(
                event,
                {
                    'thumbnail': ('cover_photo', {url_or_none}),
                    'uploader': ('organization', 'name', {str}),
                    'age_limit': ('organization', 'flag_nsfw', {lambda v: 18 if v else None}),
                },
            ),
        }

    def _real_extract(self, url):
        event_code, session_hash = self._match_valid_url(url).group('id', 'session')
        event = traverse_obj(self._call_api(self._EVENT_QUERY, {'code': event_code}, event_code), ('events', 0, {dict}))
        if not event:
            raise ExtractorError('Crowdcast event not found', expected=True)

        sessions = traverse_obj(event, ('video_sessions', lambda _, v: v['id']))
        if session_hash:
            sessions = [s for s in sessions if s.get('url_hash') == session_hash]
            if not sessions:
                raise ExtractorError(f'Crowdcast session {session_hash} not found', expected=True)

        entries = []
        for session in sessions:
            if session.get('video_session_type_fkey') == 'lobby' and not traverse_obj(
                session, ('streams', ..., ('vod_playback_url', 'live_playback_url'), {url_or_none}),
            ):
                continue
            entry = self._extract_session(event, session, fatal=False)
            if entry:
                entries.append(entry)

        if not entries:
            self.raise_no_formats('No public Crowdcast replay is available', expected=True, video_id=event_code)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, event_code, event.get('title'), self._parse_draftjs(event.get('description')),
        )


class CrowdcastClipIE(CrowdcastBaseIE):
    IE_NAME = 'crowdcast:clip'
    IE_DESC = 'Crowdcast clips'
    _VALID_URL = r'https?://(?:www\.)?crowdcast\.io/clips/(?P<id>[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12})'
    _CLIP_QUERY = '''query Clip($slug: uuid!) {
  clips(where: {slug: {_eq: $slug}}) {
    id
    slug
    title
    playback_url
    thumbnail_url
    start_time
    end_time
    created_at
    event {
      title
      event_code
      organization { name flag_nsfw }
    }
  }
}'''
    _TESTS = [
        {
            'url': 'https://www.crowdcast.io/clips/e1812057-dfdd-416b-81ba-6a16c2d17b31',
            'md5': '55829c4ff718ba45248e71d03611d5ff',
            'info_dict': {
                'id': '3286',
                'ext': 'mp4',
                'display_id': 'e1812057-dfdd-416b-81ba-6a16c2d17b31',
                'title': 'Winner',
                'thumbnail': 'https://f005.backblazeb2.com/file/production-crowdcast-media/vods/2766203/clip-3286.jpg',
                'uploader': 'Perplexity Fund',
                'duration': 60,
                'timestamp': 1781734014,
                'upload_date': '20260617',
            },
        },
    ]

    def _real_extract(self, url):
        clip_slug = self._match_id(url)
        clip = traverse_obj(self._call_api(self._CLIP_QUERY, {'slug': clip_slug}, clip_slug), ('clips', 0, {dict}))
        if not clip:
            raise ExtractorError('Crowdcast clip not found', expected=True)

        media_url = traverse_obj(clip, ('playback_url', {url_or_none}))
        if not media_url:
            self.raise_no_formats('This Crowdcast clip has no media', expected=True, video_id=clip_slug)

        start = int_or_none(clip.get('start_time'))
        end = int_or_none(clip.get('end_time'))
        return {
            'id': str_or_none(clip.get('id')) or clip_slug,
            'display_id': clip_slug,
            'url': media_url,
            'ext': 'mp4',
            'duration': end - start if start is not None and end is not None and end > start else None,
            'timestamp': parse_iso8601(clip.get('created_at')),
            **traverse_obj(
                clip,
                {
                    'title': ('title', {str}),
                    'thumbnail': ('thumbnail_url', {url_or_none}),
                },
            ),
            **traverse_obj(
                clip,
                (
                    'event',
                    {
                        'uploader': ('organization', 'name', {str}),
                        'age_limit': ('organization', 'flag_nsfw', {lambda v: 18 if v else None}),
                    },
                ),
            ),
        }
