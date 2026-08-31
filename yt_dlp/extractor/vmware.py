from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import smuggle_url
from ..utils.traversal import traverse_obj


class VMwareIE(InfoExtractor):
    IE_NAME = 'vmware'
    IE_DESC = 'VMware / Broadcom video library'
    _VALID_URL = r'https?://(?:www\.)?vmware\.com/(?:explore/(?:video-library/)?video|video)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.vmware.com/video/6403236648112',
        'md5': '698377974d2d42cb535587ac35434a2d',
        'info_dict': {
            'id': '6403236648112',
            'ext': 'mp4',
            'title': 'VCF 9.1 Upgrade Planning Tool | Break It Down',
            'description': 'md5:22527da7f406b473b32ee93de8c7f363',
            'duration': 131.968,
            'timestamp': 1786491483,
            'upload_date': '20260811',
            'uploader_id': '6415665063001',
            'tags': ['break it down', 'james gottry', 'vcf', 'upgrade planning'],
            'thumbnail': r're:https?://.+\.jpg',
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://www.vmware.com/explore/video/6377042537112',
        'only_matching': True,
    }, {
        'url': 'https://www.vmware.com/explore/video-library/video/6360760233112',
        'only_matching': True,
    }]

    _PLAYERS = {
        '6415665063001': '83iWkhhmz',  # VMware
        '6164421911001': 'lUBT2rAMW',  # Explore
    }

    def _resolve_account(self, url, video_id):
        data = self._download_json(
            'https://www.vmware.com/get-st', video_id,
            'Downloading video metadata', fatal=False, query={
                'document_types[]': 'videos',
                'filters[videos][external_id]': video_id,
                'page': '1',
                'per_page': '1',
            })
        account_id = traverse_obj(data, ('records', 'videos', 0, 'account_id', {str}))
        if account_id in self._PLAYERS:
            return account_id

        if '/explore/' in url:
            return '6164421911001'
        return '6415665063001'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        account_id = self._resolve_account(url, video_id)
        player_id = self._PLAYERS.get(account_id) or 'default'
        bc_url = f'https://players.brightcove.net/{account_id}/{player_id}_default/index.html?videoId={video_id}'
        return self.url_result(smuggle_url(bc_url, {'referrer': url}), BrightcoveNewIE, video_id)
