from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    extract_attributes,
    int_or_none,
    unified_strdate,
    url_or_none,
)


class TimesRadioIE(InfoExtractor):
    IE_NAME = 'TimesRadio'
    IE_DESC = 'Times Radio'
    _VALID_URL = r'https?://(?:www\.)?thetimes\.co(?:m|\.uk)/radio/(?:show/(?P<id>\d{8}-\d+)(?:/\d{4}-\d{2}-\d{2})?|(?P<live>live)(?:-player)?)'
    _TESTS = [{
        'url': 'https://www.thetimes.com/radio/show/20260828-34188/2026-08-28',
        'md5': '19f18aad115c82627f91bfed29c5e2ca',
        'info_dict': {
            'id': '20260828-34188',
            'ext': 'mp3',
            'title': 'Ryan Tubridy in for Ed Vaizey',
            'description': 'Lively discussion and debate around today\'s big stories',
            'thumbnail': r're:https?://.+\.(?:png|jpe?g|webp)',
            'duration': 10800,
            'upload_date': '20260828',
            'series': 'Times Radio',
        },
    }, {
        'url': 'https://www.thetimes.com/radio/show/20260828-34188',
        'only_matching': True,
    }, {
        'url': 'https://www.thetimes.co.uk/radio/show/20260828-34188/2026-08-28',
        'only_matching': True,
    }, {
        'url': 'https://www.thetimes.com/radio/live',
        'only_matching': True,
    }, {
        'url': 'https://www.thetimes.com/radio/live-player',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        is_live = bool(mobj.group('live'))
        video_id = mobj.group('id') or 'live'

        webpage = self._download_webpage(url, video_id)
        if 'Verifying your device' in webpage or 'toadmash' in webpage:
            webpage = self._download_webpage(
                url, video_id, note='Downloading webpage with impersonation',
                impersonate=True)

        player = extract_attributes(self._search_regex(
            r'(<div[^>]+class="[^"]*tm-wp-radio-(?:catch-up-player|listen-live)\b[^"]*"[^>]*>)',
            webpage, 'player', default='')) or {}

        audio_url = url_or_none(player.get('data-stream-url')) or url_or_none(
            self._search_regex(
                r'<audio[^>]+src=["\']([^"\']+)["\']',
                webpage, 'audio URL', default=None))
        if not audio_url:
            raise ExtractorError('No Times Radio audio source found', expected=True)

        ext = determine_ext(audio_url, 'aac' if is_live else 'mp3')
        if ext in ('unknown_video', 'stream'):
            ext = 'aac' if is_live else 'mp3'

        title = (
            self._html_search_regex(
                r'<h1[^>]+class="[^"]*tm-wp-radio-(?:catch-up-player|listen-live)__title"[^>]*>([^<]+)',
                webpage, 'title', default=None)
            or player.get('data-media-name')
            or self._og_search_title(webpage, default=None)
            or 'Times Radio')
        description = self._html_search_regex(
            r'<p[^>]+class="[^"]*tm-wp-radio-(?:catch-up-player|listen-live)__description"[^>]*>([^<]+)',
            webpage, 'description', default=None)
        thumbnail = (
            self._html_search_regex(
                r'<img[^>]+class="[^"]*presenter-image"[^>]+src=["\']([^"\']+)["\']',
                webpage, 'thumbnail', default=None)
            or self._og_search_thumbnail(webpage))

        upload_date = None
        if not is_live:
            upload_date = unified_strdate(self._html_search_regex(
                r'<p[^>]+class="[^"]*catch-up-date"[^>]*>\s*([^<]+)',
                webpage, 'upload date', default=None)) or video_id[:8]

        return {
            'id': video_id,
            'url': audio_url,
            'ext': ext,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': int_or_none(player.get('data-recording-duration'), scale=1000),
            'upload_date': upload_date,
            'series': 'Times Radio',
            'vcodec': 'none',
            'acodec': 'aac' if ext == 'aac' else 'mp3',
            'is_live': is_live,
        }
