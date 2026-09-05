import re
import time
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    decode_packed_codes,
    determine_ext,
    float_or_none,
    int_or_none,
    orderedSet,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class KissasianIE(InfoExtractor):
    IE_NAME = "kissasian"
    IE_DESC = "Kissasian"
    _VALID_URL = (
        r"https?://(?:www\d*\.|ww\d+\.)?kissasian\.video/watch/"
        r"(?P<slug>[^/?#]+)/episode-(?P<episode>\d+)(?:\.html)?"
    )
    _EMBED_REGEXES = [
        r'<iframe[^>]+src=["\']((?:https?:)?//(?:www\.)?hndrama\.(?:cc|com)/embed/[^"\']+)',
        r"(https?://(?:www\.)?hndrama\.(?:cc|com)/embed/drama/\d+/\d+)",
    ]
    _SKIP_HOST_RE = re.compile(
        r"(?:hglink|streamwish|dood(?:stream)?|mp4upload|mixdrop|miixdrop|"
        r"streamtape|watchadsontape|vidbasic)\.",
        re.I,
    )
    _TESTS = [
        {
            "url": "https://ww8.kissasian.video/watch/pearl-in-red-2026/episode-1.html",
            "skip": "downloaded file is empty",
            "md5": "2035e69f9848d7205ff2de713aa94bcb",
            "info_dict": {
                "id": "pearl-in-red-2026-episode-1",
                "ext": "mp4",
                "title": "Watch Pearl in Red (2026) Episode 1 drama online | KissAsian",
                "description": "md5:b04260c7d692667de7238d1ecd16218d",
                "thumbnail": "https://pixibay.cc/lhh3wr4p0itl.jpg",
                "duration": 1921.47,
                "episode": "Episode 1",
                "episode_number": 1,
                "timestamp": 1778900734,
                "upload_date": "20260516",
            },
        },
        {
            "url": "https://ww1.kissasian.video/watch/the-real-has-come-2023/episode-26.html",
            "only_matching": True,
        },
        {
            "url": "https://kissasian.video/watch/pearl-in-red-2026/episode-1.html",
            "only_matching": True,
        },
        {
            "url": "https://ww8.kissasian.video/watch/otto-no-kanojo-2013/episode-8.html",
            "only_matching": True,
        },
    ]

    def _download(self, url, video_id, note, fatal=True, headers=None):
        webpage = self._download_webpage(url, video_id, note, fatal=False, headers=headers)
        if webpage:
            return webpage
        return self._download_webpage(url, video_id, note, fatal=fatal, headers=headers, impersonate=True)

    def _player_urls_from_webpage(self, webpage, base_url):
        urls = []
        for src in re.findall(r'<iframe[^>]+src=["\']([^"\']+)', webpage):
            urls.append(urljoin(base_url, unescapeHTML(src)))
        for src in re.findall(r'data-video=["\']([^"\']+)', webpage):
            urls.append(urljoin(base_url, unescapeHTML(src)))
        return [u for u in urls if url_or_none(u)]

    def _is_aggregator(self, url):
        host = urllib.parse.urlparse(url).netloc
        return host.endswith("vidbasic.top")

    def _should_skip_host(self, url):
        host = urllib.parse.urlparse(url).netloc
        return bool(self._SKIP_HOST_RE.search(host + "."))

    def _server_sort_key(self, name):
        name = (name or "").lower()
        if "vidhide" in name:
            return 0
        if "standard" in name:
            return 1
        return 2

    def _extract_packed_formats(self, player_url, webpage, video_id):
        packed = self._search_regex(r"(eval\(function\(p,a,c,k,e,d\).+)", webpage, "packed player", default=None)
        decoded = decode_packed_codes(packed) if packed else ""
        blob = f"{webpage}\n{decoded}"
        extra = {
            "duration": float_or_none(
                self._search_regex(r'\bduration\s*:\s*["\']([^"\']+)["\']', blob, "duration", default=None)
            ),
            "thumbnail": url_or_none(
                self._search_regex(r'\bimage\s*:\s*["\'](https?://[^"\']+)["\']', blob, "thumbnail", default=None)
            ),
        }

        links = self._search_json(r"var\s+links\s*=", blob, "player links", video_id, fatal=False) or {}
        # hls4 is an ad playlist of image segments; hls3 (.txt) often 404s
        media_urls = []
        if url_or_none(links.get("hls2")):
            media_urls.append(links["hls2"])
        elif url_or_none(links.get("hls3")):
            media_urls.append(links["hls3"])
        else:
            media_urls.extend(re.findall(r'https?://[^\'"\\\s<>]+\.m3u8[^\'"\\\s<>]*', decoded))

        player_host = urllib.parse.urlparse(player_url).netloc
        formats, subtitles, seen_media = [], {}, set()
        for media_url in media_urls:
            media_url = url_or_none(urljoin(player_url, media_url))
            if not media_url or media_url in seen_media:
                continue
            seen_media.add(media_url)
            parsed = urllib.parse.urlparse(media_url)
            if parsed.netloc == player_host and parsed.path.startswith("/stream/"):
                continue
            ext = determine_ext(media_url, default_ext="m3u8")
            if not (ext in ("m3u8", "txt") or ".m3u8" in media_url):
                continue
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, "mp4", m3u8_id="hls", fatal=False, headers={"Referer": player_url}
            )
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        return formats, subtitles, extra

    def _expand_player_url(self, player_url, video_id, referer):
        if self._is_aggregator(player_url):
            aggregator = (
                self._download(player_url, video_id, "Downloading aggregator player", fatal=False, headers=referer)
                or ""
            )
            return [u for u in self._player_urls_from_webpage(aggregator, player_url) if not self._should_skip_host(u)]
        if self._should_skip_host(player_url):
            return []
        return [player_url]

    def _collect_player_urls(self, embed_url, embed, video_id):
        parsed = urllib.parse.urlparse(embed_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        servers = re.findall(r'data-hash=["\']([^"\']+)["\'][^>]*>([^<]+)', embed)
        if not servers:
            servers = [(h, "") for h in re.findall(r'/streaming/([^"\']+)', embed)]
        servers.sort(key=lambda item: self._server_sort_key(item[1]))

        referer = {"Referer": embed_url}
        player_urls, usable = [], []
        for server_hash, _name in servers:
            stream_url = urljoin(origin, f"/streaming/{server_hash}")
            stream_page = self._download(
                stream_url, video_id, "Downloading HnDrama server", fatal=False, headers=referer
            )
            if not stream_page:
                continue
            for player_url in self._player_urls_from_webpage(stream_page, stream_url):
                player_urls.extend(self._expand_player_url(player_url, video_id, referer))
            usable = [u for u in orderedSet(player_urls) if url_or_none(u) and not self._should_skip_host(u)]
            if usable:
                break
        return sorted(usable, key=lambda u: 0 if "/v/" in urllib.parse.urlparse(u).path else 1)

    def _extract_hndrama_formats(self, embed_url, embed, video_id):
        formats, subtitles, extra = [], {}, {}
        for player_url in self._collect_player_urls(embed_url, embed, video_id):
            webpage = self._download(
                player_url, video_id, "Downloading host player", fatal=False, headers={"Referer": embed_url}
            )
            if not webpage:
                continue
            fmts, subs, host_extra = self._extract_packed_formats(player_url, webpage, video_id)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
            extra.update({k: v for k, v in host_extra.items() if v})
            if formats:
                break
        return formats, subtitles, extra

    def _download_watch_page(self, url, video_id):
        webpage, embed_url = None, None
        for attempt in range(5):
            webpage = self._download(url, video_id, "Downloading webpage", fatal=False)
            embed_url = self._search_regex(self._EMBED_REGEXES, webpage or "", "HnDrama embed", default=None)
            if embed_url:
                return webpage, urljoin(url, embed_url)
            if attempt < 4:
                self.report_warning("Kissasian returned an empty or error page; retrying")
                time.sleep(1)
        raise ExtractorError("Unable to extract HnDrama embed", expected=True)

    def _real_extract(self, url):
        slug, episode = self._match_valid_url(url).group("slug", "episode")
        video_id = f"{slug}-episode-{episode}"
        webpage, embed_url = self._download_watch_page(url, video_id)
        embed = self._download(embed_url, video_id, "Downloading HnDrama embed")

        formats, subtitles, extra = self._extract_hndrama_formats(embed_url, embed, video_id)
        if not formats:
            raise ExtractorError("Unable to extract video formats", expected=True)

        json_ld = self._search_json_ld(webpage, video_id, default={})
        title = (
            self._og_search_title(webpage, default=None)
            or clean_html(self._html_search_regex(r"<h1[^>]*>(.+?)</h1>", webpage, "title", default=None))
            or json_ld.get("title")
            or video_id
        )

        return {
            **json_ld,
            "id": video_id,
            "title": title,
            "description": self._og_search_description(webpage, default=None) or json_ld.get("description"),
            "thumbnail": extra.get("thumbnail") or self._og_search_thumbnail(webpage) or json_ld.get("thumbnail"),
            "duration": extra.get("duration") or json_ld.get("duration"),
            "episode_number": int_or_none(episode),
            "formats": formats,
            "subtitles": subtitles,
        }
