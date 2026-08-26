import json
import re

from .common import InfoExtractor
from ..utils import (
    classproperty,
    int_or_none,
    traverse_obj,
    urljoin,
)


class BrainPOPBaseIE(InfoExtractor):
    _NETRC_MACHINE = "brainpop"
    _ORIGIN = ""  # So that _VALID_URL doesn't crash
    _PRODUCT = "bp"
    _ENTITY = "topic"
    _CMS_ASSETS = "https://static.brainpop.com/directus/"
    _LOGIN_ERRORS = {
        1502: "The username and password you entered did not match.",  # LOGIN_FAILED
        1503: "Payment method is expired.",  # LOGIN_FAILED_ACCOUNT_NOT_ACTIVE
        1506: "Your BrainPOP plan has expired.",  # LOGIN_FAILED_ACCOUNT_EXPIRED
        1507: "Terms not accepted.",  # LOGIN_FAILED_TERMS_NOT_ACCEPTED
        1508: "Account not activated.",  # LOGIN_FAILED_SUBSCRIPTION_NOT_ACTIVE
        1512: "The maximum number of devices permitted are logged in with your account right now.",  # LOGIN_FAILED_LOGIN_LIMIT_REACHED
        1513: "You are trying to access your account from outside of its allowed IP range.",  # LOGIN_FAILED_INVALID_IP
        1514: "Individual accounts are not included in your plan. Try again with your shared username and password.",  # LOGIN_FAILED_MBP_DISABLED
        1515: "Account not activated.",  # LOGIN_FAILED_TEACHER_NOT_ACTIVE
        1523: "That username and password won't work on this BrainPOP site.",  # LOGIN_FAILED_NO_ACCESS
        1524: "You'll need to join a class before you can login.",  # LOGIN_FAILED_STUDENT_NO_PERIOD
        1526: "Your account is locked. Reset your password, or ask a teacher or administrator for help.",  # LOGIN_FAILED_ACCOUNT_LOCKED
    }
    _MOVIE_TYPE_FORMATS = {
        "high_resolution": {
            "format_id": "high",
            "quality": 1,
        },
        "low_resolution": {
            "format_id": "low",
            "quality": -1,
        },
        "audio_description": {
            "format_id": "audio_description",
            "format_note": "Audio description",
            "source_preference": -2,
        },
    }

    @classproperty
    def _VALID_URL(cls):
        root = re.escape(cls._ORIGIN).replace(r"https:", r"https?:").replace(r"www\.", r"(?:www\.)?")
        return rf"{root}/(?:topic|lesson|[^/]+/[^/]+)/(?P<id>[^/?#&]+)"

    def _perform_login(self, username, password):
        login_res = self._download_json(
            "https://api.brainpop.com/api/login",
            None,
            data=json.dumps({"username": username, "password": password}).encode(),
            headers={
                "Content-Type": "application/json",
                "Referer": self._ORIGIN,
            },
            note="Logging in",
            errnote="Unable to log in",
            expected_status=400,
        )
        status_code = int_or_none(login_res["status_code"])
        if status_code != 1505:
            message = self._LOGIN_ERRORS.get(status_code) or login_res.get("message")
            self.report_warning(f"Unable to login: {message}" if message else f"Got status code {status_code}")

    def _real_extract(self, url):
        display_id = self._match_id(url)
        movie_data = self._download_json(
            f"https://api.brainpop.com/api/content/{self._PRODUCT}/{self._ENTITY}/{display_id}/movie",
            display_id,
            "Downloading movie data JSON",
            "Unable to download movie data",
        )["data"]

        access = movie_data.get("access") or {}
        if not access.get("allow"):
            reason = access.get("reason") or "This video is not available"
            if "logged" in reason.lower():
                self.raise_login_required(reason, metadata_available=True)
            else:
                self.raise_no_formats(reason, video_id=display_id, expected=True)

        entity = movie_data.get("entity") or {}
        movie = (
            traverse_obj(movie_data, ("feature", "resources", lambda _, v: v.get("type") == "movie", any, {dict})) or {}
        )
        feature_data = movie.get("data") or {}

        formats = []
        for video in traverse_obj(feature_data, ("movies", ..., {dict})):
            filename = video.get("filename")
            if not filename:
                continue
            formats.append(
                {
                    "url": urljoin(self._CMS_ASSETS, filename),
                    "ext": "mp4",
                    **self._MOVIE_TYPE_FORMATS.get(video.get("type"), {}),
                }
            )

        subtitles = {}
        for subtitle in traverse_obj(feature_data, ("subtitles", ..., {dict})):
            filename = subtitle.get("filename")
            if not filename:
                continue
            subtitles.setdefault(subtitle.get("language") or "en", []).append(
                {
                    "url": urljoin(self._CMS_ASSETS, filename),
                }
            )

        thumbnails = []
        for filename in traverse_obj(
            feature_data,
            (
                "thumbnails",
                ...,
                "directus_files_id",
                "filename",
                {str},
            ),
        ):
            thumbnails.append({"url": urljoin(self._CMS_ASSETS, filename)})

        return {
            "id": entity.get("EntryID") or movie.get("EntryID") or display_id,
            "display_id": display_id,
            "title": entity.get("title") or movie.get("title") or feature_data.get("title"),
            "description": entity.get("description") or entity.get("synopsis"),
            "duration": int_or_none(movie.get("play_time")),
            "formats": formats,
            "subtitles": subtitles,
            "thumbnails": thumbnails,
        }


