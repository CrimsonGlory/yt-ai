from .common import InfoExtractor
from ..utils import (
    js_to_json,
    str_or_none,
    traverse_obj,
)


class RDSIE(InfoExtractor):
    IE_DESC = 'RDS.ca'
    _GEO_COUNTRIES = ['CA']
    _VALID_URL = [
        r'https?://(?:www\.)?rds\.ca/(?:[^/?#]+/)*vid(?:[eé]|%C3%A9)os/(?:[^/?#]+/)*(?P<id>[^/?#]+)/?(?:[?#]|$)',
        r'https?://(?:www\.)?rds\.ca/emissions/[^/?#]+/\d{4}/\d{2}/\d{2}/(?P<id>[^/?#]+)/?(?:[?#]|$)',
    ]

    _TESTS = [{
        'url': 'https://www.rds.ca/videos/2025/09/17/la-f1-lautre-amour-de-pierre-houde/',
        'md5': '8042381a9ae3e00297b945a68d41f246',
        'info_dict': {
            'id': '3219322',
            'ext': 'mp4',
            'display_id': 'la-f1-lautre-amour-de-pierre-houde',
            'title': "La F1 : l'autre amour de Pierre Houde",
            'description': "À l'Antichambre, François Dumontier et Bertrand Houle rejoignent Pierre Houde pour rendre hommage à ses 50 ans de carrière.",
            'timestamp': 1757995200,
            'upload_date': '20250916',
            'duration': 642.81,
            'thumbnail': r're:https?://images2\.9c9media\.com/.+',
            'series': 'RDS 2025-9',
            'season': '1',
            'season_number': 1,
            'season_id': '97543',
            'tags': ['Pierre Houde', '50 ans', 'Antichambre'],
            'categories': [],
        },
        'params': {'format': 'bv'},
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        # has two 9c9media ContentPackages, the web player selects the first ContentPackage
        'url': 'https://www.rds.ca/videos/Hockey/NationalHockeyLeague/teams/9/forum-du-5-a-7-jesperi-kotkaniemi-de-retour-de-finlande-3.1377606',
        'skip': 'video gone',
        'info_dict': {
            'id': '2083309',
            'display_id': 'forum-du-5-a-7-jesperi-kotkaniemi-de-retour-de-finlande',
            'ext': 'flv',
            'title': 'Forum du 5 à 7 : Kotkaniemi de retour de Finlande',
            'description': 'md5:83fa38ecc4a79b19e433433254077f25',
            'timestamp': 1606129030,
            'upload_date': '20201123',
            'duration': 773.039,
        },
    }, {
        'url': 'http://www.rds.ca/vid%C3%A9os/un-voyage-positif-3.877934',
        'only_matching': True,
    }, {
        'url': 'https://www.rds.ca/hockey/canadiens/videos/2026/08/27/du-golf-un-helicoptere-militaire-et-des-pitous-pour-suzuki/',
        'only_matching': True,
    }, {
        'url': 'https://www.rds.ca/emissions/le-5-a-7/2025/09/17/montreal-voulait-sa-course-sprint-des-2020/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id, destination = self._extract_axis_ids(webpage, display_id)

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'display_id': display_id,
            'url': f'9c9media:{destination}:{video_id}',
            'ie_key': 'NineCNineMedia',
        }

    def _extract_axis_ids(self, webpage, display_id):
        embed_url = self._search_regex(
            r'(https?://embed\.jasperplayer\.com/\?[^"\'<>]+)',
            webpage, 'jasper embed url', default=None)
        if embed_url:
            video_id = self._search_regex(r'contentId=(\d+)', embed_url, 'content id')
            destination = self._search_regex(
                r'destination=([^&]+)', embed_url, 'destination', default='rds_web')
            return video_id, destination

        fusion = self._search_json(
            r'Fusion\.globalContent\s*=', webpage, 'fusion content',
            display_id, default={})
        video_id = str_or_none(
            traverse_obj(fusion, ('additional_properties', 'axisId'))
            or traverse_obj(fusion, ('source', 'source_id')))
        if video_id:
            return video_id, 'rds_web'

        item = self._parse_json(self._search_regex(
            r'(?s)itemToPush\s*=\s*({.+?});', webpage, 'item'), display_id, js_to_json)
        return str(item['id']), 'rds_web'
