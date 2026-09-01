from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import (
    ExtractorError,
    traverse_obj,
)


class IWitnessIE(InfoExtractor):
    IE_DESC = 'USC Shoah Foundation IWitness'
    _VALID_URL = r'https?://(?:www\.)?iwitness\.usc\.edu/sites/(?!360(?:/|$))(?P<id>[\w-]+)/?(?:[?#]|$)'
    _PARTNER_ID = '27654'
    _CMS_SPACE = 'r2fjqekz37jz'
    _CMS_TOKEN = 'jAXPET4KQX_GAt-sLwRdHwMGDME9ren-MM9jcFr-WSQ'
    _TESTS = [{
        'url': 'https://iwitness.usc.edu/sites/tattooedtorah',
        'md5': 'ed8409d7a789f74eb3cb3b8f3664c953',
        'info_dict': {
            'id': '1_4c4hnnkv',
            'ext': 'mp4',
            'title': 'The Tattooed Torah_ENGLISH_Web_UnWatermarked_Vimeo',
            'uploader_id': 'sfi.kaltura@gmail.com',
            'upload_date': '20210121',
            'timestamp': 1611188411,
            'duration': 1273,
            'view_count': int,
            'thumbnail': r're:https?://cfvod\.kaltura\.com/.+',
        },
    }, {
        'url': 'https://iwitness.usc.edu/sites/theredscarffilm',
        'only_matching': True,
    }, {
        'url': 'https://iwitness.usc.edu/sites/tattooedtorah/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        site_id = self._match_id(url)
        cms = self._download_json(
            f'https://cdn.contentful.com/spaces/{self._CMS_SPACE}/environments/master/entries',
            site_id, 'Downloading IWitness CMS JSON', query={
                'skip': '0',
                'limit': '1',
                'content_type': 'section',
                'fields.name': f'iwitness://partnership#{site_id}',
                'fields.domain': 'iwitness.partnership',
                'include': '5',
                'access_token': self._CMS_TOKEN,
            })
        component_ids = set(traverse_obj(cms, (
            'items', 0, 'fields', 'components', ..., 'sys', 'id', {str})))
        entry_id = traverse_obj(cms, (
            'includes', 'Entry',
            lambda _, v: traverse_obj(v, ('sys', 'id', {str})) in component_ids,
            'fields', 'entryID', {str}, any))
        if not entry_id:
            raise ExtractorError(
                'No public Kaltura video is embedded on this IWitness page', expected=True)

        return self.url_result(
            f'kaltura:{self._PARTNER_ID}:{entry_id}', ie=KalturaIE, video_id=entry_id)
