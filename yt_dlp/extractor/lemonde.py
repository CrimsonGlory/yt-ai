from .common import InfoExtractor
from ..utils import extract_attributes, get_element_html_by_class


class LemondeIE(InfoExtractor):
    _VALID_URL = r"https?://(?:.+?\.)?lemonde\.fr/(?:[^/]+/)*(?P<id>[^/]+)\.html"
    _TESTS = [
        {
            "url": "https://www.lemonde.fr/videos/video/2026/08/27/caen-un-automobiliste-fonce-sur-un-groupe-de-pietons_6758452_1669088.html",
            "md5": "c9247c6e21f51a2abd0bedee4cae85e7",
            "info_dict": {
                "id": "xb19dqm",
                "ext": "mp4",
                "title": "Un automobiliste fonce sur des piétons à Caen, voici ce que l'on sait",
                "description": "md5:38bc64d41444b80ed434a54240b942f1",
                "thumbnail": r"re:https?://s[12]\.dmcdn\.net/v/.+",
                "duration": 61,
                "timestamp": 1787828789,
                "upload_date": "20260827",
                "uploader": "Le Monde",
                "uploader_id": "x1wd0c",
                "view_count": int,
                "like_count": int,
                "age_limit": 0,
                "tags": list,
            },
            "add_ie": ["Dailymotion"],
            # HLS --test only fetches the fMP4 init fragment (~1KB), below the default 10KB check
            "file_minsize": None,
        },
        {
            "url": "http://www.lemonde.fr/police-justice/video/2016/01/19/comprendre-l-affaire-bygmalion-en-cinq-minutes_4849702_1653578.html",
            "skip": "Original Digiteka embed replaced by YouTube",
            "md5": "da120c8722d8632eec6ced937536cc98",
            "info_dict": {
                "id": "lqm3kl",
                "ext": "mp4",
                "title": "Comprendre l'affaire Bygmalion en 5 minutes",
                "thumbnail": r"re:^https?://.*\.jpg",
                "duration": 309,
                "upload_date": "20160119",
                "timestamp": 1453194778,
                "uploader_id": "3pmkp",
            },
        },
        {
            # standard iframe embed
            "url": "http://www.lemonde.fr/les-decodeurs/article/2016/10/18/tout-comprendre-du-ceta-le-petit-cousin-du-traite-transatlantique_5015920_4355770.html",
            "only_matching": True,
        },
        {
            "url": "http://redaction.actu.lemonde.fr/societe/video/2016/01/18/calais-debut-des-travaux-de-defrichement-dans-la-jungle_4849233_3224.html",
            "only_matching": True,
        },
        {
            # YouTube embeds
            "url": "http://www.lemonde.fr/pixels/article/2016/12/09/pourquoi-pewdiepie-superstar-de-youtube-a-menace-de-fermer-sa-chaine_5046649_4408996.html",
            "only_matching": True,
        },
    ]

    _PROVIDERS = {
        "dailymotion": "https://www.dailymotion.com/video/{}",
        "youtube": "https://www.youtube.com/watch?v={}",
        "digiteka": "https://www.ultimedia.com/default/index/videogeneric/id/{}",
        "ultimedia": "https://www.ultimedia.com/default/index/videogeneric/id/{}",
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id, impersonate=True)

        digiteka_url = self._proto_relative_url(
            self._search_regex(
                r'url\s*:\s*(["\'])(?P<url>(?:https?://)?//(?:www\.)?(?:digiteka\.net|ultimedia\.com)/deliver/.+?)\1',
                webpage,
                "digiteka url",
                group="url",
                default=None,
            )
        )

        if digiteka_url:
            return self.url_result(digiteka_url, "Digiteka")

        player = get_element_html_by_class("js_player", webpage)
        if player:
            attrs = extract_attributes(player)
            video_id = attrs.get("data-id")
            embed_url = self._PROVIDERS.get(attrs.get("data-provider"), "").format(video_id or "")
            if video_id and embed_url:
                return self.url_result(embed_url)

        return self.url_result(url, "Generic")
