from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
    str_or_none,
    traverse_obj,
    url_or_none,
)


class SlutloadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?slutload\.com/(?:porn/video|(?:video/[^/?#]+|embed_player|watch))/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.slutload.com/porn/video/tiny_ebony_cutie_fucks_her_pocket_pussy_and_plugs_her_big_ass_live_on_cam',
        'md5': '6975b4ed0b5953580971951c194410d2',
        'info_dict': {
            'id': '1315',
            'display_id': 'tiny_ebony_cutie_fucks_her_pocket_pussy_and_plugs_her_big_ass_live_on_cam',
            'ext': 'mp4',
            'title': 'Tiny Ebony Cutie Fucks Her Pocket Pussy and Plugs Her Big Ass Live on Cam',
            'thumbnail': r're:https?://.*\.(?:jpg|webp)',
            'duration': 1125,
            'timestamp': 1767897856,
            'upload_date': '20260108',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'age_limit': 18,
            'uploader': 'Thee Mini Stalli',
            'uploader_id': 'theeministalli',
            'tags': ['Anal', 'Blowjob', 'Dildo', 'Fingering', 'Masturbation', 'Natural', 'Petite', 'Shaved Pussy', 'Small Tits', 'Tattoos'],
        },
    }, {
        'url': 'http://www.slutload.com/video/virginie-baisee-en-cam/TD73btpBqSxc/',
        'skip': 'video gone',
        'md5': '868309628ba00fd488cf516a113fd717',
        'info_dict': {
            'id': 'TD73btpBqSxc',
            'ext': 'mp4',
            'title': 'virginie baisee en cam',
            'age_limit': 18,
            'thumbnail': r're:https?://.*?\.jpg',
        },
    }, {
        # mobile site
        'url': 'http://mobile.slutload.com/video/masturbation-solo/fviFLmc6kzJ/',
        'only_matching': True,
    }, {
        'url': 'http://www.slutload.com/embed_player/TD73btpBqSxc/',
        'only_matching': True,
    }, {
        'url': 'http://www.slutload.com/watch/TD73btpBqSxc/Virginie-Baisee-En-Cam.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, impersonate=True)

        data = self._search_json(
            r'<script[^>]+id=["\']__PRELOADED_STATE__["\'][^>]*>',
            webpage, 'preloaded state', display_id, fatal=False)
        video = traverse_obj(data, ('freePorn', 'video', 'video', {dict})) or {}

        video_id = str_or_none(video.get('id')) or display_id
        title = traverse_obj(video, ('title', {str})) or self._og_search_title(webpage)
        hls_url = traverse_obj(video, ('video_url_hls', {url_or_none}))

        formats = []
        if hls_url:
            formats = self._extract_m3u8_formats(hls_url, video_id, 'mp4', m3u8_id='hls')
        else:
            for entry in self._parse_html5_media_entries(url, webpage, video_id) or []:
                media_url = url_or_none(entry.get('url'))
                if media_url and '.m3u8' in media_url:
                    formats.extend(self._extract_m3u8_formats(
                        media_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                else:
                    formats.extend(entry.get('formats') or ([entry] if media_url else []))

        if not formats:
            self.raise_no_formats('Unable to extract video URL', video_id=video_id)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': traverse_obj(video, ('thumb_url', {url_or_none})) or self._og_search_thumbnail(webpage),
            'duration': int_or_none(video.get('duration_in_second')),
            'timestamp': parse_iso8601(video.get('created_at')),
            'view_count': int_or_none(video.get('view_count')),
            'like_count': int_or_none(video.get('vote_up_count')),
            'dislike_count': int_or_none(video.get('vote_down_count')),
            'age_limit': 18,
            'uploader': traverse_obj(video, ('modelList', 0, 'displayName', {str})),
            'uploader_id': traverse_obj(video, ('modelList', 0, 'username', {str})),
            'tags': traverse_obj(video, ('tagList', ..., {str})),
        }
