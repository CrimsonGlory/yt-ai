import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    strip_or_none,
    url_or_none,
)


class SkyBaseIE(InfoExtractor):
    BRIGHTCOVE_URL_TEMPLATE = "http://players.brightcove.net/%s/%s_default/index.html?videoId=%s"
    _SDC_EL_REGEX = r'(?s)(<div[^>]+data-(?:component-name|fn)="sdc-(?:articl|sit)e-video"[^>]*>)'
    _PLAYER_EL_REGEX = r"(?s)(<div[^>]*\bui-video-player\b[^>]*>)"
    _UUID_RE = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z", re.I)

    def _process_video_element(self, webpage, sdc_el, url):
        sdc = extract_attributes(sdc_el)
        video_id = sdc.get("data-video-id")
        if not video_id:
            return None
        if self._UUID_RE.match(video_id):
            video_id = f"ref:{video_id}"
        account_id = sdc.get("data-account-id") or "6058004172001"
        player_id = sdc.get("data-player-id") or "RC9PQUaJ6"
        return {
            "_type": "url_transparent",
            "id": video_id,
            "url": self.BRIGHTCOVE_URL_TEMPLATE % (account_id, player_id, video_id),
            "ie_key": "BrightcoveNew",
        }

    def _extract_player_entries(self, webpage, url):
        entries = []
        for regex in (self._PLAYER_EL_REGEX, self._SDC_EL_REGEX):
            for sdc_el in re.findall(regex, webpage):
                entry = self._process_video_element(webpage, sdc_el, url)
                if entry:
                    entries.append(entry)
        return entries

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        entries = self._extract_player_entries(webpage, url)
        if not entries:
            raise ExtractorError("Unable to extract video player")
        info = entries[0]
        info.update(
            {
                "title": self._og_search_title(webpage),
                "description": strip_or_none(self._og_search_description(webpage)),
            }
        )
        return info


class SkySportsIE(SkyBaseIE):
    IE_NAME = "sky:sports"
    _VALID_URL = r"https?://(?:www\.)?skysports\.com/watch/video/([^/]+/)*(?P<id>[0-9]+)"
    _TESTS = [
        {
            "url": "http://www.skysports.com/watch/video/10328419/bale-its-our-time-to-shine",
            "md5": "77d59166cddc8d3cb7b13e35eaf0f5ec",
            "info_dict": {
                "id": "o3eWJnNDE6l7kfNO8BOoBlRxXRQ4ANNQ",
                "ext": "mp4",
                "title": "Bale: It's our time to shine",
                "description": "md5:e88bda94ae15f7720c5cb467e777bb6d",
            },
            "add_ie": ["BrightcoveNew"],
        },
        {
            "url": "https://www.skysports.com/watch/video/sports/f1/12160544/abu-dhabi-gp-the-notebook",
            "only_matching": True,
        },
        {
            "url": "https://www.skysports.com/watch/video/tv-shows/12118508/rainford-brent-how-ace-programme-helps",
            "only_matching": True,
        },
    ]


