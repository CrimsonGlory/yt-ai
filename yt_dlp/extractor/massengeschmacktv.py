from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_resolution,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class MassengeschmackTVIE(InfoExtractor):
    IE_NAME = 'massengeschmack.tv'
    _VALID_URL = [
        r'https?://(?:www\.)?massengeschmack\.tv/play/(?P<id>[^?&#]+)',
        r'https?://(?:www\.)?orangeflix\.de/clip/(?P<id>[^?&#]+)',
    ]

    _TESTS = [{
        'url': 'https://massengeschmack.tv/play/fktv202',
        'md5': 'a9e054db9c2b5a08f0a0527cc201e8d3',
        'info_dict': {
            'id': 'fktv202',
            'ext': 'mp4',
            'title': 'Folge 202 – Fernsehkritik-TV',
            'description': 'md5:7e711f67d9e7157189adf9173d401db6',
            'thumbnail': 'https://cache.massengeschmack.tv/img/mag/fktv202.jpg',
            'duration': 3683,
            'timestamp': 1489838400,
            'upload_date': '20170318',
        },
    }, {
        'url': 'https://orangeflix.de/clip/fktv202',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        episode = self._match_id(url)
        webpage = self._download_webpage(url, episode)
        clip = traverse_obj(
            self._search_nextjs_v13_data(webpage, episode, fatal=False),
            (..., {dict}, lambda k, v: k == 'clip' and isinstance(v, dict) and v.get('id') == episode),
            get_all=False) or {}

        if clip and clip.get('canAccess') is False and not clip.get('hasDownload'):
            self.raise_login_required('This clip is only available for premium members')

        formats = []
        for download in traverse_obj(clip, ('downloads', lambda _, v: url_or_none(v['url']))):
            media_url = download['url']
            is_audio = download.get('t') == 'music'
            formats.append({
                'url': media_url,
                'format_id': download.get('desc') or determine_ext(media_url),
                'filesize': int_or_none(download.get('size')),
                'vcodec': 'none' if is_audio else None,
                **parse_resolution(download.get('dimensions')),
            })

        if not formats:
            self.raise_no_formats('No media downloads found', expected=True, video_id=episode)

        return {
            'id': episode,
            'formats': formats,
            'title': (
                join_nonempty(clip.get('title'), clip.get('projectTitle'), delim=' – ')
                or self._og_search_title(webpage, default=None)),
            'description': traverse_obj(clip, ('description', {str})),
            'thumbnail': (
                url_or_none(clip.get('image'))
                or traverse_obj(clip, ('images', 'thumbnail', {url_or_none}))
                or self._og_search_thumbnail(webpage, default=None)),
            'duration': int_or_none(clip.get('durationSeconds')),
            'timestamp': int_or_none(clip.get('time')),
        }
