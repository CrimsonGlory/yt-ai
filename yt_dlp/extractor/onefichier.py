import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    parse_filesize,
    unescapeHTML,
    url_or_none,
    urlencode_postdata,
)


class OneFichierIE(InfoExtractor):
    IE_NAME = '1fichier'
    IE_DESC = '1fichier'
    _VALID_URL = (
        r'https?://(?:www\.)?(?:'
        r'1fichier\.com/\?(?P<id>[0-9a-z]{5,20})'
        r'|(?P<host_id>[0-9a-z]{5,20})\.1fichier\.com)')
    _TESTS = [{
        'url': 'https://1fichier.com/?6prhypfv84nx1nf1yrsi',
        'md5': '88d5b3896460448b0a3edd33ad45f080',
        'info_dict': {
            'id': '6prhypfv84nx1nf1yrsi',
            'ext': 'mp4',
            'title': 'ytai-1fichier-sample',
            'filesize': int,
        },
    }, {
        'url': 'https://www.1fichier.com/?6prhypfv84nx1nf1yrsi',
        'only_matching': True,
    }, {
        'url': 'https://6prhypfv84nx1nf1yrsi.1fichier.com/',
        'only_matching': True,
    }, {
        'url': 'https://1fichier.com/?6prhypfv84nx1nf1yrsi&inline',
        'only_matching': True,
    }]
    _MAX_WAIT = 90

    def _real_id(self, url):
        groups = self._match_valid_url(url).groupdict()
        return groups.get('id') or groups['host_id']

    def _parse_wait_seconds(self, webpage):
        mobj = re.search(r'var\s+ct\s*=\s*(\d+)\s*(?:\*\s*(\d+))?', webpage)
        if not mobj:
            return 0
        wait = int(mobj.group(1))
        if mobj.group(2):
            wait *= int(mobj.group(2))
        return wait

    def _extract_download_url(self, webpage):
        return url_or_none(unescapeHTML(self._search_regex(
            (r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*>\s*Start your download',
             r'href=["\'](https?://[a-z0-9-]+\.1fichier\.com/c\d+)["\']'),
            webpage, 'download URL', default=None)))

    def _raise_if_unavailable(self, webpage, video_id):
        lower = webpage.lower()
        if 'cf-turnstile' in lower or 'challenges.cloudflare.com/turnstile' in lower:
            raise ExtractorError(
                '1fichier is blocking this request with Cloudflare Turnstile',
                expected=True, video_id=video_id)
        if 'fichier introuvable' in lower or 'file not found' in lower:
            raise ExtractorError('File not found', expected=True, video_id=video_id)
        if 'professional equipment detected' in lower:
            self.raise_login_required(
                '1fichier blocked this IP as professional equipment; premium or CDN credits are required')
        if 'all free guest slots are currently in use' in lower:
            self.raise_login_required(
                'Free guest download slots are full; a free or premium 1fichier account is required')
        if re.search(r'<input[^>]+type=["\']password["\']', webpage) and not self.get_param('videopassword'):
            raise ExtractorError(
                'This file is password protected, use --video-password',
                expected=True, video_id=video_id)

    def _download_file_page(self, url, video_id, note, data=None):
        return self._download_webpage(
            url, video_id, note, data=data, headers={
                'Referer': url,
                **({'Content-Type': 'application/x-www-form-urlencoded'} if data is not None else {}),
            }, expected_status=404)

    def _real_extract(self, url):
        video_id = self._real_id(url)
        url = f'https://1fichier.com/?{video_id}'
        webpage = self._download_file_page(url, video_id, 'Downloading file page')
        self._raise_if_unavailable(webpage, video_id)

        filename = self._html_search_regex(
            r'class="tier-name">([^<]+)', webpage, 'filename', default=None) or video_id
        filesize = parse_filesize(self._search_regex(
            r'class="tier-feat">([^<]+)', webpage, 'filesize', default=None))
        title = filename.rsplit('.', 1)[0] if '.' in filename[1:] else filename

        download_url = self._extract_download_url(webpage)
        if not download_url:
            wait = self._parse_wait_seconds(webpage)
            if wait > self._MAX_WAIT:
                raise ExtractorError(
                    f'1fichier requires waiting {wait} seconds between free downloads',
                    expected=True, video_id=video_id)
            if wait:
                self._sleep(wait, video_id)

            post_data = {}
            password = self.get_param('videopassword')
            if password:
                post_data['pass'] = password
            webpage = self._download_file_page(
                url, video_id, 'Submitting download form',
                data=urlencode_postdata(post_data))
            self._raise_if_unavailable(webpage, video_id)
            download_url = self._extract_download_url(webpage)

        if not download_url:
            raise ExtractorError('Unable to extract download URL', video_id=video_id)

        return {
            'id': video_id,
            'url': download_url,
            'title': title,
            'ext': determine_ext(filename, default_ext='mp4'),
            'filesize': filesize,
            'http_headers': {'Referer': url},
        }
