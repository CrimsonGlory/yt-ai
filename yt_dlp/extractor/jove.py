import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class JoveIE(InfoExtractor):
    _VALID_URL = r"https?://(?:(?:www|app)\.)?jove\.com/(?:[a-z]{2}/)?(?:video|v)/(?P<id>[0-9]+)"
    _TESTS = [
        {
            "url": "http://www.jove.com/video/2744/electrode-positioning-montage-transcranial-direct-current",
            "md5": "7eb69be719ea149b515b9a35b5888428",
            "info_dict": {
                "id": "2744",
                "ext": "mp4",
                "title": "Electrode Positioning and Montage in Transcranial Direct Current Stimulation",
                "description": "md5:015dd4509649c0908bc27f049e0262c6",
                "thumbnail": r"re:https?://.+\.(?:jpg|png)$",
                "upload_date": "20110523",
                "duration": 720,
                "chapters": "count:8",
            },
        },
        {
            "url": "http://www.jove.com/video/51796/culturing-caenorhabditis-elegans-axenic-liquid-media-creation",
            "md5": "a5b4cb47d97208ee24c8e1044c61e393",
            "info_dict": {
                "id": "51796",
                "ext": "mp4",
                "title": "Culturing Caenorhabditis elegans in Axenic Liquid Media and Creation of Transgenic Worms by Microparticle Bombardment",
                "description": "md5:35ff029261900583970c4023b70f1dc9",
                "thumbnail": r"re:https?://.+\.(?:jpg|png)$",
                "upload_date": "20140802",
                "duration": 506,
                "chapters": "count:7",
            },
        },
        {
            "url": "https://app.jove.com/v/2744/electrode-positioning-montage-transcranial-direct-current",
            "only_matching": True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        article = (
            traverse_obj(
                self._download_json(f"https://api.jove.com/api/free/article/en/{video_id}", video_id),
                ("content", {dict}),
            )
            or {}
        )
        domain = traverse_obj(article, ("domain", {dict})) or {}
        videos = traverse_obj(domain, ("videos", {dict})) or {}
        video = videos.get("en") or next(iter(videos.values()), None)
        if not isinstance(video, dict):
            video = {}

        cdn_file = url_or_none(video.get("cdnFile"))
        if not cdn_file:
            raise ExtractorError("No video source available", expected=True)

        formats = []
        if determine_ext(cdn_file) == "m3u8":
            formats = self._extract_m3u8_formats(cdn_file, video_id, "mp4", m3u8_id="hls")
            query = urllib.parse.urlsplit(cdn_file).query
            for fmt in formats:
                fmt["extra_param_to_segment_url"] = query
        else:
            formats.append(
                {
                    "url": cdn_file,
                    "format_id": "http",
                }
            )

        subtitles = {}
        for lang, sub_url in traverse_obj(video, ("subtitles", {dict.items}, ...)):
            if url_or_none(sub_url):
                subtitles.setdefault(lang, []).append({"url": sub_url})

        return {
            "id": video_id,
            "title": clean_html(domain.get("title")),
            "description": clean_html(domain.get("summaryContent") or domain.get("titleDescription")),
            "thumbnail": url_or_none(domain.get("headerImage")),
            "upload_date": unified_strdate(domain.get("publishedAt")),
            "duration": int_or_none(
                video.get("lengthSeconds") or domain.get("lengthSeconds") or article.get("lengthSeconds")
            ),
            "formats": formats,
            "subtitles": subtitles,
            "chapters": traverse_obj(
                video,
                (
                    "chapters",
                    lambda _, v: int_or_none(v["time"]) is not None,
                    {
                        "start_time": ("time", {int_or_none}),
                        "title": ("title", {str}),
                    },
                ),
            ),
        }
