import base64
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    merge_dicts,
    orderedSet,
    parse_duration,
    remove_end,
    unescapeHTML,
    url_or_none,
)


class ThotDeepIE(InfoExtractor):
    IE_DESC = "thotdeep.com"
    _VALID_URL = r"https?://(?:www\.)?thotdeep\.com/(?P<id>\d+)(?:/(?P<display_id>[^/?#]+))?"
    _TESTS = [
        {
            "url": "https://thotdeep.com/60793/not-aespa-winter-winteo-the-prettiest-little-cocksucker-full-video-13-56",
            "md5": "9a53afc608b6c128f92db6e7bcf1c4d7",
            "info_dict": {
                "id": "60793",
                "ext": "mp4",
                "display_id": "not-aespa-winter-winteo-the-prettiest-little-cocksucker-full-video-13-56",
                "title": "Not Aespa Winter 윈터 - The Prettiest Little Cocksucker (FULL VIDEO 13:56)",
                "description": "Watch Not Aespa Winter 윈터 - The Prettiest Little Cocksucker (FULL VIDEO 13:56) deepfakes videos on ThotDeep.",
                "thumbnail": r"re:https?://cdn\d+\.thotdeep\.com/.+",
                "duration": 80,
                "timestamp": 1722079049,
                "upload_date": "20240727",
                "view_count": int,
                "cast": ["Winter (aespa)", "Fiamurr", "Winter"],
                "categories": [
                    "Petite",
                    "Brunette",
                    "Big Dick",
                    "POV",
                    "Handjob",
                    "Deepthroat",
                    "Blowjob",
                    "Korean",
                    "Asian",
                ],
                "tags": ["Not", "kpop", "korea", "korean", "aespa", "winter", "min", "Kim", "林明祯", "deepfake"],
                "age_limit": 18,
            },
            "params": {"fixup": "never"},
        },
        {
            "url": "https://thotdeep.com/60510/preview-ipx-706-karina-aespa",
            "only_matching": True,
        },
        {
            "url": "https://www.thotdeep.com/60793",
            "only_matching": True,
        },
    ]

    @staticmethod
    def _decode_source(encoded):
        # JWPlayer f(): drop 16-char pads, reverse, then atob
        if not encoded:
            return None
        candidates = [encoded[16:-16], encoded] if len(encoded) > 32 else [encoded]
        for candidate in candidates:
            blob = candidate[::-1]
            pad = "=" * ((4 - len(blob) % 4) % 4)
            try:
                decoded = base64.b64decode(blob + pad).decode()
            except (ValueError, UnicodeDecodeError):
                continue
            if url_or_none(decoded):
                return decoded
        return None

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group("id", "display_id")
        webpage = self._download_webpage(url, video_id)

        encoded = unescapeHTML(self._search_regex(r'<[^>]+\bdata-source=["\']([^"\']+)', webpage, "player source"))
        media_url = self._decode_source(encoded)
        if not media_url:
            raise ExtractorError("Unable to decode player source", expected=True)

        # Signed /m3u8/ playlists are single-use; keep the body so hlsnative
        # does not refetch the manifest.
        headers = {"Referer": url}
        m3u8_doc = self._download_webpage(media_url, video_id, "Downloading m3u8 playlist", headers=headers)
        if not m3u8_doc.lstrip().startswith("#EXTM3U"):
            raise ExtractorError("Unable to download HLS playlist", expected=True)
        formats, subtitles = self._parse_m3u8_formats_and_subtitles(m3u8_doc, media_url, ext="mp4", m3u8_id="hls")
        for fmt in formats:
            fmt["hls_media_playlist_data"] = m3u8_doc
            fmt.setdefault("http_headers", headers)

        json_ld = self._search_json_ld(webpage, video_id, expected_type="VideoObject", default={})
        json_ld.pop("url", None)
        json_ld.pop("ext", None)

        title = (
            clean_html(self._html_search_regex(r"<h1[^>]*>([^<]+)", webpage, "title", default=None))
            or remove_end(self._og_search_title(webpage, default="") or "", " - ThotDeep")
            or None
        )

        return merge_dicts(
            {
                "id": video_id,
                "display_id": display_id,
                "title": title or None,
                "description": self._og_search_description(webpage, default=None),
                "thumbnail": self._og_search_thumbnail(webpage, default=None),
                "duration": parse_duration(
                    self._search_regex(
                        r'<div class="duration">(\d+:\d+(?::\d+)?)</div>', webpage, "duration", default=None
                    )
                ),
                "formats": formats,
                "subtitles": subtitles,
                "age_limit": 18,
                "cast": orderedSet(re.findall(r'class="model-profile-name">([^<]+)', webpage)) or None,
                "categories": orderedSet(
                    filter(
                        None,
                        (clean_html(m) for m in re.findall(r'class="cat-pill"[^>]*>(.*?)</a>', webpage, re.DOTALL)),
                    )
                )
                or None,
                "tags": orderedSet(
                    filter(
                        None, (clean_html(m).lstrip("#") for m in re.findall(r'class="tag-pill"[^>]*>([^<]+)', webpage))
                    )
                )
                or None,
            },
            json_ld,
        )
