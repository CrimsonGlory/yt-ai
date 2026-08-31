from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class BaoMoiIE(InfoExtractor):
    IE_NAME = 'baomoi'
    IE_DESC = 'Báo Mới'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?baomoi\.com/
        (?:
            (?:[^/?#]+/)?(?:s/)?c/
            |(?:[^/?#]+-)?[cr]
        )(?P<id>\d+)\.epi
    '''
    _API_URL = 'https://w-api.baomoi.com/api/v1/page/get/content-detail'
    _TESTS = [
        {
            'url': 'https://baomoi.com/thu-tuyet-menh-cua-tgd-cong-ty-dang-kiem-nghi-tu-tu-o-quang-ninh/c/46255067.epi',
            'md5': 'e6446f0bf425f71ead36b0040b2e24de',
            'info_dict': {
                'id': '46255067',
                'ext': 'mp4',
                'title': 'Thư tuyệt mệnh của TGĐ Công ty đăng kiểm nghi tự tử ở Quảng Ninh',
                'description': 'md5:634648a9f8216e63961a1ec82f518d1d',
                'thumbnail': r're:https?://photo-baomoi\.bmcdn\.me/.+',
                'duration': 59,
                'timestamp': 1688353802,
                'upload_date': '20230703',
                'uploader': 'Báo Tri thức & Cuộc sống',
                'uploader_id': '180',
                'like_count': int,
                'tags': 'count:20',
                'categories': ['Giao thông'],
            },
        },
        {
            'url': 'https://baomoi.com/cau-treo-sap-ngay-trong-ngay-khanh-thanh-nguoi-dan-roi-xuong-song-c55955177.epi',
            'md5': '7dfc30b0fd8bd341950bc32d392ef406',
            'info_dict': {
                'id': '55955177',
                'ext': 'mp4',
                'title': 'Cầu treo sập ngay trong ngày khánh thành, người dân rơi xuống sông',
                'description': 'Đây là khoảnh khắc một cây cầu treo bất ngờ bị sập trong ngày cắt băng khánh thành ở Indonesia.',
                'thumbnail': r're:https?://photo-baomoi\.bmcdn\.me/.+',
                'duration': 55,
                'timestamp': 1788202800,
                'upload_date': '20260831',
                'uploader': 'Tạp chí Người Đưa Tin',
                'uploader_id': '296',
                'like_count': int,
                'tags': list,
                'categories': ['Giao thông'],
            },
        },
        {
            'url': 'https://baomoi.com/cau-treo-sap-ngay-trong-ngay-khanh-thanh-nguoi-dan-roi-xuong-song-r55955177.epi',
            'only_matching': True,
        },
        {
            'url': 'https://baomoi.com/c55955177.epi',
            'only_matching': True,
        },
        {
            'url': 'https://baomoi.com/s/c/55955177.epi',
            'only_matching': True,
        },
        {
            'url': 'https://www.baomoi.com/thu-tuyet-menh-cua-tgd-cong-ty-dang-kiem-nghi-tu-tu-o-quang-ninh-c46255067.epi',
            'only_matching': True,
        },
    ]

    def _extract_content(self, url, video_id):
        content = traverse_obj(
            self._download_json(self._API_URL, video_id, query={'id': video_id}, fatal=False),
            ('data', 'content', {dict}),
        )
        if traverse_obj(content, 'bodys'):
            return content

        webpage = self._download_webpage(url, video_id)
        content = (
            traverse_obj(
                self._search_nextjs_data(webpage, video_id, default={}),
                ('props', 'pageProps', 'resp', 'data', 'content', {dict}),
            )
            or {}
        )
        if traverse_obj(content, 'bodys'):
            return content

        canonical = urljoin(url, content.get('url'))
        if canonical and canonical != url:
            webpage = self._download_webpage(canonical, video_id, note='Downloading canonical article', fatal=False)
            if webpage:
                content = (
                    traverse_obj(
                        self._search_nextjs_data(webpage, video_id, default={}),
                        ('props', 'pageProps', 'resp', 'data', 'content', {dict}),
                    )
                    or content
                )
        return content or {}

    def _extract_formats(self, video, video_id):
        formats = []
        media_url = url_or_none(video.get('content')) or url_or_none(video.get('originUrl'))
        if not media_url:
            return formats

        ext = determine_ext(media_url, 'mp4')
        if ext == 'm3u8':
            return self._extract_m3u8_formats(media_url, video_id, 'mp4', m3u8_id='hls', fatal=False) or []

        height = int_or_none(self._search_regex(r'/(\d+)/[^/?#]+\.mp4', media_url, 'height', default=None))
        formats.append(
            {
                'url': media_url,
                'format_id': 'http',
                'ext': ext,
                'width': int_or_none(video.get('width')),
                'height': height or int_or_none(video.get('height')),
                'http_headers': {'Referer': 'https://baomoi.com/'},
            },
        )
        return formats

    def _parse_video(self, video, video_id, content):
        formats = self._extract_formats(video, video_id)
        if not formats:
            return None
        return {
            'id': video_id,
            'formats': formats,
            'duration': traverse_obj(video, ('duration', {int_or_none})),
            'thumbnail': (
                traverse_obj(video, ('poster', {url_or_none})) or traverse_obj(content, ('thumb', {url_or_none}))
            ),
            **traverse_obj(
                content,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                    'timestamp': (('publishedDate', 'date'), {int_or_none}, any),
                    'like_count': ('totalLike', {int_or_none}),
                    'uploader': ('publisher', 'name', {str}),
                    'uploader_id': ('publisher', 'id', {str_or_none}),
                    'tags': ('tags', ..., 'name', {str}),
                    'categories': ('category', 'name', {str}, all),
                },
            ),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        content = self._extract_content(url, video_id)
        videos = traverse_obj(content, ('bodys', lambda _, v: v['type'] == 'video', {dict}))

        entries = []
        for idx, video in enumerate(videos, 1):
            entry_id = video_id if len(videos) == 1 else f'{video_id}-{idx}'
            entry = self._parse_video(video, entry_id, content)
            if entry:
                entries.append(entry)

        if not entries:
            self.raise_no_formats('This article does not contain a video', expected=True, video_id=video_id)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries,
            video_id,
            traverse_obj(content, ('title', {str})),
            traverse_obj(content, ('description', {str})),
            multi_video=True,
        )
