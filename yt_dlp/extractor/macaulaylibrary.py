import hashlib
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    traverse_obj,
    unified_strdate,
    urljoin,
)


class MacaulayLibraryIE(InfoExtractor):
    IE_DESC = 'Macaulay Library'
    _VALID_URL = r'https?://(?:www\.)?macaulaylibrary\.org/(?:[a-z]{2}(?:-[A-Z]{2})?/)?asset/(?P<id>\d+)'
    _CDN_BASE = 'https://cdn.download.ams.birds.cornell.edu/api/v2/asset/'
    _TESTS = [{
        'url': 'https://macaulaylibrary.org/asset/477823',
        'md5': '78f3c55b17c6e27bc965541b2e5268fb',
        'info_dict': {
            'id': '477823',
            'ext': 'mp4',
            'title': 'ML477823 - Bumblebee Hummingbird - Macaulay Library',
            'alt_title': 'Selasphorus heloisa',
            'description': 'Macaulay Library ML477823; © Luke Seitz; Oaxaca, Mexico',
            'thumbnail': r're:https?://cdn\.download\.ams\.birds\.cornell\.edu/api/v2/asset/477823/',
            'uploader': 'Luke Seitz',
            'uploader_id': 'USER90474',
            'location': 'Small track at Km. 139 Route 175, Oaxaca, Mexico',
            'timestamp': 1469022950,
            'upload_date': '20160720',
            'release_date': '20130110',
            'tags': ['archive', 'flying_flight', 'song', 'vocalizing'],
            'height': 1280,
        },
    }, {
        'url': 'https://macaulaylibrary.org/asset/100872',
        'md5': '56f1065bdb9d8c5c0499d635ebd51ec0',
        'info_dict': {
            'id': '100872',
            'ext': 'mp3',
            'title': 'ML100872 - Winter Wren - Macaulay Library',
            'alt_title': 'Nannus hiemalis',
            'description': 'Macaulay Library ML100872; © Wil Hershberger; Hamilton, New York, United States',
            'thumbnail': r're:https?://cdn\.download\.ams\.birds\.cornell\.edu/api/v2/asset/100872/',
            'uploader': 'Wil Hershberger',
            'uploader_id': 'USER187124',
            'location': "Ferd's Bog, New York, United States",
            'timestamp': 1469023594,
            'upload_date': '20160720',
            'release_date': '19990530',
            'tags': ['archive', 'no_playback', 'song'],
            'vcodec': 'none',
        },
    }, {
        'url': 'https://macaulaylibrary.org/zh-CN/asset/477823',
        'only_matching': True,
    }, {
        'url': 'https://www.macaulaylibrary.org/asset/193964791',
        'only_matching': True,
    }]

    def _solve_anubis_pow(self, random_data, difficulty):
        prefix = '0' * (int_or_none(difficulty) or 0)
        for nonce in range(5_000_000):
            digest = hashlib.sha256(f'{random_data}{nonce}'.encode()).hexdigest()
            if digest.startswith(prefix):
                return nonce, digest
        raise ExtractorError('Unable to solve Anubis proof-of-work challenge', expected=True)

    def _download_macaulay_webpage(self, url, asset_id):
        webpage = self._download_webpage(url, asset_id)
        challenge = traverse_obj(self._search_json(
            r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
            webpage, 'anubis challenge', asset_id, default=None), 'challenge')
        if not challenge:
            return webpage

        random_data = challenge.get('randomData')
        challenge_id = challenge.get('id')
        method = challenge.get('method') or 'fast'
        if method != 'fast':
            raise ExtractorError(
                f'Unsupported Anubis challenge method {method!r}', expected=True)
        if not random_data or not challenge_id:
            raise ExtractorError('Unable to parse Anubis challenge', expected=True)

        nonce, response = self._solve_anubis_pow(
            random_data, challenge.get('difficulty'))
        webpage = self._download_webpage(
            urljoin(url, '/.within.website/x/cmd/anubis/api/pass-challenge'),
            asset_id, 'Solving Anubis challenge', query={
                'id': challenge_id,
                'response': response,
                'nonce': str(nonce),
                'redir': url,
                'elapsedTime': '1',
            })
        if self._search_json(
                r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
                webpage, 'anubis challenge', asset_id, default=None):
            raise ExtractorError('Anubis challenge was not accepted', expected=True)
        if 'id="__NUXT_DATA__"' not in webpage and 'window.__NUXT__' not in webpage:
            webpage = self._download_webpage(
                url, asset_id, 'Downloading webpage after Anubis')
        return webpage

    def _search_asset_str(self, webpage, field, pattern=r'[^"]+'):
        return self._search_regex(
            rf'\b{re.escape(field)}:"({pattern})"', webpage, field, default=None)

    def _real_extract(self, url):
        asset_id = self._match_id(url)
        webpage = self._download_macaulay_webpage(url, asset_id)

        asset = traverse_obj(
            self._search_nuxt_json(webpage, asset_id, fatal=False),
            ('data', f'specimen-{asset_id}', 'asset', {dict})) or {}
        taxonomy = traverse_obj(asset, ('taxonomy', {dict})) or {}
        location = traverse_obj(asset, ('location', {dict})) or {}

        media_type = asset.get('mediaType') or self._search_regex(
            r'\bmediaType:"([avp])"', webpage, 'media type', default=None)
        mime_type = asset.get('mimeType') or ''
        if media_type == 'p' or mime_type.startswith('image/'):
            self.raise_no_formats('This Macaulay Library asset is a photo', expected=True)

        is_video = media_type == 'v' or mime_type.startswith('video/')
        formats = []
        thumbnail = (
            f'{self._CDN_BASE}{asset_id}/1200'
            if is_video else self._og_search_thumbnail(webpage, default=None))
        video_attrs = extract_attributes(self._search_regex(
            r'(<video[^>]+>)', webpage, 'video tag', default='') or '')
        video_url = video_attrs.get('src')
        if not video_url and is_video:
            height = int_or_none(asset.get('height')) or 1280
            video_url = f'{self._CDN_BASE}{asset_id}/mp4/{height}'
        if video_url:
            height = int_or_none(self._search_regex(
                r'/mp4/(\d+)', video_url, 'height', default=None))
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': join_nonempty('mp4', height),
                'height': height,
            })
            thumbnail = video_attrs.get('poster') or thumbnail
        elif not is_video:
            formats.append({
                'url': f'{self._CDN_BASE}{asset_id}/mp3',
                'ext': 'mp3',
                'format_id': 'mp3',
                'vcodec': 'none',
            })

        if not formats:
            self.raise_no_formats('No video or audio URL found', expected=True)

        tags = asset.get('tags') or re.findall(
            r'"([^"]+)"',
            self._search_regex(r'\btags:\[([^\]]*)\]', webpage, 'tags', default='') or '')

        return {
            'id': asset_id,
            'title': self._og_search_title(webpage),
            'alt_title': taxonomy.get('sciName') or self._search_asset_str(webpage, 'sciName'),
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': thumbnail,
            'uploader': asset.get('userDisplayName') or self._search_asset_str(webpage, 'userDisplayName'),
            'uploader_id': asset.get('userId') or self._search_asset_str(webpage, 'userId', r'USER\d+'),
            'location': join_nonempty(
                location.get('locality') or self._search_asset_str(webpage, 'locality'),
                location.get('subnational1Name') or self._search_asset_str(webpage, 'subnational1Name'),
                location.get('countryName') or self._search_asset_str(webpage, 'countryName'),
                delim=', ') or None,
            'timestamp': parse_iso8601(asset.get('createDt') or self._search_regex(
                r'assetState:[^,]*,mediaType:"[avp]".*?createDt:"([^"]+)"',
                webpage, 'upload date', default=None, flags=re.S)),
            'release_date': unified_strdate(
                asset.get('obsDt') or self._search_asset_str(webpage, 'obsDt', r'\d{4}-\d{2}-\d{2}[^"]*')),
            'tags': tags or None,
            'formats': formats,
        }
