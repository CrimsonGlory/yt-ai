import re

from .naver import NaverBaseIE
from ..utils import (
    ExtractorError,
    extract_attributes,
    get_elements_html_by_class,
    int_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class NaverBlogIE(NaverBaseIE):
    IE_NAME = 'Naver:blog'
    IE_DESC = 'Naver Blog'
    _VALID_URL = [
        r'https?://(?:m\.)?blog\.naver\.com/(?P<blog_id>[\w.-]+)/(?P<log_no>\d+)',
        (r'https?://(?:m\.)?blog\.naver\.com/PostView\.(?:naver|nhn)\?'
         r'(?=[^#]*\bblogId=(?P<blog_id>[\w.-]+))(?=[^#]*\blogNo=(?P<log_no>\d+))'),
    ]
    _TESTS = [{
        'url': 'https://blog.naver.com/starbomb1/220025110521',
        'md5': '80cc92df611afc3cdf6784844024c0af',
        'info_dict': {
            'id': '0FD255D1DD34F5B96A679B09557FB349DE0B',
            'ext': 'mp4',
            'title': '13 Guardians 리뷰',
            'description': '맵 이름:13 Guardians UFO 아슬아슬;; 그런데 비밀길인가요...? 그래도 난이도는 전체적으로 쉬웠습니...',
            'thumbnail': r're:https?://.+\.jpg',
            'uploader': 'StarBomb',
            'uploader_id': 'starbomb1',
            'uploader_url': 'https://blog.naver.com/starbomb1',
            'timestamp': 1402302436,
            'upload_date': '20140609',
            'view_count': int,
        },
    }, {
        'url': 'https://blog.naver.com/korovo/224289487483',
        'info_dict': {
            'id': 'korovo_224289487483',
            'title': '구글 플로우 Google Flow AI 영상 생성 동영상 만들기',
            'description': str,
        },
        'playlist_count': 2,
        'params': {'skip_download': True},
    }, {
        'url': 'https://m.blog.naver.com/starbomb1/220025110521',
        'only_matching': True,
    }, {
        'url': 'https://blog.naver.com/PostView.naver?blogId=starbomb1&logNo=220025110521',
        'only_matching': True,
    }, {
        'url': 'https://blog.naver.com/PostView.naver?logNo=220025110521&blogId=starbomb1',
        'only_matching': True,
    }, {
        'url': 'https://m.blog.naver.com/PostView.naver?blogId=starbomb1&logNo=220025110521',
        'only_matching': True,
    }, {
        'url': 'http://blog.naver.com/PostView.nhn?blogId=starbomb1&logNo=220025110521',
        'only_matching': True,
    }]

    def _extract_blog_videos(self, webpage, video_id):
        videos = []
        seen = set()

        def add(vid, key):
            if not vid or not key or vid in seen:
                return
            seen.add(vid)
            videos.append((vid, key))

        for tag in get_elements_html_by_class('__se_module_data', webpage):
            attrs = extract_attributes(tag)
            for attr in ('data-module', 'data-module-v2'):
                raw = attrs.get(attr)
                if not raw:
                    continue
                data = self._parse_json(raw, video_id, fatal=False)
                add(traverse_obj(data, ('data', 'vid', {str})),
                    traverse_obj(data, ('data', ('inkey', 'key'), {str}), get_all=False))

        for mobj in re.finditer(r'<[^>]+?\bvid=["\']([^"\']+)["\'][^>]*>', webpage):
            attrs = extract_attributes(mobj.group(0))
            add(attrs.get('vid'), attrs.get('key'))

        return videos

    def _real_extract(self, url):
        blog_id, log_no = self._match_valid_url(url).group('blog_id', 'log_no')
        display_id = f'{blog_id}_{log_no}'

        webpage = self._download_webpage(
            'https://blog.naver.com/PostView.naver', display_id, query={
                'blogId': blog_id,
                'logNo': log_no,
            })

        videos = self._extract_blog_videos(webpage, display_id)
        if not videos:
            raise ExtractorError('No Naver video found in this blog post', expected=True)

        post_title = self._og_search_title(webpage, default=None)
        description = self._og_search_description(webpage, default=None)
        uploader = self._search_regex(
            r"var\s+nickName\s*=\s*'([^']*)'", webpage, 'uploader', default=None)
        timestamp = int_or_none(self._search_regex(
            r'var\s+postWriteDate\s*=\s*["\'](\d+)["\']',
            webpage, 'timestamp', default=None), scale=1000)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        entries = []
        for vid, key in videos:
            info = self._extract_video_info(vid, vid, key)
            info.update({
                'uploader': uploader or info.get('uploader'),
                'uploader_id': blog_id,
                'uploader_url': f'https://blog.naver.com/{blog_id}',
                'timestamp': timestamp,
                'description': description,
            })
            if not info.get('title'):
                info['title'] = post_title
            if not url_or_none(info.get('thumbnail')):
                info['thumbnail'] = thumbnail
            entries.append(info)

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, display_id, post_title, description, multi_video=True)
