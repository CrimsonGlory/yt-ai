from .common import InfoExtractor
from ..utils import merge_dicts, url_or_none


class WorldStarHipHopIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = (
        r'https?://(?:www\.|m\.)?worldstar(?:candy|hiphop)?\.com/'
        r'(?:(?:videos|android)/video\.php\?(?:[^#]*?&)?v=|videos/)'
        r'(?P<id>[^/?#&]+)')
    _TESTS = [{
        'url': 'https://worldstarhiphop.com/videos/wshhaGFmLBh0N98q4tJt/weight-loss-transformation-has-the-internet-debating-before-or-after',
        'md5': '16feb824978969d0b1dde5cb10fe084e',
        'info_dict': {
            'id': 'wshhaGFmLBh0N98q4tJt',
            'ext': 'mp4',
            'title': 'Weight Loss Transformation Has The Internet Debating: Before Or After?',
            'thumbnail': r're:https?://hw-static\.worldstarhiphop\.com/.+\.jpg',
            'timestamp': 1787875200,
            'upload_date': '20260828',
            'view_count': int,
        },
    }, {
        'url': 'https://worldstar.com/videos/wshhaGFmLBh0N98q4tJt/weight-loss-transformation-has-the-internet-debating-before-or-after',
        'only_matching': True,
    }, {
        'url': 'http://www.worldstarhiphop.com/videos/video.php?v=wshh6a7q1ny0G34ZwuIO',
        'skip': 'video gone',
        'md5': '9d04de741161603bf7071bbf4e883186',
        'info_dict': {
            'id': 'wshh6a7q1ny0G34ZwuIO',
            'ext': 'mp4',
            'title': 'KO Of The Week: MMA Fighter Gets Knocked Out By Swift Head Kick!',
        },
    }, {
        'url': 'http://m.worldstarhiphop.com/android/video.php?v=wshh6a7q1ny0G34ZwuIO',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info = self._search_json_ld(
            webpage, video_id, expected_type='VideoObject', default={})
        info.pop('ext', None)

        if not url_or_none(info.get('url')):
            entries = self._parse_html5_media_entries(url, webpage, video_id)
            if entries:
                info = merge_dicts(entries[0], info)
            else:
                return self.url_result(url, 'Generic')

        title = info.get('title') or self._html_search_regex(
            [r'(?s)<div class="content-heading">\s*<h1>(.*?)</h1>',
             r'<span[^>]+class="tc-sp-pinned-title">(.*)</span>'],
            webpage, 'title', default=None) or self._og_search_title(webpage)

        info = merge_dicts({
            'id': video_id,
            'title': title,
        }, info)
        if not info.get('description'):
            info.pop('description', None)
        return info
