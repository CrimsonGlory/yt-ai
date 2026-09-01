import hashlib
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    int_or_none,
    mimetype2ext,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class MemobaseIE(InfoExtractor):
    IE_NAME = 'memobase'
    IE_DESC = 'MEMOBASE von Memoriav'
    _VALID_URL = r'https?://(?:www\.)?memobase\.ch/(?:(?:de|fr|it)/)?object/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://memobase.ch/de/object/zem-001-F_20_d_f_i_Expo',
        'md5': '2860eefe7d6be2235d5fb58d1024bc1e',
        'info_dict': {
            'id': 'zem-001-F_20_d_f_i_Expo',
            'ext': 'm4v',
            'title': 'Wehrhafte Schweiz / La Suisse vigilante / La Svizzera vigilante',
            'description': 'md5:81af5ca93f6efc480dbf17011203c0c1',
            'thumbnail': r're:https://media\.memobase\.ch/memo/.+',
            'release_year': 1964,
            'uploader': 'Zentrum elektronische Medien',
            'tags': ['Landesausstellung 1964', 'Kalter Krieg', 'Historische Ereignisse'],
        },
    }, {
        'url': 'https://memobase.ch/object/zem-001-F_20_d_f_i_Expo',
        'only_matching': True,
    }, {
        'url': 'https://memobase.ch/fr/object/zem-001-F_20_d_f_i_Expo',
        'only_matching': True,
    }, {
        'url': 'https://memobase.ch/it/object/lfg-001-DoitYourself',
        'only_matching': True,
    }, {
        'url': 'https://memobase.ch/de/object/srf-999-d433b979-6b40-44b0-90a6-4319683c2bed_01',
        'only_matching': True,
    }]
    _SRG_EMBED_RE = r'''(?x)
        https?://(?:www\.)?(?P<bu>srf|rts|rsi|rtr|swissinfo)\.ch/play/embed\?
        urn=urn:(?P<urn_bu>srf|rts|rsi|rtr|swi):(?P<kind>video|audio):(?P<srg_id>[\da-f-]+)
    '''
    # Anubis challenges User-Agents that contain "Mozilla"; other UAs reach Drupal.
    _PAGE_HEADERS = {'User-Agent': 'yt-dlp'}

    def _solve_anubis_pow(self, random_data, difficulty):
        prefix = '0' * (int_or_none(difficulty) or 0)
        for nonce in range(5_000_000):
            digest = hashlib.sha256(f'{random_data}{nonce}'.encode()).hexdigest()
            if digest.startswith(prefix):
                return nonce, digest
        raise ExtractorError('Unable to solve Anubis proof-of-work challenge', expected=True)

    def _download_memobase_webpage(self, url, video_id):
        webpage = self._download_webpage(
            url, video_id, headers=self._PAGE_HEADERS)
        challenge = traverse_obj(self._search_json(
            r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
            webpage, 'anubis challenge', video_id, default=None), 'challenge')
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
            video_id, 'Solving Anubis challenge', query={
                'id': challenge_id,
                'response': response,
                'nonce': str(nonce),
                'redir': url,
                'elapsedTime': '1',
            })
        if self._search_json(
                r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
                webpage, 'anubis challenge', video_id, default=None):
            raise ExtractorError('Anubis challenge was not accepted', expected=True)
        if 'mediaIframe' not in webpage and 'application/ld+json' not in webpage:
            webpage = self._download_webpage(
                url, video_id, 'Downloading webpage after Anubis',
                headers=self._PAGE_HEADERS)
        return webpage

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_memobase_webpage(url, video_id)
        ld = next(self._yield_json_ld(webpage, video_id, fatal=False), {})

        viewer_src = (
            url_or_none(ld.get('embedUrl'))
            or self._search_regex(
                r'<iframe[^>]+id=["\']mediaIframe["\'][^>]*\bsrc=["\']([^"\']+)',
                webpage, 'media viewer', default=None))
        if not viewer_src:
            raise ExtractorError(
                'No publicly playable media found', expected=True)
        viewer_url = urljoin(url, viewer_src)
        viewer = self._download_webpage(
            viewer_url, video_id, note='Downloading media viewer')

        srg = re.search(self._SRG_EMBED_RE, viewer)
        if srg:
            bu = 'swi' if srg.group('bu') == 'swissinfo' else srg.group('urn_bu')
            return self.url_result(
                f'srgssr:{bu}:{srg.group("kind")}:{srg.group("srg_id")}',
                ie='SRGSSR', video_id=srg.group('srg_id'))

        formats = []
        for tag in re.findall(r'<source[^>]+>', viewer, flags=re.DOTALL):
            attrs = extract_attributes(tag)
            src = url_or_none(re.sub(r'\s+', '', attrs.get('src') or ''))
            if not src:
                continue
            mime = (attrs.get('type') or '').split(';')[0].strip().lower()
            ext = mimetype2ext(mime)
            fmt = {'url': src, 'ext': ext}
            if mime.startswith('audio/') or ext in ('mp3', 'm4a', 'ogg', 'wav', 'flac'):
                fmt['vcodec'] = 'none'
            formats.append(fmt)

        if not formats:
            if 'openseadragon' in viewer.lower() or '/iiif/' in viewer:
                raise ExtractorError(
                    'This Memobase object is an image, not a video', expected=True)
            raise ExtractorError('No media sources found', expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        json_ld.pop('url', None)
        json_ld.pop('ext', None)

        keywords = ld.get('keywords')
        if isinstance(keywords, str):
            keywords = [keywords]
        tags = []
        for item in keywords or []:
            if isinstance(item, str):
                tags.extend(t.strip() for t in item.split(',') if t.strip())

        release_year = None
        for key in ('dateCreated', 'datePublished', 'uploadDate'):
            mobj = re.search(r'(?:18|19|20)\d{2}', str(ld.get(key) or ''))
            if mobj:
                release_year = int_or_none(mobj.group(0))
                break

        thumbnail = url_or_none(self._search_regex(
            r'<(?:video|audio)[^>]+poster=(["\'])(?P<url>(?:(?!\1).)+)\1',
            viewer, 'poster', default=None, group='url'))

        return {
            **json_ld,
            'id': video_id,
            'title': (json_ld.get('title')
                      or self._html_search_regex(
                          r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)
                      or self._og_search_title(webpage)),
            'description': json_ld.get('description') or self._og_search_description(webpage),
            'thumbnail': thumbnail or json_ld.get('thumbnail'),
            'tags': tags or None,
            'release_year': release_year,
            'uploader': traverse_obj(ld, (
                ('copyrightHolder', 'publisher', 'creator'), (None, 0), 'name', {str}),
                get_all=False),
            'formats': formats,
        }
