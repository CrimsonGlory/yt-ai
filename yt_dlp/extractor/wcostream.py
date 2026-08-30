import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    orderedSet,
    parse_qs,
    unescapeHTML,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class WCOStreamBaseIE(InfoExtractor):
    _EMBED_HOST = 'https://embed.wcostream.com'
    # www embeds live under the historical cizgi/ path; other embed= values are the CDN directory.
    _EMBED_DIRS = {
        'www': 'cizgi',
    }
    _QUALITIES = (
        ('enc', 'sd', 480),
        ('hd', 'hd', 720),
        ('fhd', 'fhd', 1080),
    )
    # getvid tokens are bound to the TLS fingerprint used for getvidlink.php.
    _MEDIA_IMPERSONATE = True

    def _page_title(self, webpage):
        title = (
            self._html_search_regex(
                r'itemprop="name"\s+content="([^"]+)"', webpage, 'title', default=None)
            or self._html_search_regex(
                r'class="film-name[^"]*"[^>]*>([^<]+)', webpage, 'title', default=None)
            or self._html_extract_title(webpage, default=None))
        if title:
            title = re.split(r'\s+\|\s+Watch cartoons online', title, maxsplit=1)[0].strip()
        return title or None

    def _extract_embed_urls(self, webpage):
        embeds = []
        for mobj in re.finditer(r'<iframe\b[^>]+>', webpage, re.I):
            src = url_or_none(unescapeHTML(extract_attributes(mobj.group(0)).get('src') or ''))
            if src and 'embed.wcostream.com/inc/embed/' in src:
                embeds.append(src)
        if embeds:
            return orderedSet(embeds)

        # itemprop fallback when the iframe src is omitted
        for file_path in re.findall(
                r'itemprop="embedURL"\s+content="[^"]*?[?&]file=([^"&]+)', webpage):
            file_path = unescapeHTML(file_path)
            embeds.append(
                f'{self._EMBED_HOST}/inc/embed/index.php?file={file_path}&embed=www')
        return orderedSet(embeds)

    def _extract_from_embed(self, embed_url, video_id):
        qs = parse_qs(embed_url)
        file_path = traverse_obj(qs, ('file', 0, {str}))
        if not file_path:
            raise ExtractorError('Missing embed file path', expected=True)

        embed = traverse_obj(qs, ('embed', 0, {str})) or 'www'
        directory = self._EMBED_DIRS.get(embed, embed)
        stem = file_path.rsplit('.', 1)[0]
        query = {
            'v': f'{directory}/{stem}.mp4',
            'embed': embed,
        }
        for key in ('hd', 'fullhd'):
            value = traverse_obj(qs, (key, 0, {str}))
            if value:
                query[key] = value

        data = self._download_json(
            f'{self._EMBED_HOST}/inc/embed/getvidlink.php', video_id,
            'Downloading video token JSON', query=query, impersonate=True,
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Referer': embed_url,
                'X-Requested-With': 'XMLHttpRequest',
            })
        server = traverse_obj(data, (('server', 'cdn'), {url_or_none}, any))
        if not server:
            raise ExtractorError('No media server returned', expected=True)

        headers = {'Referer': f'{self._EMBED_HOST}/'}
        formats = []
        for key, format_id, height in self._QUALITIES:
            token = traverse_obj(data, (key, {str}))
            if not token:
                continue
            formats.append({
                'url': f'{server}/getvid?evid={token}',
                'format_id': format_id,
                'height': height,
                'ext': 'mp4',
                'http_headers': headers,
                'impersonate': self._MEDIA_IMPERSONATE,
            })
        if not formats:
            raise ExtractorError('No video formats available', expected=True)

        return {
            'id': video_id,
            'formats': formats,
        }


class WCOStreamIE(WCOStreamBaseIE):
    IE_NAME = 'wcostream'
    IE_DESC = 'wcostream.tv'
    _VALID_URL = (
        r'https?://(?:www\.)?wcostream\.tv/'
        r'(?!anime(?:/|$)|search(?:/|$)|genre(?:/|$)|dubbed-anime(?:/|$)|'
        r'subbed-anime(?:/|$)|cartoon(?:-list)?(?:/|$)|movie(?:s|-list)?(?:/|$)|'
        r'wp-|inc/|js/|user(?:/|$)|login(?:/|$)|register(?:/|$))'
        r'(?P<id>[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)/?(?:$|[?#])')
    _TESTS = [{
        'url': 'https://www.wcostream.tv/rilakkuma-episode-22-english-dubbed',
        'md5': 'c2398a3d033e8bf2077144db2260540a',
        'info_dict': {
            'id': 'rilakkuma-episode-22-english-dubbed',
            'ext': 'mp4',
            'title': 'Rilakkuma Episode 22 English Dubbed',
        },
    }, {
        'url': 'https://www.wcostream.tv/spongebob-squarepants-season-6-episode-4-not-normal-gone',
        'info_dict': {
            'id': 'spongebob-squarepants-season-6-episode-4-not-normal-gone',
            'title': 'SpongeBob SquarePants Season 6 Episode 4 Not Normal – Gone',
        },
        'playlist_mincount': 2,
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://wcostream.tv/rilakkuma-episode-22-english-dubbed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)
        embed_urls = self._extract_embed_urls(webpage)
        if not embed_urls:
            raise ExtractorError('No WCO embed player found', expected=True)

        title = self._page_title(webpage)
        entries = []
        for idx, embed_url in enumerate(embed_urls, 1):
            video_id = display_id if len(embed_urls) == 1 else f'{display_id}-{idx}'
            info = self._extract_from_embed(embed_url, video_id)
            info['title'] = (
                title if len(embed_urls) == 1
                else (f'{title} (part {idx})' if title else f'{display_id} part {idx}'))
            entries.append(info)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, display_id, title, multi_video=True)


class WCOStreamShowIE(WCOStreamBaseIE):
    IE_NAME = 'wcostream:show'
    IE_DESC = 'wcostream.tv shows'
    _VALID_URL = r'https?://(?:www\.)?wcostream\.tv/anime/(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'https://www.wcostream.tv/anime/spongebob-squarepants',
        'info_dict': {
            'id': 'spongebob-squarepants',
            'title': 'SpongeBob SquarePants',
        },
        'playlist_mincount': 50,
        'params': {
            'skip_download': True,
            'extract_flat': True,
        },
    }, {
        'url': 'https://www.wcostream.tv/anime/rilakkuma',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id, impersonate=True)
        hrefs = re.findall(
            r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*\bdark-episode-item\b', webpage)
        hrefs.extend(re.findall(
            r'<a[^>]+class="[^"]*\bdark-episode-item\b[^"]*"[^>]*href="([^"]+)"', webpage))
        entries = [
            self.url_result(urljoin(url, path), WCOStreamIE)
            for path in orderedSet(hrefs)
            if path and not path.startswith('#')
        ]
        if not entries:
            raise ExtractorError('No episodes found', expected=True)
        return self.playlist_result(entries, show_id, self._page_title(webpage))