class BrainPOPIE(BrainPOPBaseIE):
    _ORIGIN = "https://www.brainpop.com"
    _PRODUCT = "bp"
    _TESTS = [
        {
            "url": "https://www.brainpop.com/topic/main-idea/",
            "md5": "1109b5abc25c6b5f24aae00b6cb72369",
            "info_dict": {
                "id": "927f970ddd5070b9f733dcb34010ee2a",
                "ext": "mp4",
                "title": "Main Idea",
                "display_id": "main-idea",
                "description": "md5:09d3a52f8487aa80079d1f3d28dd9d8e",
                "duration": 272,
                "thumbnail": r"re:https?://static\.brainpop\.com/directus/.+",
            },
        },
        {
            "url": "https://www.brainpop.com/topic/main-idea/movie",
            "only_matching": True,
        },
        {
            "url": "https://www.brainpop.com/health/conflictresolution/martinlutherkingjr/movie?ref=null",
            "skip": "video gone",
            "md5": "3ead374233ae74c7f1b0029a01c972f0",
            "info_dict": {
                "id": "1f3259fa457292b4",
                "ext": "mp4",
                "title": "Martin Luther King, Jr.",
                "display_id": "martinlutherkingjr",
                "description": "md5:f403dbb2bf3ccc7cf4c59d9e43e3c349",
            },
        },
        {
            "url": "https://www.brainpop.com/science/space/bigbang/",
            "md5": "9a1ff0e77444dd9e437354eb669c87ec",
            "info_dict": {
                "id": "acae52cd48c99acf",
                "ext": "mp4",
                "title": "Big Bang",
                "display_id": "bigbang",
                "description": "md5:3e53b766b0f116f631b13f4cae185d38",
            },
            "skip": "Requires login",
        },
    ]


class BrainPOPJrIE(BrainPOPBaseIE):
    _ORIGIN = "https://jr.brainpop.com"
    _PRODUCT = "bpjr"
    _TESTS = [
        {
            "url": "https://jr.brainpop.com/topic/seasons/",
            "md5": "6080e7e98125c7b0bfc91cd7f64d5968",
            "info_dict": {
                "id": "e96ad134f026e86278cedc61a246fac5",
                "ext": "mp4",
                "title": "Seasons",
                "display_id": "seasons",
                "description": "md5:aa30c4348181b12d0eea29638d2a494e",
                "duration": 250,
            },
        },
        {
            "url": "https://jr.brainpop.com/health/feelingsandsel/emotions/",
            "md5": "04e0561bb21770f305a0ce6cf0d869ab",
            "info_dict": {
                "id": "347",
                "ext": "mp4",
                "title": "Emotions",
                "display_id": "emotions",
            },
            "skip": "Requires login",
        },
        {
            "url": "https://jr.brainpop.com/science/habitats/arctichabitats/",
            "md5": "b0ed063bbd1910df00220ee29340f5d6",
            "info_dict": {
                "id": "29",
                "ext": "mp4",
                "title": "Arctic Habitats",
                "display_id": "arctichabitats",
            },
            "skip": "Requires login",
        },
    ]


