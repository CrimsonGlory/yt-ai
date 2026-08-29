from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    filter_dict,
    float_or_none,
    int_or_none,
    parse_iso8601,
    parse_qs,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ViddlerIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r"""(?x)
        https?://(?:www\.)?viddler\.com/
        (?:
            (?:\#/)?embed(?:/player)?(?:/(?P<embed_id>[A-Za-z0-9_-]+))?(?:[/?#]|$)
            |(?:p|v|player|video|video-iframe)/(?P<id>[A-Za-z0-9_-]+)
            |(?!(?:signup|upload)(?:[/?#]|$))
             (?P<slug>[A-Za-z0-9]{6})(?:[/?#].*)?$
        )
    """
    _EMBED_REGEX = [
        r'<(?:iframe[^>]+?src|param[^>]+?value)=(["\'])(?P<url>(?:https?:)?//(?:www\.)?viddler\.com/(?:embed|player)/.+?)\1'
    ]
    _API_BASE = "https://viddler.com/api/videos"
    _TESTS = [
        {
            "url": "https://viddler.com/p/9hPBbd",
            "md5": "264b412b34b46a19f099dcc8ee1a1f26",
            "info_dict": {
                "id": "9hPBbd",
                "ext": "mp4",
                "title": "Atticus Finch_ A hero for all time",
                "description": "Uploaded on 3/27/2025",
                "uploader": "funksam",
                "duration": 108,
                "timestamp": 1743114967,
                "upload_date": "20250327",
                "view_count": int,
                "thumbnail": r"re:https?://.+\.jpg",
            },
        },
        {
            "url": "https://viddler.com/9hPBbd",
            "only_matching": True,
        },
        {
            "url": "https://viddler.com/video/33",
            "only_matching": True,
        },
        {
            "url": "https://viddler.com/embed/player?id=33",
            "only_matching": True,
        },
        {
            "url": "http://www.viddler.com/v/43903784",
            "md5": "9eee21161d2c7f5b39690c3e325fab2f",
            "info_dict": {
                "id": "43903784",
                "ext": "mov",
                "title": "Video Made Easy",
                "description": "md5:6a697ebd844ff3093bd2e82c37b409cd",
                "uploader": "viddler",
                "timestamp": 1335371429,
                "upload_date": "20120425",
                "duration": 100.89,
                "thumbnail": r"re:https?://.+\.jpg",
                "view_count": int,
                "comment_count": int,
                "categories": [
                    "video content",
                    "high quality video",
                    "video made easy",
                    "how to produce video with limited resources",
                    "viddler",
                ],
            },
            "skip": "legacy Viddler platform shut down in March 2025",
        },
        {
            "url": "http://www.viddler.com/v/4d03aad9/",
            "skip": "legacy Viddler platform shut down in March 2025",
            "md5": "f12c5a7fa839c47a79363bfdf69404fb",
            "info_dict": {
                "id": "4d03aad9",
                "ext": "ts",
                "title": "WALL-TO-GORTAT",
                "upload_date": "20150126",
                "uploader": "deadspin",
                "timestamp": 1422285291,
                "view_count": int,
                "comment_count": int,
            },
        },
        {
            "url": "http://www.viddler.com/player/221ebbbd/0/",
            "md5": "740511f61d3d1bb71dc14a0fe01a1c10",
            "info_dict": {
                "id": "221ebbbd",
                "ext": "mov",
                "title": "LETeens-Grammar-snack-third-conditional",
                "description": " ",
                "upload_date": "20140929",
                "uploader": "BCLETeens",
                "timestamp": 1411997190,
                "view_count": int,
                "comment_count": int,
            },
            "skip": "legacy Viddler platform shut down in March 2025",
        },
        {
            # secret protected
            "url": "http://www.viddler.com/v/890c0985?secret=34051570",
            "skip": "legacy Viddler platform shut down in March 2025",
            "info_dict": {
                "id": "890c0985",
                "ext": "mp4",
                "title": "Complete Property Training - Traineeships",
                "description": " ",
                "upload_date": "20130606",
                "uploader": "TiffanyBowtell",
                "timestamp": 1370496993,
                "view_count": int,
                "comment_count": int,
            },
            "params": {
                "skip_download": True,
            },
        },
    ]
    _WEBPAGE_TESTS = [
        {
            "url": "https://deadspin.com/i-cant-stop-watching-john-wall-chop-the-nuggets-with-th-1681801597/",
            "info_dict": {
                "id": "4d03aad9",
                "ext": "mp4",
                "title": "WALL-TO-GORTAT",
            },
            "skip": "Site no longer embeds Viddler",
        }
    ]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = (
            mobj.group("id") or mobj.group("embed_id") or mobj.group("slug") or traverse_obj(parse_qs(url), ("id", -1))
        )
        if not video_id:
            raise ExtractorError("Unable to extract video id", expected=True)

        data = self._fetch_video(video_id)
        if data.get("isRemoved"):
            raise ExtractorError(data.get("message") or "This video has been removed", expected=True)
        if data.get("isPasswordProtected") and data.get("locked", True):
            raise ExtractorError("This video is password protected", expected=True)

        display_id = traverse_obj(data, ("uniqueId", {str})) or video_id
        playback_id = traverse_obj(data, ("muxPlaybackId", {str}))
        if playback_id == "pending":
            playback_id = None
        token = traverse_obj(data, ("muxPlaybackToken", {str}))

        formats, subtitles = [], {}
        r2_manifest = traverse_obj(data, ("r2ManifestUrl", {url_or_none}))
        r2_progressive = traverse_obj(data, ("r2ProgressiveUrl", {url_or_none}))
        if r2_manifest:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                r2_manifest, display_id, "mp4", m3u8_id="r2", fatal=False
            )
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if r2_progressive:
            formats.append(
                {
                    "url": r2_progressive,
                    "ext": "mp4",
                    "format_id": "http-r2",
                }
            )
        if playback_id:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                f"https://stream.mux.com/{playback_id}.m3u8",
                display_id,
                "mp4",
                m3u8_id="mux",
                query=filter_dict({"token": token}),
            )
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if not formats:
            storage = traverse_obj(data, ("storageState", {str}))
            if storage and storage != "active":
                raise ExtractorError(f"This video is currently {storage}", expected=True)
            raise ExtractorError("No playable formats", expected=True)

        thumbnail = traverse_obj(data, ("thumbnailUrl", {url_or_none}))
        if not thumbnail and playback_id:
            thumbnail = f"https://image.mux.com/{playback_id}/thumbnail.jpg"

        return {
            "id": display_id,
            "formats": formats,
            "subtitles": subtitles,
            "thumbnail": thumbnail,
            "timestamp": traverse_obj(data, ("createdAt", {parse_iso8601})),
            **traverse_obj(
                data,
                {
                    "title": ("title", {str}),
                    "description": ("description", {str}),
                    "uploader": ("authorName", {str}),
                    "duration": ("duration", {float_or_none}),
                    "view_count": ("totalViews", {int_or_none}),
                },
            ),
        }

    def _fetch_video(self, video_id):
        headers = {"Accept": "application/json"}
        data = self._download_json(
            f"{self._API_BASE}/{video_id}", video_id, headers=headers, expected_status=(403, 404)
        )
        if isinstance(data, dict) and data.get("id") is not None:
            return data
        by_url = self._download_json(
            f"{self._API_BASE}/by-url/{video_id}",
            video_id,
            "Downloading video JSON by custom URL",
            headers=headers,
            expected_status=(403, 404),
            fatal=False,
        )
        if isinstance(by_url, dict) and by_url.get("id") is not None:
            return by_url
        raise ExtractorError(traverse_obj(data or by_url, ("message", {str})) or "Video not found", expected=True)
