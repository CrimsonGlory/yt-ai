from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    parse_iso8601,
    traverse_obj,
    unescapeHTML,
    url_or_none,
    urljoin,
)


class DocumaniaTVIE(InfoExtractor):
    IE_DESC = "DocumaniaTV"
    _VALID_URL = r"https?://(?:www\.)?documaniatv\.com/(?:embed/|(?:[^/?#]+/)+[^/?#]+-video_)(?P<id>[0-9a-fA-F]+)"
    _TESTS = [
        {
            "url": "https://www.documaniatv.com/ciencia-y-tecnologia/the-pirate-bay-video_22c12b753.html",
            "md5": "92e5da3570a5af703b896f42c0922872",
            "info_dict": {
                "id": "22c12b753",
                "ext": "mp4",
                "title": "The pirate bay",
                "description": "md5:6b8d1f697b78083885f1d8e572fbff1c",
                "thumbnail": r"re:https?://(?:www\.)?documaniatv\.com/uploads/thumbs/22c12b753-1\.webp",
                "duration": 4927,
                "timestamp": 1365505285,
                "upload_date": "20130409",
                "uploader": "machineto",
                "view_count": int,
                "like_count": int,
                "dislike_count": int,
                "filesize": 1071780842,
                "categories": ["ciencia-y-tecnologia"],
            },
        },
        {
            "url": "https://www.documaniatv.com/embed/22c12b753",
            "only_matching": True,
        },
        {
            "url": "https://www.documaniatv.com/naturaleza/leon-video_e2ad51cd7.html",
            "only_matching": True,
        },
    ]
    _ORIGIN = "https://www.documaniatv.com"

    def _download_jw_playlist(self, video_id, url):
        json_path = "/embjson/" if "/embed/" in url else "/json/"
        return self._download_json(
            urljoin(self._ORIGIN, f"{json_path}{video_id}"),
            video_id,
            "Downloading JWPlayer playlist",
            fatal=False,
            headers={
                "Referer": url,
                "Origin": self._ORIGIN,
                "Accept": "application/json, text/javascript, */*; q=0.01",
            },
        )

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_data = self._search_json(
            r"var\s+pm_video_data\s*=",
            webpage,
            "video data",
            video_id,
            contains_pattern=r"\{[^{}]+\}",
            transform_source=js_to_json,
            default={},
        )

        entry = traverse_obj(self._download_jw_playlist(video_id, url), (0, {dict}), ("playlist", 0, {dict})) or {}
        video_url = url_or_none(unescapeHTML(traverse_obj(entry, ("file", {str}))))
        if not video_url:
            video_url = urljoin(self._ORIGIN, f"/stream/{video_id}")

        return {
            "id": video_id,
            "url": video_url,
            "ext": "mp4",
            "http_headers": {
                "Referer": url,
                "Origin": self._ORIGIN,
            },
            "title": (
                traverse_obj(video_data, ("title", {str}))
                or traverse_obj(entry, ("title", {str}))
                or self._og_search_title(webpage, default=None)
                or self._html_search_regex(r'<span[^>]+id="video_title"[^>]*>([^<]+)', webpage, "title", default=None)
            ),
            "description": (
                self._html_search_regex(
                    r'(?s)<div[^>]+class="pm-video-description"[^>]*>(.+?)<dl\b', webpage, "description", default=None
                )
                or self._og_search_description(webpage, default=None)
                or self._html_search_meta("description", webpage, default=None)
            ),
            "thumbnail": (
                traverse_obj(video_data, ("thumb_url", {url_or_none}), ("preview_image_url", {url_or_none}))
                or traverse_obj(entry, ("image", {url_or_none}))
            ),
            "duration": traverse_obj(video_data, ("duration", {int_or_none})),
            "timestamp": (
                traverse_obj(video_data, ("publish_date_timestamp", {int_or_none}))
                or parse_iso8601(traverse_obj(video_data, ("publish_date_str", {str})))
            ),
            "uploader": self._html_search_regex(
                r'por\s*<a\b[^>]+href="[^"]+/user/[^"]+"[^>]*>([^<]+)', webpage, "uploader", default=None
            ),
            "view_count": traverse_obj(video_data, ("views", {int_or_none})),
            "like_count": traverse_obj(video_data, ("likes", {int_or_none})),
            "dislike_count": traverse_obj(video_data, ("dislikes", {int_or_none})),
            "filesize": traverse_obj(entry, ("filesize", {int_or_none})),
            "categories": traverse_obj(video_data, ("category_str", {lambda v: [v] if v else None})),
        }
