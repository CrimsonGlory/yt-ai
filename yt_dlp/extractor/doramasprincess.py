import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    clean_html,
    decode_packed_codes,
    determine_ext,
    float_or_none,
    int_or_none,
    orderedSet,
    unescapeHTML,
    url_or_none,
    urlencode_postdata,
    urljoin,
)


class DoramasPrincessIE(InfoExtractor):
    IE_NAME = 'doramasprincess'
    IE_DESC = 'DoramasPrincess'
    _VALID_URL = r'https?://(?:www\.)?doramasprincess\.com/(?P<kind>serie|movie)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://doramasprincess.com/serie/the-one-2077-1-season-8-episode',
        'md5': '395a2d5b7f6e04835557dfddcd9a07a1',
        'info_dict': {
            'id': 'the-one-2077-1-season-8-episode',
            'ext': 'mp4',
            'title': 'Ver The One capitulo 8 sub español gratis✅',
            'description': 'md5:fd467aa124683cbc62086025a6873355',
            'thumbnail': r're:https?://doramasprincess\.com/public/upload/cover/.+',
            'duration': 590.63,
            'series': 'The One',
            'season': 'Season 1',
            'season_number': 1,
            'episode': 'Episode 8',
            'episode_number': 8,
        },
    }, {
        'url': 'https://doramasprincess.com/serie/the-one-2077',
        'info_dict': {
            'id': 'the-one-2077',
            'title': 'The One',
        },
        'playlist_mincount': 1,
        'params': {'skip_download': True},
    }, {
        'url': 'https://doramasprincess.com/serie/i-am-nobody-the-showdown-between-yin-yang-1017-1-season-1-episode',
        'only_matching': True,
    }, {
        'url': 'https://doramasprincess.com/movie/chains-of-heart-the-movie-280',
        'only_matching': True,
    }, {
        'url': 'https://www.doramasprincess.com/serie/the-one-2077-1-season-8-episode',
        'only_matching': True,
    }]

    def _extract_player_formats(self, webpage, video_id, page_url):
        formats, subtitles = [], {}
        if not webpage:
            return formats, subtitles, None

        for entry in self._parse_html5_media_entries(page_url, webpage, video_id) or []:
            formats.extend(entry.get('formats') or [])
            self._merge_subtitles(entry.get('subtitles') or {}, target=subtitles)

        packed = self._search_regex(
            r'(eval\(function\(p,a,c,k,e,d\).+)', webpage, 'packed player', default=None)
        decoded = decode_packed_codes(packed) if packed else ''
        seen = {f.get('url') for f in formats if f.get('url')}
        candidates = []
        for media_url in re.findall(r'https?://[^\'"\\\s<>]+', decoded):
            media_url = url_or_none(unescapeHTML(media_url.rstrip('\\,;')))
            if not media_url or media_url in seen:
                continue
            ext = determine_ext(media_url)
            is_hls = ext in ('m3u8', 'txt') or '.m3u8' in media_url
            if not (is_hls or ext == 'mp4'):
                continue
            seen.add(media_url)
            candidates.append((media_url, is_hls))
        # Host pages list both `hls2` (.m3u8) and `hls3` (.txt); the .txt variant 404s.
        if any('.m3u8' in media_url for media_url, is_hls in candidates if is_hls):
            candidates = [
                item for item in candidates
                if not item[1] or '.m3u8' in item[0]]
        for media_url, is_hls in candidates:
            if is_hls:
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                    headers={'Referer': page_url})
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
            else:
                formats.append({
                    'url': media_url,
                    'ext': 'mp4',
                    'http_headers': {'Referer': page_url},
                })

        duration = float_or_none(self._search_regex(
            r'\bduration\s*:\s*["\']([^"\']+)["\']', decoded, 'duration', default=None))
        return formats, subtitles, duration

    def _extract_embeds(self, url, video_id, webpage):
        embed_ids = orderedSet(re.findall(r'\bdata-embed=["\'](\d+)["\']', webpage))
        if not embed_ids:
            self.raise_no_formats('No player embeds found', expected=True, video_id=video_id)

        parsed = urllib.parse.urlparse(url)
        origin = f'{parsed.scheme}://{parsed.netloc}'
        formats, subtitles, duration = [], {}, None
        for embed_id in embed_ids:
            embed_html = self._download_webpage(
                f'{origin}/ajax/embed', video_id,
                note=f'Downloading embed {embed_id}',
                data=urlencode_postdata({'id': embed_id}),
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': origin,
                    'Referer': url,
                    'X-Requested-With': 'XMLHttpRequest',
                }, fatal=False)
            if not embed_html:
                continue

            pages = [(embed_html, url)]
            for iframe_url in orderedSet(re.findall(
                    r'<iframe[^>]+src=["\']([^"\']+)', embed_html)):
                iframe_url = url_or_none(urljoin(url, unescapeHTML(iframe_url)))
                if not iframe_url:
                    continue
                iframe_html = self._download_webpage(
                    iframe_url, video_id, 'Downloading embed player',
                    headers={'Referer': url}, fatal=False)
                if iframe_html and 'File is no longer available' not in iframe_html:
                    pages.append((iframe_html, iframe_url))

            for html, page_url in pages:
                fmts, subs, dur = self._extract_player_formats(html, video_id, page_url)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
                duration = duration or dur

        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)
        return formats, subtitles, duration

    def _real_extract(self, url):
        kind, video_id = self._match_valid_url(url).group('kind', 'id')
        webpage = self._download_webpage(url, video_id)

        title = (
            clean_html(self._html_search_regex(
                r'<h1[^>]*>([^<]+)', webpage, 'title', default=None))
            or self._og_search_title(webpage, default=None)
            or self._html_extract_title(webpage, default=video_id))

        if kind == 'serie' and not re.search(r'-\d+-season-\d+-episode$', video_id):
            episode_urls = [
                u for u in orderedSet(
                    urljoin(url, path) for path in re.findall(
                        r'href=["\']([^"\']+-\d+-season-\d+-episode(?:/)?)["\']', webpage))
                if '/serie/' in u]
            if not episode_urls:
                self.raise_no_formats('No episodes found', expected=True, video_id=video_id)
            return self.playlist_from_matches(
                episode_urls, video_id, title, ie=self.ie_key())

        formats, subtitles, duration = self._extract_embeds(url, video_id, webpage)
        season_number = episode_number = None
        ep_mobj = re.search(r'-(\d+)-season-(\d+)-episode$', video_id)
        if ep_mobj:
            season_number, episode_number = int_or_none(ep_mobj.group(1)), int_or_none(ep_mobj.group(2))

        return {
            'id': video_id,
            'title': self._og_search_title(webpage, default=None) or title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'series': title if ep_mobj else None,
            'season_number': season_number,
            'episode_number': episode_number,
            'formats': formats,
            'subtitles': subtitles,
        }
