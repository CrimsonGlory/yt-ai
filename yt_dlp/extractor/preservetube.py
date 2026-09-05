import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    orderedSet,
    parse_resolution,
    remove_end,
    traverse_obj,
    unified_strdate,
    url_or_none,
    urljoin,
)


class PreserveTubeIE(InfoExtractor):
    IE_NAME = 'preservetube'
    IE_DESC = 'PreserveTube'
    _VALID_URL = r'https?://(?:www\.)?preservetube\.com/(?:watch\?(?:[^#]*&)?v=|video/)(?P<id>[\w-]{11}(?:-\d+)?)'
    _API_HEADERS = {
        'User-Agent': 'yt-ai/1.0 (https://github.com/CrimsonGlory/yt-ai; PreserveTube extractor)',
    }
    _TESTS = [{
        'url': 'https://preservetube.com/watch?v=NQlXDZnss1g',
        'md5': 'f0a0160e00e09feae6b52212e55b85a4',
        'info_dict': {
            'id': 'NQlXDZnss1g',
            'ext': 'mp4',
            'title': 'Hardest Math Problem You Already Learned in High School | Thomson Problem',
            'description': 'md5:2e487e52bb962c667f7aa9ed9a8f8184',
            'thumbnail': r're:https?://.+\.webp',
            'upload_date': '20250106',
            'channel': 'EpsilonDelta',
            'channel_id': 'UCrn9HkH3trWYpxzlW9l8eSg',
            'channel_url': 'https://preservetube.com/channel/UCrn9HkH3trWYpxzlW9l8eSg',
            'uploader': 'EpsilonDelta',
            'uploader_id': 'UCrn9HkH3trWYpxzlW9l8eSg',
            'uploader_url': 'https://preservetube.com/channel/UCrn9HkH3trWYpxzlW9l8eSg',
        },
    }, {
        'url': 'https://preservetube.com/video/NQlXDZnss1g',
        'only_matching': True,
    }, {
        'url': 'https://www.preservetube.com/watch?v=nz-z4hNccQM',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            f'https://preservetube.com/video/{video_id}', video_id,
            headers=self._API_HEADERS, fatal=False, expected_status=404)
        if isinstance(data, dict) and data.get('id'):
            return self._parse_api_data(data, video_id)
        if isinstance(data, dict) and data.get('error'):
            raise ExtractorError('Archive not found', expected=True)
        return self._extract_from_html(video_id)

    def _parse_api_data(self, data, video_id):
        stage = traverse_obj(data, ('deletion_stage', {str}))
        if traverse_obj(data, ('disabled', {bool})) or stage in ('deleted', 'soft_delete'):
            unplayable = 'This video has been removed from PreserveTube'
        elif stage == 'cold_storage':
            unplayable = 'This video has been moved to cold storage; email admin@preservetube.com to retrieve it'
        else:
            unplayable = None

        media_url = None if unplayable else traverse_obj(data, ('source', {url_or_none}))
        if not media_url:
            self.raise_no_formats(
                unplayable or 'No video source found', expected=True, video_id=video_id)

        channel_id = traverse_obj(data, ('channelId', {str}))
        channel = traverse_obj(data, ('channel', {str}))
        channel_url = urljoin(
            'https://preservetube.com/', f'channel/{channel_id}') if channel_id else None
        media_file = traverse_obj(data, ('file', {dict})) or {}

        return {
            'id': video_id,
            'url': media_url,
            'ext': determine_ext(media_url, 'mp4'),
            'title': traverse_obj(data, ('title', {str})),
            'description': clean_html(traverse_obj(data, ('description', {str}))) or None,
            'thumbnail': traverse_obj(data, ('thumbnail', {url_or_none})),
            'upload_date': unified_strdate(traverse_obj(data, ('published', {str}))),
            'channel': channel,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'uploader': channel,
            'uploader_id': channel_id,
            'uploader_url': channel_url,
            'duration': float_or_none(media_file.get('duration_seconds')),
            'filesize': int_or_none(media_file.get('size_bytes')),
            'fps': int_or_none(media_file.get('fps')),
            'vcodec': traverse_obj(media_file, ('video_codec', {str})),
            'acodec': traverse_obj(media_file, ('audio_codec', {str})),
            **parse_resolution(traverse_obj(media_file, ('resolution', {str}))),
        }

    def _extract_from_html(self, video_id):
        url = f'https://preservetube.com/watch?v={video_id}'
        webpage = self._download_webpage(url, video_id)
        if 'Archive not found' in webpage:
            raise ExtractorError('Archive not found', expected=True)
        if 'moved to cold storage' in webpage or 'has been removed' in webpage:
            self.raise_no_formats(
                'This video is not currently downloadable from PreserveTube',
                expected=True, video_id=video_id)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        if not entries or not (entries[0].get('formats') or entries[0].get('url')):
            self.raise_no_formats('No video source found', expected=True, video_id=video_id)
        info = entries[0]

        channel_id = self._search_regex(
            r'href="/channel/([^"/?#]+)"', webpage, 'channel id', default=None)
        channel = self._html_search_regex(
            r'class="channel-name"[^>]*>\s*<a[^>]*>([^<]+)', webpage, 'channel', default=None)
        channel_url = urljoin(url, f'/channel/{channel_id}') if channel_id else None
        title = (
            self._html_search_regex(r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', default=None)
            or remove_end(self._og_search_title(webpage, default=''), ' | PreserveTube')
            or None)

        info.update({
            'id': video_id,
            'title': title,
            'description': clean_html(
                self._html_search_regex(
                    r'<p class="description">(.+?)</p>', webpage, 'description', default=None)
                or self._og_search_description(webpage, default=None)),
            'upload_date': unified_strdate(self._search_regex(
                r'Published on (\d{4}-\d{2}-\d{2})', webpage, 'upload date', default=None)),
            'channel': channel,
            'channel_id': channel_id,
            'channel_url': channel_url,
            'uploader': channel,
            'uploader_id': channel_id,
            'uploader_url': channel_url,
        })
        return info


class PreserveTubeChannelIE(InfoExtractor):
    IE_NAME = 'preservetube:channel'
    _VALID_URL = r'https?://(?:www\.)?preservetube\.com/channel/(?P<id>[^/?#]+)(?:/videos)?'
    _TESTS = [{
        'url': 'https://preservetube.com/channel/UCtXP-QNYkq4RvAAAHfRU_9g',
        'info_dict': {
            'id': 'UCtXP-QNYkq4RvAAAHfRU_9g',
            'title': 'UCtXP-QNYkq4RvAAAHfRU_9g videos',
        },
        'playlist_mincount': 2,
        'params': {'skip_download': True},
    }, {
        'url': 'https://preservetube.com/channel/UCwHwDuNd9lCdA7chyyquDXw/videos',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        # /channel/<id> is Cloudflare-challenged; the archived listing is public.
        webpage = self._download_webpage(
            f'https://preservetube.com/channel/{channel_id}/videos', channel_id)
        title = remove_end(
            self._html_extract_title(webpage, default=''), ' | PreserveTube') or None
        video_ids = orderedSet(re.findall(r'href="/watch\?v=([^"&]+)"', webpage))
        return self.playlist_result(
            (self.url_result(
                f'https://preservetube.com/watch?v={vid}', PreserveTubeIE, vid)
             for vid in video_ids),
            channel_id, title)
