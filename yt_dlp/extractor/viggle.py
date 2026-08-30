from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    str_or_none,
    strip_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ViggleIE(InfoExtractor):
    IE_DESC = 'Viggle'
    _VALID_URL = r'https?://(?:www\.)?viggle\.ai/(?:s|share|meme/app/share)/(?P<id>[\da-fA-F]{8}-(?:[\da-fA-F]{4}-){3}[\da-fA-F]{12})'
    _TESTS = [{
        'url': 'https://viggle.ai/s/0bb30ee8-c805-4246-81fa-ae9c4f1958f2',
        'md5': '48d10a2551da64a441c36080ad190819',
        'info_dict': {
            'id': '0bb30ee8-c805-4246-81fa-ae9c4f1958f2',
            'ext': 'mp4',
            'title': 'This video sucks #dance',
            'description': 'md5:17f5c191d913f0826e5fc5d9bbb02365',
            'thumbnail': 'https://cdn.viggle.ai/template/1751828823149-f21d9ff3-3b41-4ce2-9cda-92561697a1f7.jpg',
            'duration': 32.880204,
            'timestamp': 1751828946,
            'upload_date': '20250706',
            'like_count': int,
            'comment_count': int,
            'uploader': 'randompersonrr',
            'uploader_id': 'bd0ae4bb-671a-4cc4-a2d9-7f288de28105',
            'width': 527,
            'height': 966,
            'tags': ['#dance'],
            'age_limit': 0,
        },
    }, {
        'url': 'https://viggle.ai/share/0bb30ee8-c805-4246-81fa-ae9c4f1958f2',
        'only_matching': True,
    }, {
        'url': 'https://viggle.ai/meme/app/share/0bb30ee8-c805-4246-81fa-ae9c4f1958f2',
        'only_matching': True,
    }, {
        'url': 'https://viggle.ai/s/9b8dd99d-1b54-4c7f-b440-997caea783a9',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api = self._download_json(
            'https://viggle.ai/api/share/video-task', video_id,
            query={'id': video_id}, impersonate=True,
            headers={
                'Accept': 'application/json',
                'Referer': f'https://viggle.ai/s/{video_id}',
            })
        if traverse_obj(api, 'code') not in (0, None):
            raise ExtractorError(
                traverse_obj(api, (('reason', 'message'), {str}, any)) or 'Viggle API error',
                expected=True)

        data = traverse_obj(api, ('data', {dict}))
        if not data:
            raise ExtractorError('Unable to extract Viggle video', expected=True)

        video_url = traverse_obj(data, ('result', {url_or_none}))
        if not video_url:
            self.raise_no_formats('No video URL', expected=True, video_id=video_id)

        title = strip_or_none(''.join(traverse_obj(
            data, ('descParts', ..., 'value', {str}), default=[]))) or traverse_obj(
            data, (('name', {str}), ('rap', 'title', {str})), get_all=False) or video_id

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'age_limit': 18 if traverse_obj(data, 'nsfwType') else 0,
            **traverse_obj(data, {
                'description': ((('description', {str}), ('rap', 'lyrics', {str})), filter, any),
                'thumbnail': ('resultCover', {url_or_none}),
                'duration': ('videoDuration', {float_or_none}),
                'timestamp': ((('postedAt', {parse_iso8601}), ('createdAt', {parse_iso8601})), any),
                'like_count': ('likedCount', {int_or_none}),
                'comment_count': ('commentCount', {int_or_none}),
                'uploader': ('user', ('nickname', 'username'), {str}, any),
                'uploader_id': ('user', 'id', {str_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'tags': ('descParts', lambda _, v: v.get('type') == 1, 'value', {str}),
            }),
        }
