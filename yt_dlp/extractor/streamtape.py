import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_filesize,
    remove_end,
    update_url_query,
    url_or_none,
)


class StreamtapeIE(InfoExtractor):
    IE_NAME = 'streamtape'
    IE_DESC = 'Streamtape'
    _DOMAINS = r'streamtape\.(?:com|net|to|xyz|cc|site)'
    _VALID_URL = rf'https?://(?:www\.)?(?:{_DOMAINS})/(?:e|v)/(?P<id>[0-9A-Za-z]+)(?:/[^?#]*)?'
    _TESTS = [{
        'url': 'https://streamtape.com/v/oAyl8rV67auW39',
        'md5': '8e6b2305f9b1900b4b6f3d3c343d0caf',
        'info_dict': {
            'id': 'oAyl8rV67auW39',
            'ext': 'mp4',
            'title': 'Jellyfish_1080_10s_5MB.mp4',
            'description': 'Jellyfish_1080_10s_5MB.mp4 at Streamtape.com',
            'thumbnail': r're:https?://thumb\.tapecontent\.net/thumb/.+',
            'filesize_approx': int,
        },
    }, {
        'url': 'https://streamtape.com/e/oAyl8rV67auW39',
        'only_matching': True,
    }, {
        'url': 'https://streamtape.com/e/oAyl8rV67auW39/',
        'only_matching': True,
    }, {
        'url': 'https://streamtape.com/v/oAyl8rV67auW39/Jellyfish_1080_10s_5MB.mp4',
        'only_matching': True,
    }, {
        'url': 'https://streamtape.net/v/oAyl8rV67auW39',
        'only_matching': True,
    }, {
        'url': 'https://streamtape.to/v/oAyl8rV67auW39',
        'only_matching': True,
    }, {
        'url': 'https://streamtape.com/e/bZ8oePdQPPtdyw',
        'only_matching': True,
    }]

    _PLAYER_LINK_IDS = ('captchalink', 'botlink', 'norobotlink', 'robotlink')

    @staticmethod
    def _eval_js_string_expr(expr):
        """Evaluate JS made of string literals, +, parentheses, and .substring(n)."""
        if not expr:
            return None
        tokens, i, n = [], 0, len(expr)
        while i < n:
            c = expr[i]
            if c.isspace():
                i += 1
                continue
            if c in '\'"':
                q, i, buf = c, i + 1, []
                while i < n and expr[i] != q:
                    if expr[i] == '\\' and i + 1 < n:
                        buf.append(expr[i + 1])
                        i += 2
                        continue
                    buf.append(expr[i])
                    i += 1
                i += 1
                tokens.append(('str', ''.join(buf)))
                continue
            if c in '+()':
                tokens.append((c,))
                i += 1
                continue
            m = re.match(r'\.\s*substring\s*\(\s*(\d+)\s*\)', expr[i:])
            if m:
                tokens.append(('sub', int(m.group(1))))
                i += m.end()
                continue
            i += 1

        def parse_value(pos):
            if pos >= len(tokens):
                return '', pos
            tok = tokens[pos]
            if tok[0] == '(':
                val, pos = parse_expr(pos + 1)
                if pos < len(tokens) and tokens[pos][0] == ')':
                    pos += 1
            elif tok[0] == 'str':
                val, pos = tok[1], pos + 1
            else:
                return '', pos
            while pos < len(tokens) and tokens[pos][0] == 'sub':
                val = val[tokens[pos][1]:]
                pos += 1
            return val, pos

        def parse_expr(pos):
            val, pos = parse_value(pos)
            while pos < len(tokens) and tokens[pos][0] == '+':
                rhs, pos = parse_value(pos + 1)
                val += rhs
            return val, pos

        return parse_expr(0)[0] or None

    def _is_get_video_path(self, path):
        return bool(path and re.search(
            rf'(?:{self._DOMAINS})/get_video\?', path))

    def _absolute_media_url(self, path):
        path = (path or '').strip()
        if path.startswith('//'):
            return f'https:{path}'
        if re.match(rf'/{self._DOMAINS}/get_video\?', path):
            return f'https:/{path}'
        return url_or_none(path)

    def _extract_media_path(self, webpage):
        for link_id in self._PLAYER_LINK_IDS:
            expr = self._search_regex(
                rf'''document\.getElementById\(['"]{link_id}['"]\)\.innerHTML\s*=\s*(.+?);''',
                webpage, f'{link_id} expression', default=None)
            path = self._eval_js_string_expr(expr)
            if self._is_get_video_path(path):
                return path

        token = self._search_regex(
            r'''getElementById\(['"](?:captcha|bot|no)?robotlink['"]\)\.innerHTML\s*=[^;]*[?&]token=([^&'"\\]+)''',
            webpage, 'token', default=None)
        hidden = self._html_search_regex(
            r'<(?:div|span)[^>]+id=["\'](?:ideooo?link|(?:no)?robotlink|captchalink|botlink)["\'][^>]*>([^<]+)',
            webpage, 'hidden get_video path', default=None)
        if token and hidden and 'get_video' in hidden:
            return re.sub(r'(?<=[?&])token=[^&]*', f'token={token}', hidden)
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        path = self._extract_media_path(webpage)
        video_url = self._absolute_media_url(path)
        if not video_url:
            raise ExtractorError('Unable to extract video URL', expected=True)
        video_url = update_url_query(video_url, {'stream': '1'})

        vidconfig = self._search_json(
            r'var\s+vidconfig\s*=', webpage, 'vidconfig', video_id, fatal=False) or {}
        title = (
            vidconfig.get('showtitle')
            or self._og_search_title(webpage)
            or remove_end(self._html_extract_title(webpage, default=''), ' at Streamtape.com')
            or None)

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage) or self._html_search_regex(
                r'<video[^>]+poster=(["\'])(?P<url>[^"\']+)\1',
                webpage, 'thumbnail', default=None, group='url'),
            'url': video_url,
            'ext': 'mp4',
            'filesize_approx': parse_filesize(self._html_search_regex(
                r'<p[^>]+class=["\']subheading["\'][^>]*>([^<]+)',
                webpage, 'filesize', default=None)),
            'http_headers': {'Referer': url},
        }