class BrainPOPELLIE(BrainPOPBaseIE):
    _ORIGIN = "https://ell.brainpop.com"
    _PRODUCT = "bpell"
    _ENTITY = "lesson"
    _TESTS = [
        {
            "url": "https://ell.brainpop.com/lesson/the-friends/",
            "md5": "a2012700cfb774acb7ad2e8834eed0d0",
            "info_dict": {
                "id": "78137f4a170dc40e9c15740e1956c850",
                "ext": "mp4",
                "title": "Personal Pronouns",
                "display_id": "the-friends",
                "description": "md5:51bfc29d32728098296e486fd6337506",
                "duration": 126,
            },
        },
        {
            "url": "https://ell.brainpop.com/level1/unit1/lesson1/",
            "md5": "a2012700cfb774acb7ad2e8834eed0d0",
            "info_dict": {
                "id": "1",
                "ext": "mp4",
                "title": "Lesson 1",
                "display_id": "lesson1",
                "alt_title": "Personal Pronouns",
            },
            "skip": "URL changed",
        },
        {
            "url": "https://ell.brainpop.com/level3/unit6/lesson5/",
            "md5": "be19c8292c87b24aacfb5fda2f3f8363",
            "info_dict": {
                "id": "101",
                "ext": "mp4",
                "title": "Lesson 5",
                "display_id": "lesson5",
                "alt_title": "Review: Unit 6",
            },
            "skip": "Requires login",
        },
    ]


class BrainPOPEspIE(BrainPOPBaseIE):
    IE_DESC = "BrainPOP Español"
    _ORIGIN = "https://esp.brainpop.com"
    _PRODUCT = "bpesp"
    _TESTS = [
        {
            "url": "https://esp.brainpop.com/topic/ecosistemas/",
            "only_matching": True,
        },
        {
            "url": "https://esp.brainpop.com/ciencia/la_diversidad_de_la_vida/ecosistemas/",
            "skip": "media CDN 503",
            "md5": "cb3f062db2b3c5240ddfcfde7108f8c9",
            "info_dict": {
                "id": "3893",
                "ext": "mp4",
                "title": "Ecosistemas",
                "display_id": "ecosistemas",
                "description": "md5:80fc55b07e241f8c8f2aa8d74deaf3c3",
            },
        },
        {
            "url": "https://esp.brainpop.com/espanol/la_escritura/emily_dickinson/",
            "md5": "98c1b9559e0e33777209c425cda7dac4",
            "info_dict": {
                "id": "7146",
                "ext": "mp4",
                "title": "Emily Dickinson",
                "display_id": "emily_dickinson",
                "description": "md5:2795ad87b1d239c9711c1e92ab5a978b",
            },
            "skip": "Requires login",
        },
    ]


class BrainPOPFrIE(BrainPOPBaseIE):
    IE_DESC = "BrainPOP Français"
    _ORIGIN = "https://fr.brainpop.com"
    _PRODUCT = "bpfr"
    _TESTS = [
        {
            "url": "https://fr.brainpop.com/topic/sources-denergie/",
            "md5": "97e7f48af8af93f8a2be11709f239371",
            "info_dict": {
                "id": "d564f027eae19be981143af01c1b8ac4",
                "ext": "mp4",
                "title": "Sources d'énergie",
                "display_id": "sources-denergie",
                "description": "md5:7eece350f019a21ef9f64d4088b2d857",
                "duration": 272,
            },
        },
        {
            "url": "https://fr.brainpop.com/sciencesdelaterre/energie/sourcesdenergie/",
            "skip": "URL changed",
            "md5": "97e7f48af8af93f8a2be11709f239371",
            "info_dict": {
                "id": "1651",
                "ext": "mp4",
                "title": "Sources d'énergie",
                "display_id": "sourcesdenergie",
                "description": "md5:7eece350f019a21ef9f64d4088b2d857",
            },
        },
        {
            "url": "https://fr.brainpop.com/francais/ecrire/plagiat/",
            "md5": "0cf2b4f89804d0dd4a360a51310d445a",
            "info_dict": {
                "id": "5803",
                "ext": "mp4",
                "title": "Plagiat",
                "display_id": "plagiat",
                "description": "md5:4496d87127ace28e8b1eda116e77cd2b",
            },
            "skip": "Requires login",
        },
    ]


class BrainPOPIlIE(BrainPOPBaseIE):
    IE_DESC = "BrainPOP Hebrew"
    _ORIGIN = "https://il.brainpop.com"
    _PRODUCT = "bphe"
    _TESTS = [
        {
            "url": "https://il.brainpop.com/category_9/subcategory_150/subjects_3782/",
            "md5": "9e4ea9dc60ecd385a6e5ca12ccf31641",
            "info_dict": {
                "id": "3782",
                "ext": "mp4",
                "title": "md5:e993632fcda0545d9205602ec314ad67",
                "display_id": "subjects_3782",
                "description": "md5:4cc084a8012beb01f037724423a4d4ed",
            },
            "skip": "site moved to brainpop.co.il",
        }
    ]
