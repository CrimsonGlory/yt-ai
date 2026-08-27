from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class MochaVideoIE(InfoExtractor):
    _VALID_URL = r"https?://video\.mocha\.com\.vn/(?P<video_slug>[\w-]+)(?:\.html)?"
    _TESTS = [
        {
            "url": "https://video.mocha.com.vn/nhung-danh-hai-trien-vong-1-v20197697.html",
            "info_dict": {
                "id": "20197697",
                "title": "Những danh hài triển vọng #1",
                "ext": "mp4",
                "view_count": int,
                "like_count": int,
                "dislike_count": int,
                "display_id": "nhung-danh-hai-trien-vong-1",
                "thumbnail": r"re:https?://.*\.jpg",
                "description": "Những danh hài triển vọng #1",
                "duration": 51,
                "timestamp": 1768899300,
                "upload_date": "20260120",
                "comment_count": int,
                "categories": ["Hài"],
                "channel": "Coi Cấm Cười TV",
                "channel_id": "255562",
                "channel_follower_count": int,
            },
        },
        {
            "url": "http://video.mocha.com.vn/chuyen-meo-gia-su-tu-thong-diep-cuoc-song-v18694039",
            "info_dict": {
                "id": "18694039",
                "ext": "mp4",
            },
            "skip": "video gone",
        },
    ]

    def _real_extract(self, url):
        video_slug = self._match_valid_url(url).group("video_slug")
        json_data = self._download_json(
            "https://apivideo.mocha.com.vn/onMediaBackendBiz/mochavideo/getVideoDetail",
            video_slug,
            query={
                "url": f"https://video.mocha.com.vn/{video_slug}.html",
                "token": "",
            },
        )["data"]["videoDetail"]
        video_id = str_or_none(json_data.get("id"))
        if not video_id:
            raise ExtractorError("This video is unavailable", expected=True)

        formats, subtitles = [], {}
        for video in traverse_obj(json_data, ("list_resolution", ..., {dict})):
            video_path = url_or_none(video.get("video_path"))
            if not video_path:
                continue
            fmts, subs = self._extract_m3u8_formats_and_subtitles(video_path, video_id, "mp4", fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        original_path = url_or_none(json_data.get("original_path"))
        if original_path:
            if determine_ext(original_path) == "m3u8":
                if not formats:
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(original_path, video_id, "mp4")
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append({"url": original_path, "ext": "mp4"})

        return {
            "id": video_id,
            "display_id": json_data.get("slug") or video_slug,
            "title": json_data.get("name"),
            "formats": formats,
            "subtitles": subtitles,
            "description": json_data.get("description"),
            "duration": json_data.get("durationS"),
            "view_count": json_data.get("total_view"),
            "like_count": json_data.get("total_like"),
            "dislike_count": json_data.get("total_unlike"),
            "thumbnail": json_data.get("image_path_thumb"),
            "timestamp": int_or_none(json_data.get("publish_time"), scale=1000),
            "is_live": json_data.get("isLive"),
            "channel": traverse_obj(json_data, ("channels", 0, "name")),
            "channel_id": traverse_obj(json_data, ("channels", 0, "id", {str_or_none})),
            "channel_follower_count": traverse_obj(json_data, ("channels", 0, "numfollow")),
            "categories": traverse_obj(json_data, ("categories", ..., "categoryname")),
            "comment_count": json_data.get("total_comment"),
        }
