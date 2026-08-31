import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    join_nonempty,
    mimetype2ext,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class OyezIE(InfoExtractor):
    IE_NAME = "oyez"
    IE_DESC = "Oyez"
    _API_BASE = "https://api.oyez.org"
    _VALID_URL = [
        r"https?://api\.oyez\.org/case_media/(?P<kind>oral_argument_audio|opinion_announcement_audio)/(?P<id>\d+)",
        r"https?://apps\.oyez\.org/player/?(?:#|%23).*/(?P<kind>oral_argument_audio|opinion_announcement_audio)/(?P<id>\d+)",
    ]
    _TESTS = [
        {
            "url": "https://api.oyez.org/case_media/oral_argument_audio/24834",
            "md5": "a9d5d41aeda73455dcf43a7f8783cef7",
            "info_dict": {
                "id": "24834",
                "ext": "mp3",
                "title": "Oral Argument - April 23, 2019",
                "duration": 3315.075,
                "timestamp": 1555977600,
                "upload_date": "20190423",
                "vcodec": "none",
            },
        },
        {
            "url": "https://api.oyez.org/case_media/opinion_announcement_audio/24900",
            "only_matching": True,
        },
        {
            "url": "https://apps.oyez.org/player/#/roberts6/oral_argument_audio/24834",
            "only_matching": True,
        },
    ]

    def _extract_media_formats(self, audio):
        formats = []
        for media in traverse_obj(audio, ("media_file", ..., {dict})) or []:
            media_url = url_or_none(media.get("href"))
            if not media_url:
                continue
            ext = mimetype2ext(media.get("mime")) or determine_ext(media_url)
            if ext == "m3u8":
                # HLS objects on the public bucket return 403
                continue
            formats.append(
                {
                    "url": media_url,
                    "format_id": ext,
                    "ext": ext,
                    "filesize": int_or_none(media.get("size")),
                    "vcodec": "none",
                    "acodec": "mp3" if ext == "mp3" else None,
                }
            )
        # OGG objects are also 403; prefer the public MP3 delivery files
        mp3_formats = [f for f in formats if f.get("ext") == "mp3"]
        return mp3_formats or formats

    def _extract_audio_entry(self, audio_id, kind, case=None, fatal=True):
        audio = self._download_json(f"{self._API_BASE}/case_media/{kind}/{audio_id}", audio_id, fatal=fatal)
        if not audio:
            return None
        if audio.get("unavailable"):
            if fatal:
                self.raise_no_formats("This recording is unavailable", expected=True, video_id=audio_id)
            return None

        formats = self._extract_media_formats(audio)
        if not formats:
            if fatal:
                self.raise_no_formats("No public audio formats", expected=True, video_id=audio_id)
            return None

        title = traverse_obj(audio, (("display_title", "title"), {str}, any))
        case_name = traverse_obj(case, ("name", {str}))
        stops = [
            s
            for s in traverse_obj(audio, ("transcript", "sections", ..., "stop", {float_or_none})) or []
            if s is not None
        ]
        date_mobj = re.search(r"([A-Za-z]+ \d{1,2}, \d{4})", title or "")

        return {
            "id": str_or_none(audio.get("id")) or str(audio_id),
            "title": join_nonempty(case_name, title, delim=" - ") or None,
            "formats": formats,
            "duration": max(stops) if stops else None,
            "timestamp": unified_timestamp(date_mobj.group(1)) if date_mobj else None,
            "series": case_name,
            "description": self._case_description(case),
            "vcodec": "none",
        }

    @staticmethod
    def _case_description(case):
        if not case:
            return None
        return (
            join_nonempty(
                traverse_obj(case, ("description", {str})),
                traverse_obj(case, ("facts_of_the_case", {clean_html})),
                traverse_obj(case, ("question", {clean_html})),
                delim="\n\n",
            )
            or None
        )

    def _real_extract(self, url):
        kind, audio_id = self._match_valid_url(url).group("kind", "id")
        return self._extract_audio_entry(audio_id, kind)


class OyezCaseIE(OyezIE):
    IE_NAME = "oyez:case"
    IE_DESC = "Oyez case"
    _VALID_URL = r"https?://(?:www\.|api\.)?oyez\.org/cases?/(?P<term>\d{4})/(?P<id>[^/?#]+)"
    _TESTS = [
        {
            # Single oral argument (no opinion announcement)
            "url": "https://www.oyez.org/cases/2019/18-328",
            "md5": "e269fadc6d39c4376dc201f864b48a5b",
            "info_dict": {
                "id": "25084",
                "ext": "mp3",
                "title": "Rotkiske v. Klemm - Oral Argument - October 16, 2019",
                "description": "md5:02392d407d30a29d2e30c9cd0caffec4",
                "duration": 3438.52,
                "timestamp": 1571184000,
                "upload_date": "20191016",
                "series": "Rotkiske v. Klemm",
                "vcodec": "none",
            },
        },
        {
            "url": "https://www.oyez.org/cases/2018/17-9560",
            "info_dict": {
                "id": "2018-17-9560",
                "title": "Rehaif v. United States",
                "description": "md5:ecc6aa034792471d7335af72b4dddb87",
            },
            "playlist_count": 2,
        },
        {
            "url": "https://www.oyez.org/cases/1965/14_orig",
            "only_matching": True,
        },
        {
            "url": "https://api.oyez.org/cases/2018/17-9560",
            "only_matching": True,
        },
        {
            "url": "https://www.oyez.org/case/2018/17-9560",
            "only_matching": True,
        },
    ]

    def _real_extract(self, url):
        term, display_id = self._match_valid_url(url).group("term", "id")
        case = self._download_json(f"{self._API_BASE}/cases/{term}/{display_id}", display_id)

        entries = []
        for kind, key in (
            ("oral_argument_audio", "oral_argument_audio"),
            ("opinion_announcement_audio", "opinion_announcement"),
        ):
            for item in traverse_obj(case, (key, ..., {dict})) or []:
                if item.get("unavailable"):
                    continue
                audio_id = str_or_none(item.get("id"))
                if not audio_id:
                    continue
                href = item.get("href") or ""
                if "opinion_announcement" in href:
                    item_kind = "opinion_announcement_audio"
                elif "oral_argument" in href:
                    item_kind = "oral_argument_audio"
                else:
                    item_kind = kind
                entry = self._extract_audio_entry(audio_id, item_kind, case, fatal=False)
                if entry:
                    entries.append(entry)

        if not entries:
            raise ExtractorError("No public audio is available for this case", expected=True)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, f"{term}-{display_id}", traverse_obj(case, ("name", {str})), self._case_description(case)
        )
