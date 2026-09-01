import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    decode_packed_codes,
    determine_ext,
    float_or_none,
    join_nonempty,
    orderedSet,
    parse_duration,
    parse_iso8601,
    remove_end,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class JavmixIE(InfoExtractor):
    IE_NAME = "javmix"
    IE_DESC = "Javmix.TV"
    _VALID_URL = r"https?://(?:www\.)?javmix\.tv/(?:video|xvideo|fc2ppv)/(?P<id>[^/?#]+)/?"
    _EMBED_SKIP_RE = re.compile(r"(?:whitetrafsa|googletagmanager|yandex|ad-nex)\.", re.I)
    _TESTS = [
        {
            "url": "https://javmix.tv/video/mx-1start635ec/",
            "md5": "3d2a91642718e32a22107b3f5c6a1bba",
            "info_dict": {
                "id": "mx-1start635ec",
                "ext": "mp4",
                "title": "99発のホンモノ精子大量ぶっかけ 松永あかり SODSTAR完全転職 SOD退社記念作品 パンティと写真セット",
                "description": "md5:48704ca41888890dd9109d4ae11a39a7",
                "thumbnail": r"re:https?://.+\.jpg",
                "duration": 14331.38,
                "timestamp": 1788207645,
                "upload_date": "20260831",
                "cast": ["松永あかり"],
                "tags": ["OL", "ドキュメンタリー", "パイパン", "ぶっかけ", "単体作品", "顔射"],
                "age_limit": 18,
            },
            "params": {"format": "best[format_id^=iplayerhls]"},
        },
        {
            "url": "https://javmix.tv/xvideo/mx-x_ekdv-711/",
            "only_matching": True,
        },
        {
            "url": "https://javmix.tv/fc2ppv/fc2ppv-3049947",
            "only_matching": True,
        },
        {
            "url": "https://www.javmix.tv/video/mx-1start635ec/",
            "only_matching": True,
        },
    ]

    @staticmethod
    def _host_id(url):
        host = urllib.parse.urlparse(url).hostname or "host"
        parts = host.split(".")
        return parts[-2] if len(parts) >= 2 else host

    def _embed_urls(self, webpage):
        packed = self._search_regex(r"(eval\(function\(p,a,c,k,e,d\).+)", webpage, "packed player", default="")
        decoded = ""
        if packed:
            try:
                decoded = decode_packed_codes(packed)
            except (AttributeError, TypeError, ValueError):
                decoded = ""
        urls = []
        for src in re.findall(r"""(?x)src=["'](https?://[^"']+)""", decoded):
            src = url_or_none(unescapeHTML(src))
            if src and not self._EMBED_SKIP_RE.search(src):
                urls.append(src)
        return orderedSet(urls)

    def _post_tag_links(self, html, kind):
        return (
            orderedSet(
                unescapeHTML(name.strip())
                for name in re.findall(rf'href="https?://(?:www\.)?javmix\.tv/{kind}/[^"]+"[^>]*>([^<]+)', html)
                if name.strip()
            )
            or None
        )

    def _extract_via_host_ie(self, embed_url):
        skipped = {self.ie_key(), "Generic"}
        for ie in self._downloader._ies.values():
            ie_key = ie.ie_key()
            if ie_key in skipped or not ie.working() or not ie.suitable(embed_url):
                continue
            try:
                info = self._downloader.get_info_extractor(ie_key).extract(embed_url)
            except ExtractorError:
                continue
            if isinstance(info, dict) and (info.get("formats") or info.get("url")):
                return info
        return None

    def _formats_from_info(self, info, format_id):
        formats, subtitles = [], info.get("subtitles") or {}
        if info.get("formats"):
            for fmt in info["formats"]:
                fmt = dict(fmt)
                fmt["format_id"] = join_nonempty(format_id, fmt.get("format_id"))
                formats.append(fmt)
        elif info.get("url"):
            formats.append(
                {
                    "url": info["url"],
                    "ext": info.get("ext") or determine_ext(info["url"], "mp4"),
                    "format_id": format_id,
                    "http_headers": info.get("http_headers"),
                    "impersonate": info.get("impersonate"),
                }
            )
        return formats, subtitles

    def _extract_packed_formats(self, embed_url, webpage, video_id, format_id):
        packed = self._search_regex(r"(eval\(function\(p,a,c,k,e,d\).+)", webpage, "packed player", default=None)
        decoded = ""
        if packed:
            try:
                decoded = decode_packed_codes(packed)
            except (AttributeError, TypeError, ValueError):
                decoded = ""
        blob = f"{webpage}\n{decoded}"
        extra = {
            "duration": float_or_none(
                self._search_regex(r'\bduration\s*:\s*["\']?(\d+(?:\.\d+)?)', blob, "duration", default=None)
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
            media_urls.extend(re.findall(r'https?://[^\'"\\\s<>]+\.m3u8[^\'"\\\s<>]*', decoded or webpage))
            media_urls.extend(re.findall(r'https?://[^\'"\\\s<>]+\.mp4[^\'"\\\s<>]*', decoded or webpage))

        player_host = urllib.parse.urlparse(embed_url).netloc
        headers = {"Referer": embed_url}
        formats, subtitles, seen = [], {}, set()
        for media_url in media_urls:
            media_url = url_or_none(urljoin(embed_url, unescapeHTML(media_url.rstrip("\\,;"))))
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)
            parsed = urllib.parse.urlparse(media_url)
            if parsed.netloc == player_host and parsed.path.startswith("/stream/"):
                continue
            ext = determine_ext(media_url, default_ext="m3u8")
            is_hls = ext in ("m3u8", "txt") or ".m3u8" in media_url
            if is_hls:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, "mp4", m3u8_id=format_id, fatal=False, headers=headers
                )
                for fmt in fmts:
                    fmt.setdefault("http_headers", {}).update(headers)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext == "mp4":
                formats.append(
                    {
                        "url": media_url,
                        "ext": "mp4",
                        "format_id": format_id,
                        "http_headers": headers,
                    }
                )
        return formats, subtitles, extra

    def _extract_embed_formats(self, embed_url, video_id):
        format_id = self._host_id(embed_url)
        host_info = self._extract_via_host_ie(embed_url)
        if host_info:
            formats, subtitles = self._formats_from_info(host_info, format_id)
            if formats:
                return (
                    formats,
                    subtitles,
                    {
                        "duration": float_or_none(host_info.get("duration")),
                        "thumbnail": host_info.get("thumbnail"),
                    },
                )

        webpage = self._download_webpage(
            embed_url, video_id, f"Downloading {format_id} embed", fatal=False, impersonate=True
        )
        if not webpage:
            return [], {}, {}
        return self._extract_packed_formats(embed_url, webpage, video_id, format_id)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)

        if "<title>Just a moment...</title>" in webpage:
            raise ExtractorError("Cloudflare challenge; try again with impersonation (curl_cffi)", expected=True)

        formats, subtitles, duration, thumbnail = [], {}, None, None
        for embed_url in self._embed_urls(webpage):
            try:
                fmts, subs, extra = self._extract_embed_formats(embed_url, video_id)
            except (ExtractorError, KeyError, TypeError, ValueError, IndexError, AttributeError):
                continue
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
            duration = duration or extra.get("duration")
            thumbnail = thumbnail or extra.get("thumbnail")

        if not formats:
            self.raise_no_formats("No video formats found", expected=True, video_id=video_id)

        title = self._html_search_regex(r"<h1[^>]*>([^<]+)", webpage, "title", default=None) or self._og_search_title(
            webpage, default=None
        )
        if title:
            title = remove_end(title, " - Javmix.TV").strip() or title

        post_tag = self._search_regex(r'<div id="post-tag">(.*?)</div>', webpage, "post tags", default="") or ""

        return {
            "id": video_id,
            "title": title,
            "description": (
                self._og_search_description(webpage, default=None)
                or self._html_search_regex(r'<div id="post-content">\s*([^<]+)', webpage, "description", default=None)
            ),
            "thumbnail": thumbnail
            or url_or_none(
                unescapeHTML(self._search_regex(r'data-thumbnail="([^"]+)"', webpage, "thumbnail", default=None))
            ),
            "duration": duration
            or parse_duration(
                (self._html_search_regex(r'id="post-duration">([^<]+)', webpage, "duration", default="") or "").rstrip(
                    "."
                )
            ),
            "timestamp": parse_iso8601(self._html_search_meta("article:published_time", webpage, default=None)),
            "cast": self._post_tag_links(post_tag, "actress"),
            "tags": self._post_tag_links(post_tag, "genre"),
            "age_limit": 18,
            "formats": formats,
            "subtitles": subtitles or None,
        }
