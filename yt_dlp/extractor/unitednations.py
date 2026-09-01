from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import (
    ExtractorError,
    merge_dicts,
    parse_iso8601,
)


class UnitedNationsWebTvIE(InfoExtractor):
    _VALID_URL = r'https?://webtv\.un\.org/(?:ar|zh|en|fr|ru|es)/asset/\w+/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://webtv.un.org/en/asset/k1o/k1o7stmi6p',
        'md5': 'b2f8b3030063298ae841b4b7ddc01477',
        'info_dict': {
            'id': '1_o7stmi6p',
            'ext': 'mp4',
            'title': 'António Guterres (Secretary-General) on Israel and Iran - Security Council, 9939th meeting',
            'thumbnail': 'http://cfvod.kaltura.com/p/2503451/sp/250345100/thumbnail/entry_id/1_o7stmi6p/version/100021',
            'uploader_id': 'evgeniia.alisova@un.org',
            'upload_date': '20250620',
            'timestamp': 1750430976,
            'duration': 234,
            'view_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        partner_id = self._html_search_regex(
            r'partnerId:\s*(\d+)', webpage, 'partner_id')
        entry_id = self._html_search_regex(
            r'const\s+kentryID\s*=\s*["\'](\w+)["\']', webpage, 'kentry_id')

        return self.url_result(f'kaltura:{partner_id}:{entry_id}', KalturaIE)


class UnitedNationsMediaIE(InfoExtractor):
    _VALID_URL = r'https?://media\.un\.org/(?:avlibrary|unifeed)/(?:[a-z]{2}/)?asset/(?:[^/#?]+/)?(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://media.un.org/avlibrary/en/asset/d362/d3621638',
        'md5': '07bdbf7b6c93fbff8b7b4ba13e3fcc60',
        'info_dict': {
            'id': '1_kk266ab7',
            'ext': 'mp4',
            'title': 'Kyrgyzstan, Libya, Nepal & other topics - Daily Press Briefing',
            'thumbnail': r're:https?://.+/thumbnail/.+',
            'uploader_id': 'UNWebTV_New_York',
            'upload_date': '20260831',
            'timestamp': 1788191167,
            'duration': 1582,
            'view_count': int,
        },
    }, {
        'url': 'https://media.un.org/unifeed/en/asset/d362/d3621668',
        'md5': 'd87b3a563d73c115cc4d15abf3536f01',
        'info_dict': {
            'id': 'd3621668',
            'ext': 'mp4',
            'title': 'UN / SEA LEVEL RISE REPORT',
            'description': 'md5:62bfbfe073505ba706e3c555b2f4ddb4',
            'thumbnail': r're:https?://.+\.jpg',
            'timestamp': 1788177600,
            'upload_date': '20260831',
        },
    }, {
        'url': 'https://media.un.org/unifeed/en/asset/u130/u130625d',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        entry_id = self._search_regex(
            r'''(?x)(?:entryId\s*:\s*|const\s+kentryID\s*=\s*)["'](\w+)["']''',
            webpage, 'entry_id', default=None)
        if entry_id:
            partner_id = self._search_regex(
                r'partnerId:\s*(\d+)', webpage, 'partner_id')
            return self.url_result(f'kaltura:{partner_id}:{entry_id}', KalturaIE)

        info = {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'timestamp': parse_iso8601(self._html_search_regex(
                r'<time[^>]+datetime="([^"]+)"', webpage, 'timestamp', default=None)),
        }

        jwplayer_data = self._find_jwplayer_data(webpage, video_id)
        if jwplayer_data:
            return merge_dicts(info, self._parse_jwplayer_data(
                jwplayer_data, video_id, require_title=False))

        video_url = self._search_regex(
            r'file:\s*"(https?://[^"]+\.mp4)"', webpage, 'video url', default=None)
        if video_url:
            return {
                **info,
                'url': video_url,
                'ext': 'mp4',
            }

        raise ExtractorError('Unable to extract Kaltura or JWPlayer media', expected=True)

