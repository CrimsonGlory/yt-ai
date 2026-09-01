from .rezka import RezkaIE
from ..utils import (
    NO_DEFAULT,
    ExtractorError,
    traverse_obj,
    urljoin,
)


class HDRezkaIE(RezkaIE):
    IE_NAME = 'hdrezka'
    IE_DESC = 'HDrezka (hdrezka.ag)'
    _VALID_URL = r'https?://(?:www\.)?(?:hdrezka\.ag|hdrezka-home\.tv)/(?:films|series|cartoons|animation)/[^/?#]+/(?P<id>\d+)(?:-[^/?#]+)?(?:/(?P<translator>[^/?#]+))?'
    _TESTS = [{
        'url': 'https://hdrezka.ag/series/thriller/646-vo-vse-tyazhkie-2008.html#t:56-s:1-e:1',
        'md5': '10849cbbe98dfc11ec6d02caa7d84820',
        'info_dict': {
            'id': '646_s1e1',
            'ext': 'mp4',
            'title': 'Во все тяжкие (2008)',
            'alt_title': 'Breaking Bad',
            'description': 'md5:0e107044b7f5962173fb7c5a421ef7be',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png)',
            'duration': 2820,
            'season': 'Season 1',
            'season_number': 1,
            'episode': 'Episode 1',
            'episode_number': 1,
        },
        'params': {
            'format': 'best[protocol=https]',
        },
    }, {
        'url': 'https://hdrezka.ag/films/drama/92189-istoriya-lyubvi-v-chennai-2026.html',
        'only_matching': True,
    }, {
        'url': 'https://hdrezka-home.tv/series/thriller/646-vo-vse-tyazhkie-2008.html',
        'only_matching': True,
    }]

    def _configuration_arg(self, key, default=NO_DEFAULT, **kwargs):
        val = super()._configuration_arg(key, default=None, **kwargs)
        if val:
            return val
        frag_val = (getattr(self, '_fragment_args', None) or {}).get(key)
        if frag_val is not None:
            return [frag_val]
        return [] if default is NO_DEFAULT else default

    def _download_rezka_webpage(self, url, video_id):
        urlh = self._request_webpage(url, video_id)
        page_url = urlh.url
        webpage = self._webpage_read_content(urlh, url, video_id)
        self._canonical_url = page_url.split('#', 1)[0]

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
        # pass-challenge with the video URL as redir 500s on hdrezka-home.tv;
        # solve against the origin root, then reload the title page.
        origin = urljoin(page_url, '/')
        webpage = self._download_webpage(
            urljoin(origin, '/.within.website/x/cmd/anubis/api/pass-challenge'),
            video_id, 'Solving Anubis challenge', query={
                'id': challenge_id,
                'response': response,
                'nonce': str(nonce),
                'redir': origin,
                'elapsedTime': '1',
            })
        if self._search_json(
                r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
                webpage, 'anubis challenge', video_id, default=None):
            raise ExtractorError('Anubis challenge was not accepted', expected=True)
        if 'initCDN' not in webpage:
            webpage = self._download_webpage(
                self._canonical_url, video_id, 'Downloading webpage after Anubis')
        return webpage

    def _call_cdn(self, url, video_id, form, note='Downloading stream JSON'):
        return super()._call_cdn(
            getattr(self, '_canonical_url', url), video_id, form, note)

    def _real_extract(self, url):
        fragment = url.split('#', 1)[-1] if '#' in url else ''
        self._fragment_args = {
            'translator': self._search_regex(
                r'(?:^|[-_])t:(\d+)', fragment, 'translator', default=None),
            'season': self._search_regex(
                r'(?:^|[-_])s:(\d+)', fragment, 'season', default=None),
            'episode': self._search_regex(
                r'(?:^|[-_])e:(\d+)', fragment, 'episode', default=None),
        }
        return super()._real_extract(url)
