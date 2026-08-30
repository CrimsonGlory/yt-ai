import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    remove_start,
    unified_strdate,
    urlencode_postdata,
    urljoin,
)


class FreeSexIE(InfoExtractor):
    IE_NAME = 'freesex'
    IE_DESC = 'freesex.cz'
    _VALID_URL = r'https?://(?:www\.)?freesex\.cz/content/(?P<id>\d+)-(?P<display_id>[^/?#]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://freesex.cz/content/18125-divoke-brunetky-v-rozkosi',
        'md5': 'ce7717007571f3ac2b1aee497d63d9e9',
        'info_dict': {
            'id': '18125',
            'ext': 'mp4',
            'display_id': 'divoke-brunetky-v-rozkosi',
            'title': 'Divoké brunetky v rozkoši',
            'description': 'md5:744d078b26fc09c42937d44a00beecca',
            'thumbnail': r're:https?://freesex\.cz/freesex/video/.+\.jpg',
            'uploader': 'nugget123',
            'uploader_id': '7',
            'uploader_url': 'https://freesex.cz/users/7',
            'upload_date': '20260212',
            'view_count': int,
            'age_limit': 18,
            'categories': ['Video', 'Brunety'],
            'tags': ['brunetky', 'fisting', 'lízání kundičky', 'prstění kundičky', 'Anina Silk', 'tvrdé bradavky', 'pulsující kundičky'],
        },
    }, {
        'url': 'https://www.freesex.cz/content/18604-kdyz-curak-klouze-mezi-naolejovanymi-prsy',
        'only_matching': True,
    }, {
        'url': 'https://freesex.cz/content/17196-lesbicky-krev-a-mliko',
        'only_matching': True,
    }]

    def _accept_terms(self, webpage, video_id, video_url):
        self.report_age_confirmation()
        form = self._search_regex(
            r'(?s)<form[^>]+class=["\']form-terms-accept["\'][^>]*>(.*?)</form>',
            webpage, 'terms form')
        data = self._hidden_inputs(form)
        data['accept_terms_form[accept_check]'] = 'true'
        self._download_webpage(
            urljoin(video_url, '/terms/accept'), video_id,
            'Submitting age confirmation', data=urlencode_postdata(data),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': urljoin(video_url, '/terms/accept'),
            })
        return self._download_webpage(video_url, video_id)

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage, urlh = self._download_webpage_handle(url, video_id)
        if '/terms/accept' in urlh.url or 'form-terms-accept' in webpage:
            webpage = self._accept_terms(webpage, video_id, url)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        if not entries or not entries[0].get('formats'):
            raise ExtractorError('No video source found', expected=True)
        info = entries[0]
        for f in info['formats']:
            f.setdefault('http_headers', {'Referer': url})

        uploader_id, uploader = self._html_search_regex(
            r'<span[^>]+class=["\']name["\'][^>]*>\s*<a[^>]+href=["\']/users/(?P<id>\d+)["\'][^>]*>(?P<name>[^<]+)',
            webpage, 'uploader', default=(None, None), group=('id', 'name'))
        category = self._html_search_regex(
            r'<div[^>]+class=["\']category["\'][^>]*>[\s\S]*?<span>([^<]+)</span>',
            webpage, 'category', default=None)
        title = (
            self._html_search_regex(
                r'<h1[^>]+class=["\']content-name["\'][^>]*>([^<]+)',
                webpage, 'title', default=None)
            or self._og_search_title(webpage, default=None)
            or remove_start(self._html_extract_title(webpage, default=''), 'FreeSex.cz - ')
            or None)

        info.update({
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': (
                self._html_search_regex(
                    r'<div[^>]+class=["\']description["\'][^>]*>([^<]+)',
                    webpage, 'description', default=None)
                or self._og_search_description(webpage, default=None)),
            'thumbnail': info.get('thumbnail') or self._og_search_thumbnail(webpage),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'uploader_url': urljoin(url, f'/users/{uploader_id}') if uploader_id else None,
            'upload_date': unified_strdate(self._html_search_regex(
                r'<div[^>]+class=["\']date["\'][^>]*>[\s\S]*?<span>([^<]+)</span>',
                webpage, 'upload date', default=None)),
            'view_count': int_or_none(self._search_regex(
                r'class=["\']num["\'][^>]*>\s*(\d+)\s*x', webpage, 'view count', default=None)),
            'age_limit': 18,
            'categories': [c.strip() for c in (category or '').split('/') if c.strip()] or None,
            'tags': re.findall(
                r'<span[^>]+class=["\']tag["\'][^>]*>\s*<a[^>]+>([^<]+)', webpage) or None,
            'http_headers': {'Referer': url},
        })
        return info
