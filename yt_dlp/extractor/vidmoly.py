from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    js_to_json,
    merge_dicts,
    url_or_none,
)


class VidMolyIE(InfoExtractor):
    IE_NAME = "vidmoly"
    IE_DESC = "VidMoly"
    _DOMAINS = r"(?:www\.)?vidmoly\.(?:to|me|net|biz)"
    _VALID_URL = (
        rf"https?://{_DOMAINS}/(?:embed-|(?:[wvd]|dl)/)?"
        rf"(?P<id>[0-9a-zA-Z]{{10,15}})(?:\.html)?(?:[/?#]|$)"
    )
    _EMBED_REGEX = [
        rf'<iframe[^>]+\bsrc=(["\'])(?P<url>https?://{_DOMAINS}/embed-[0-9a-zA-Z]+\.html(?:\?[^"\']*)?)\1',
    ]
    _EMBED_TEMPLATE = "https://vidmoly.biz/embed-{}.html"
    _TESTS = [
        {
            "url": "https://vidmoly.to/embed-9gqfukicodho.html",
            "md5": "3c04996a0669f9961a2f47bc43063999",
            "info_dict": {
                "id": "9gqfukicodho",
                "ext": "mp4",
                "title": "Arknights S3 01 VOSTFR 1080",
                "thumbnail": r"re:https?://.+\.jpg",
                "duration": 1420,
            },
        },
        {
            "url": "https://vidmoly.net/embed-9gqfukicodho.html",
            "only_matching": True,
        },
        {
            "url": "https://vidmoly.biz/embed-9gqfukicodho.html",
            "only_matching": True,
        },
        {
            "url": "https://vidmoly.me/v/9gqfukicodho",
            "only_matching": True,
        },
        {
            "url": "https://vidmoly.to/w/xhd2pxfap2jk",
            "only_matching": True,
        },
        {
            "url": "https://vidmoly.to/embed-xhd2pxfap2jk.html",
            "only_matching": True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        embed_url = self._EMBED_TEMPLATE.format(video_id)
        webpage = self._download_webpage(
            embed_url,
            video_id,
            headers={
                "Referer": embed_url,
                "Sec-Fetch-Dest": "iframe",
            },
            expected_status=404,
        )

        if "This video not found" in webpage or "File was deleted" in webpage:
            raise ExtractorError("Video not found", expected=True)

        jwplayer_data = self._search_json(
            r"(?:playerInstance\s*=\s*)?player\.setup\s*\(",
            webpage,
            "JWPlayer data",
            video_id,
            transform_source=js_to_json,
            default=None,
        )
        info = (
            self._parse_jwplayer_data(jwplayer_data, video_id, require_title=False, m3u8_id="hls")
            if jwplayer_data
            else {}
        )
        if not isinstance(info, dict):
            info = {}

        if not info.get("formats"):
            m3u8_url = url_or_none(
                self._search_regex(
                    r"""sources\s*:\s*\[\s*\{\s*file\s*:\s*(["'])(?P<url>https?://[^"']+\.m3u8[^"']*)\1""",
                    webpage,
                    "m3u8 URL",
                    group="url",
                    default=None,
                )
            )
            if not m3u8_url:
                raise ExtractorError("No video source found", expected=True)
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(m3u8_url, video_id, "mp4", m3u8_id="hls")
            info["formats"] = formats
            info["subtitles"] = subtitles

        return merge_dicts(
            {
                "id": video_id,
                "title": self._html_extract_title(webpage, default=video_id),
                "thumbnail": url_or_none((jwplayer_data or {}).get("image")) or info.get("thumbnail"),
                "duration": int_or_none((jwplayer_data or {}).get("duration")) or info.get("duration"),
                "http_headers": {"Referer": embed_url},
            },
            info,
        )