class SkyNewsIE(SkyBaseIE):
    IE_NAME = "sky:news"
    _VALID_URL = r"https?://news\.sky\.com/video/[0-9a-z-]+-(?P<id>[0-9]+)"
    _VIDEO_SITEMAP_INDEX = "https://news.sky.com/sitemap/sitemap-index-video.xml"
    _TESTS = [
        {
            "url": "https://news.sky.com/video/huge-blaze-breaks-out-near-wembley-stadium-13578164",
            "md5": "581de632f1fd9cf72f2ac16745ed6047",
            "info_dict": {
                "id": "ref:56b5e9e8-61c6-4b23-90db-4393ea01d81b",
                "ext": "mp4",
                "title": "Large fire breaks out near Wembley",
                "description": "md5:c9c5dad53753351c890ee75d006c7dc5",
                "uploader_id": "6058004172001",
                "timestamp": 1787928362,
                "upload_date": "20260828",
                "duration": 28.821,
                "thumbnail": r"re:https://videos\.skynews\.com/.+",
                "tags": ["/shape/9:16", "/uk"],
            },
            "add_ie": ["BrightcoveNew"],
        },
        {
            "url": "https://news.sky.com/video/russian-plane-inspected-after-deadly-fire-11712962",
            "skip": "HTTP Error 403",
            "md5": "411e8893fd216c75eaf7e4c65d364115",
            "info_dict": {
                "id": "ref:1ua21xaDE6lCtZDmbYfl8kwsKLooJbNM",
                "ext": "mp4",
                "title": "Russian plane inspected after deadly fire",
                "description": "The Russian Investigative Committee has released video of the wreckage of a passenger plane which caught fire near Moscow.",
                "uploader_id": "6058004172001",
                "timestamp": 1567112345,
                "upload_date": "20190829",
            },
            "add_ie": ["BrightcoveNew"],
        },
    ]

    def _is_akamai_challenge(self, webpage):
        return 'id="sec-if-cpt-container"' in webpage or "scf-akamai-logo" in webpage

    def _widget_url_from_sitemap(self, url, video_id):
        index = self._download_xml(
            self._VIDEO_SITEMAP_INDEX, video_id, note="Downloading video sitemap index", impersonate=True
        )
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        sitemaps = sorted(
            ((el.findtext(f"{ns}lastmod") or "", el.findtext(f"{ns}loc")) for el in index.findall(f"{ns}sitemap")),
            reverse=True,
        )
        page_url = url.split("#")[0].split("?")[0].rstrip("/")
        loc_re = re.compile(
            r"<loc>\s*" + re.escape(page_url) + r"/?\s*</loc>\s*"
            r"<video:video>.*?<video:player_loc[^>]*>\s*([^<\s]+)",
            re.DOTALL,
        )
        for _, sitemap_url in sitemaps[:6]:
            if not sitemap_url:
                continue
            sitemap = self._download_webpage(
                sitemap_url, video_id, fatal=False, impersonate=True, note="Downloading video sitemap"
            )
            if not sitemap:
                continue
            mobj = loc_re.search(sitemap)
            if mobj:
                return url_or_none(mobj.group(1).strip())
        return None

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, impersonate=True)
        entries = self._extract_player_entries(webpage, url)
        if self._is_akamai_challenge(webpage) or not entries:
            widget_url = self._widget_url_from_sitemap(url, video_id)
            if not widget_url:
                raise ExtractorError("This video page is protected by an Akamai bot challenge", expected=True)
            webpage = self._download_webpage(widget_url, video_id, impersonate=True, note="Downloading video widget")
            entries = self._extract_player_entries(webpage, url)
        if not entries:
            raise ExtractorError("Unable to extract video player")
        info = entries[0]
        title = self._og_search_title(webpage, default=None)
        description = strip_or_none(self._og_search_description(webpage, default=None))
        if title:
            info["title"] = title
        if description:
            info["description"] = description
        return info


class SkyNewsStoryIE(SkyBaseIE):
    IE_NAME = "sky:news:story"
    _VALID_URL = r"https?://news\.sky\.com/story/[0-9a-z-]+-(?P<id>[0-9]+)"
    _TEST = {
        "url": "https://news.sky.com/story/budget-2021-chancellor-rishi-sunak-vows-address-will-deliver-strong-economy-fit-for-a-new-age-of-optimism-12445425",
        "skip": "HTTP Error 403",
        "info_dict": {
            "id": "ref:0714acb9-123d-42c8-91b8-5c1bc6c73f20",
            "title": "md5:e408dd7aad63f31a1817bbe40c7d276f",
            "description": "md5:a881e12f49212f92be2befe4a09d288a",
            "ext": "mp4",
            "upload_date": "20211027",
            "timestamp": 1635317494,
            "uploader_id": "6058004172001",
        },
    }

    def _real_extract(self, url):
        article_id = self._match_id(url)
        webpage = self._download_webpage(url, article_id, impersonate=True)
        entries = self._extract_player_entries(webpage, url)
        return self.playlist_result(
            entries,
            article_id,
            self._og_search_title(webpage, default=None),
            self._html_search_meta(["og:description", "description"], webpage),
        )


class SkySportsNewsIE(SkyBaseIE):
    IE_NAME = "sky:sports:news"
    _VALID_URL = r"https?://(?:www\.)?skysports\.com/([^/]+/)*news/\d+/(?P<id>\d+)"
    _TEST = {
        "url": "http://www.skysports.com/golf/news/12176/10871916/dustin-johnson-ready-to-conquer-players-championship-at-tpc-sawgrass",
        "info_dict": {
            "id": "10871916",
            "title": "Dustin Johnson ready to conquer Players Championship at TPC Sawgrass",
            "description": "Dustin Johnson is confident he can continue his dominant form in 2017 by adding the Players Championship to his list of victories.",
        },
        "playlist_count": 2,
    }

    def _real_extract(self, url):
        article_id = self._match_id(url)
        webpage = self._download_webpage(url, article_id)

        entries = self._extract_player_entries(webpage, url)

        return self.playlist_result(
            entries,
            article_id,
            self._og_search_title(webpage),
            self._html_search_meta(["og:description", "description"], webpage),
        )
