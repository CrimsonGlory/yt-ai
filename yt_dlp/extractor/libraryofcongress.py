import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    parse_filesize,
    url_or_none,
)


class LibraryOfCongressIE(InfoExtractor):
    IE_NAME = "loc"
    IE_DESC = "Library of Congress"
    _VALID_URL = [
        r"https?://(?:www\.)?loc\.gov/(?:item/|today/cyberlc/feature_wdesc\.php\?.*\brec=)(?P<id>[0-9a-z_.]+)",
        r"https?://media\.loc\.gov/services/v1/media/?\?(?:[^#]*&)?id=(?P<id>[0-9A-Fa-f]+)",
    ]
    _TESTS = [
        {
            # media.loc.gov remains publicly reachable; www.loc.gov item pages
            # currently serve a Cloudflare managed challenge from datacenter IPs
            "url": "https://media.loc.gov/services/v1/media?id=E6AB0B2585930180E0438C93F0280180&context=json",
            "md5": "6ec0ae8f07f86731b1b2ff70f046210a",
            "info_dict": {
                "id": "E6AB0B2585930180E0438C93F0280180",
                "ext": "mp4",
                "title": "Pa's trip to Mars",
                "view_count": int,
            },
        },
        {
            # embedded via <div class="media-player"
            "url": "http://loc.gov/item/90716351/",
            "skip": "Cloudflare managed challenge",
            "md5": "6ec0ae8f07f86731b1b2ff70f046210a",
            "info_dict": {
                "id": "90716351",
                "ext": "mp4",
                "title": "Pa's trip to Mars",
                "duration": 0,
                "view_count": int,
            },
        },
        {
            # webcast embedded via mediaObjectId
            "url": "https://www.loc.gov/today/cyberlc/feature_wdesc.php?rec=5578",
            "skip": "Cloudflare managed challenge",
            "info_dict": {
                "id": "5578",
                "ext": "mp4",
                "title": "Help! Preservation Training Needs Here, There & Everywhere",
                "duration": 3765,
                "view_count": int,
                "subtitles": "mincount:1",
            },
            "params": {
                "skip_download": True,
            },
        },
        {
            # with direct download links
            "url": "https://www.loc.gov/item/78710669/",
            "skip": "Cloudflare managed challenge",
            "info_dict": {
                "id": "78710669",
                "ext": "mp4",
                "title": "La vie et la passion de Jesus-Christ",
                "duration": 0,
                "view_count": int,
                "formats": "mincount:4",
            },
            "params": {
                "skip_download": True,
            },
        },
        {
            "url": "https://www.loc.gov/item/ihas.200197114/",
            "only_matching": True,
        },
        {
            "url": "https://www.loc.gov/item/afc1981005_afs20503/",
            "only_matching": True,
        },
    ]

    def _extract_media_id_from_loc_json(self, loc_json):
        for resource in loc_json.get("resources") or []:
            media_id = resource.get("uuid")
            if media_id:
                return media_id
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = None

        if "media.loc.gov" in url:
            media_id = video_id
        else:
            media_id = None
            if "/item/" in url:
                loc_json = self._download_json(
                    f"https://www.loc.gov/item/{video_id}/?fo=json&at=item,resources",
                    video_id,
                    "Downloading loc.gov JSON",
                    fatal=False,
                )
                if loc_json:
                    media_id = self._extract_media_id_from_loc_json(loc_json)
            if not media_id:
                webpage = self._download_webpage(url, video_id)
                media_id = self._search_regex(
                    (
                        r'id=(["\'])media-player-(?P<id>.+?)\1',
                        r'<video[^>]+id=(["\'])uuid-(?P<id>.+?)\1',
                        r'<video[^>]+data-uuid=(["\'])(?P<id>.+?)\1',
                        r'mediaObjectId\s*:\s*(["\'])(?P<id>.+?)\1',
                        r'data-tab="share-media-(?P<id>[0-9A-F]{32})"',
                    ),
                    webpage,
                    "media id",
                    group="id",
                )

        data = self._download_json(f"https://media.loc.gov/services/v1/media?id={media_id}&context=json", media_id)[
            "mediaObject"
        ]

        derivative = data["derivatives"][0]
        media_url = derivative["derivativeUrl"]

        title = (
            derivative.get("shortName")
            or data.get("shortName")
            or (self._og_search_title(webpage) if webpage else None)
        )

        # Following algorithm was extracted from setAVSource js function
        # found in webpage
        media_url = media_url.replace("rtmp", "https")

        is_video = data.get("mediaType", "v").lower() == "v"
        ext = determine_ext(media_url)
        if ext not in ("mp4", "mp3"):
            media_url += ".mp4" if is_video else ".mp3"

        formats = []
        # stream-media.loc.gov /hls-vod/ playlists 404; IIIF on tile.loc.gov is current
        mp4_path = re.search(r"mp4:(.+?)(?:\.mp4)?$", media_url)
        if mp4_path:
            ident = mp4_path.group(1).replace("/", ":")
            formats.append(
                {
                    "url": f"https://tile.loc.gov/streaming-services/iiif/media:{ident}/full/full/0/full/default.m3u8",
                    "format_id": "hls",
                    "ext": "mp4",
                    "protocol": "m3u8_native",
                    "quality": 1,
                    "preference": -1,
                }
            )
        http_format = {
            "url": re.sub(r"(://[^/]+/)(?:[^/]+/)*(?:mp4|mp3):", r"\1", media_url),
            "format_id": "http",
            "quality": 1,
            "preference": 1,
        }
        if not is_video:
            http_format["vcodec"] = "none"
        formats.append(http_format)

        download_url = url_or_none(derivative.get("downloadUrl"))
        if download_url and download_url.lower() != "n/a":
            download_url = download_url.replace("http://", "https://", 1)
            if download_url != http_format["url"]:
                formats.append(
                    {
                        "url": download_url,
                        "format_id": "download",
                        "quality": 1,
                        "preference": 1,
                    }
                )

        download_urls = set()
        for m in re.finditer(
            r'<option[^>]+value=(["\'])(?P<url>.+?)\1[^>]+data-file-download=[^>]+>\s*(?P<id>.+?)(?:(?:&nbsp;|\s+)\((?P<size>.+?)\))?\s*<',
            webpage or "",
        ):
            format_id = m.group("id").lower()
            if format_id in ("gif", "jpeg"):
                continue
            download_url = m.group("url")
            if download_url in download_urls:
                continue
            download_urls.add(download_url)
            formats.append(
                {
                    "url": download_url,
                    "format_id": format_id,
                    "filesize_approx": parse_filesize(m.group("size")),
                }
            )

        duration = float_or_none(data.get("duration"))
        view_count = int_or_none(data.get("viewCount"))

        subtitles = {}
        cc_url = self._proto_relative_url(url_or_none(data.get("ccUrl")))
        if cc_url:
            subtitles.setdefault("en", []).append(
                {
                    "url": cc_url,
                    "ext": "ttml",
                }
            )

        return {
            "id": video_id,
            "title": title,
            "thumbnail": (
                self._proto_relative_url(url_or_none(data.get("thumbnailUrl")))
                or (self._og_search_thumbnail(webpage, default=None) if webpage else None)
            ),
            "duration": duration,
            "view_count": view_count,
            "formats": formats,
            "subtitles": subtitles,
        }
