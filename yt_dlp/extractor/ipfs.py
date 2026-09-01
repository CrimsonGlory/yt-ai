import os
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    expand_path,
    traverse_obj,
    url_or_none,
)


class IpfsIE(InfoExtractor):
    IE_NAME = "ipfs"
    IE_DESC = "IPFS"
    _VALID_URL = r"(?P<scheme>ipfs|ipns)://(?:ipfs/)?(?P<id>[^/?#]+)(?P<path>/[^?#]*)?"
    _DEFAULT_GATEWAY = "https://gateway.pinata.cloud"
    _TESTS = [
        {
            "url": "ipfs://bafybeigvafaks2bvivtv46n2z7uxszpvl25jhvzc6dbhnjjgjkbeia5jta/nft.mp4",
            "md5": "ba5c55a16ac4c63a679d65a2fe716306",
            "info_dict": {
                "id": "bafybeigvafaks2bvivtv46n2z7uxszpvl25jhvzc6dbhnjjgjkbeia5jta",
                "ext": "mp4",
                "title": "nft",
            },
        },
        {
            "url": "ipfs://ipfs/bafybeigvafaks2bvivtv46n2z7uxszpvl25jhvzc6dbhnjjgjkbeia5jta/nft.mp4",
            "only_matching": True,
        },
        {
            "url": "ipfs://bafyjvzacdkmdv5iy5ldtibqc6yesvwg3cqmfpdo4clwfrpbc7xdq/index_1080p.m3u8",
            "only_matching": True,
        },
        {
            "url": "ipns://docs.ipfs.tech",
            "only_matching": True,
        },
    ]

    def _get_gateway(self):
        gateway = traverse_obj(self._configuration_arg("gateway", default=[], casesense=True), 0)
        if not gateway:
            gateway = os.environ.get("IPFS_GATEWAY")
        if not gateway:
            gateway_file = expand_path("~/.ipfs/gateway")
            try:
                with open(gateway_file, encoding="utf-8") as f:
                    gateway = f.readline().strip() or None
            except OSError:
                pass
        if not gateway:
            gateway = self._DEFAULT_GATEWAY
        gateway = gateway.rstrip("/")
        for suffix in ("/ipfs", "/ipns"):
            if gateway.lower().endswith(suffix):
                gateway = gateway[: -len(suffix)]
                break
        if not url_or_none(gateway):
            raise ExtractorError(f"Invalid IPFS gateway: {gateway}", expected=True)
        return gateway

    def _real_extract(self, url):
        scheme, video_id, path = self._match_valid_url(url).group("scheme", "id", "path")
        path = path or ""
        gateway = self._get_gateway()
        http_url = f"{gateway}/{scheme}/{video_id}{path}"
        filename = urllib.parse.unquote(path.rsplit("/", 1)[-1])
        title = os.path.splitext(filename)[0] or video_id
        self.to_screen(f"Using gateway {gateway}")

        ext = determine_ext(http_url)
        if ext == "m3u8":
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(http_url, video_id, "mp4", m3u8_id="hls")
            return {
                "id": video_id,
                "title": title,
                "formats": formats,
                "subtitles": subtitles,
            }

        return {
            "id": video_id,
            "title": title,
            "url": http_url,
            "ext": ext if ext != "unknown_video" else None,
        }
