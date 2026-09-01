import json
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    unescapeHTML,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class SuperrikiIE(InfoExtractor):
    IE_NAME = 'superriki'
    IE_DESC = 'SuperRiki'
    _VALID_URL = (
        r'https?://(?:[\w-]+\.)?superriki\.yt/'
        r'(?:embed/|index\.php\?(?:[^#]*&)?newsid=|(?P<cat>[\w-]+)/)'
        r'(?P<id>\d+)'
    )
    _TESTS = [
        {
            'url': 'https://y.superriki.yt/comedy/258-alti-ustu-istanbul/source-29-series-2.html',
            'md5': '7cfbb5b89635555c8c122d3f222102a5',
            'info_dict': {
                'id': '258-2',
                'ext': 'mp4',
                'title': 'Alti Ustu Istanbul episode 2 english subtitles',
                'description': 'md5:0029f5254e6f848e6b2afe1d11610c14',
                'thumbnail': r're:https?://.+\.jpg',
                'episode': 'Episode 2',
                'episode_number': 2,
            },
        },
        {
            'url': 'https://superriki.yt/comedy/161-ak-mantk-ntikam-love-logic-revenge/source-23-series-8.html',
            'only_matching': True,
        },
        {
            'url': 'https://y.superriki.yt/comedy/258-alti-ustu-istanbul.html',
            'only_matching': True,
        },
        {
            'url': 'https://y.superriki.yt/embed/258/',
            'only_matching': True,
        },
        {
            'url': 'https://m.superriki.yt/index.php?newsid=161&seourl=ak-mantk-ntikam-love-logic-revenge&seocat=comedy&source=23&series=8',
            'only_matching': True,
        },
    ]

    def _call_iframe_player(self, ajax_url, post_id, select, video_id, referer):
        return self._download_json(
            ajax_url,
            video_id,
            'Downloading iframe player',
            query={
                'mod': 'iframe_player',
                'post_id': post_id,
                'select': select,
            },
            headers={
                'Referer': referer,
                'X-Requested-With': 'XMLHttpRequest',
            },
        )

    def _player_embed_url(self, player_html, page_url):
        src = self._search_regex(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:(?!\1).)+)\1',
            player_html,
            'iframe src',
            default=None,
            group='url',
        )
        if not src:
            return None
        return url_or_none(urljoin(page_url, unescapeHTML(src)))

    def _vidara_source_id(self, selectors):
        return self._search_regex(
            r'(?i)<option value="(\d+)"[^>]*>\s*vidara', selectors, 'vidara source', default=None,
        )

    def _extract_vidara(self, embed_url, video_id):
        parsed = urllib.parse.urlparse(embed_url)
        origin = f'{parsed.scheme}://{parsed.netloc}'
        filecode = parsed.path.rstrip('/').split('/')[-1]
        if not filecode:
            raise ExtractorError('Unable to extract Vidara file code', expected=True)

        stream = self._download_json(
            urljoin(origin, '/api/stream'),
            video_id,
            'Downloading Vidara stream JSON',
            data=json.dumps(
                {
                    'filecode': filecode,
                    'device': 'web',
                },
            ).encode(),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Origin': origin,
                'Referer': embed_url,
            },
        )

        stream_url = traverse_obj(stream, ('streaming_url', {url_or_none}))
        if not stream_url:
            raise ExtractorError('Vidara did not return a stream URL', expected=True)

        headers = {
            'Origin': origin,
            'Referer': embed_url,
        }
        formats, subtitles = [], {}
        if determine_ext(stream_url, default_ext='m3u8') == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id='hls', headers=headers,
            )
        else:
            formats.append(
                {
                    'url': stream_url,
                    'http_headers': headers,
                },
            )

        for sub in traverse_obj(stream, ('subtitles', ..., {dict})) or []:
            sub_url = url_or_none(urljoin(origin, sub.get('file_path')))
            if not sub_url:
                continue
            lang = sub.get('language') or 'und'
            subtitles.setdefault(lang, []).append({'url': sub_url})

        return {
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': headers,
            **traverse_obj(
                stream,
                {
                    'title': ('title', {str}),
                    'thumbnail': ('thumbnail', {url_or_none}),
                },
            ),
        }

    def _real_extract(self, url):
        post_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, post_id)
        page_url = urlh.url

        post_id = self._html_search_regex(r'data-frame=["\'](\d+)["\']', webpage, 'post id', default=post_id)
        select = unescapeHTML(
            self._html_search_regex(r'data-current=["\']([^"\']*)["\']', webpage, 'player select', default=''),
        )

        ajax_url = urllib.parse.urljoin(page_url, '/engine/ajax/controller.php')

        player = self._call_iframe_player(ajax_url, post_id, select, post_id, page_url)
        if not traverse_obj(player, ('success', {bool})):
            raise ExtractorError(
                traverse_obj(player, ('info', {str})) or 'Unable to load SuperRiki player', expected=True,
            )

        selectors = player.get('selectors') or ''
        query = dict(urllib.parse.parse_qsl(select, keep_blank_values=True))
        if not query.get('series'):
            query['series'] = self._search_regex(
                r'(?s)<select name="series">.*?<option value="(\d+)"[^>]*selected',
                selectors,
                'episode number',
                default=None,
            )
        if not query.get('source'):
            query['source'] = self._search_regex(
                r'(?s)<select name="source">.*?<option value="(\d+)"[^>]*selected',
                selectors,
                'source id',
                default=None,
            )

        embed_url = self._player_embed_url(player.get('player') or '', page_url)
        host = (urllib.parse.urlparse(embed_url).hostname or '') if embed_url else ''
        if embed_url and 'vidara' not in host:
            vidara_source = self._vidara_source_id(selectors)
            if vidara_source:
                query['source'] = vidara_source
                player = self._call_iframe_player(ajax_url, post_id, urllib.parse.urlencode(query), post_id, page_url)
                embed_url = self._player_embed_url(player.get('player') or '', page_url)
                host = (urllib.parse.urlparse(embed_url).hostname or '') if embed_url else ''

        series = query.get('series')
        video_id = join_nonempty(post_id, series)
        title = self._og_search_title(webpage, default=None) or self._html_extract_title(webpage) or video_id
        info = {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'episode_number': int_or_none(series),
            'episode': f'Episode {series}' if series else None,
        }

        if embed_url and 'vidara' in host:
            vidara = self._extract_vidara(embed_url, video_id)
            info['title'] = title or vidara.get('title')
            info['thumbnail'] = vidara.get('thumbnail')
            info['formats'] = vidara['formats']
            info['subtitles'] = vidara.get('subtitles')
            info['http_headers'] = vidara.get('http_headers')
            return info

        if embed_url:
            return {
                **info,
                '_type': 'url_transparent',
                'url': embed_url,
            }

        raise ExtractorError('Unable to extract SuperRiki player iframe', expected=True)
