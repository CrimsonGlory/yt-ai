from .common import InfoExtractor
from ..utils import ExtractorError, remove_end


class ThisAVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisav\.com/video/(?P<id>[0-9]+)/.*'
    _TESTS = [{
        # jwplayer
        'url': 'http://www.thisav.com/video/47734/%98%26sup1%3B%83%9E%83%82---just-fit.html',
        'skip': 'thisav.com seized by FANZA in 2025; domain serves a confiscation notice and no longer hosts videos',
        'md5': '0480f1ef3932d901f0e0e719f188f19b',
        'info_dict': {
            'id': '47734',
            'ext': 'flv',
            'title': '高樹マリア - Just fit',
            'uploader': 'dj7970',
            'uploader_id': 'dj7970',
        },
    }, {
        # html5 media
        'url': 'http://www.thisav.com/video/242352/nerdy-18yo-big-ass-tattoos-and-glasses.html',
        'skip': 'thisav.com seized by FANZA in 2025; domain serves a confiscation notice and no longer hosts videos',
        'md5': 'ba90c076bd0f80203679e5b60bf523ee',
        'info_dict': {
            'id': '242352',
            'ext': 'mp4',
            'title': 'Nerdy 18yo Big Ass Tattoos and Glasses',
            'uploader': 'cybersluts',
            'uploader_id': 'cybersluts',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        if 'domain was confiscated' in webpage.lower() or 'ドメインの没収' in webpage:
            raise ExtractorError(
                'thisav.com was seized by FANZA in 2025; the domain no longer hosts videos',
                expected=True)
        title = remove_end(self._html_extract_title(webpage), ' - 視頻 - ThisAV.com-世界第一中文成人娛樂網站')
        video_url = self._html_search_regex(
            r"addVariable\('file','([^']+)'\);", webpage, 'video url', default=None)
        if video_url:
            info_dict = {
                'formats': [{
                    'url': video_url,
                }],
            }
        else:
            entries = self._parse_html5_media_entries(url, webpage, video_id)
            if entries:
                info_dict = entries[0]
            else:
                info_dict = self._extract_jwplayer_data(
                    webpage, video_id, require_title=False)
        if isinstance(info_dict, list):
            info_dict = info_dict[0] if info_dict else {}
        uploader = self._html_search_regex(
            r': <a href="http://www\.thisav\.com/user/[0-9]+/(?:[^"]+)">([^<]+)</a>',
            webpage, 'uploader name', fatal=False)
        uploader_id = self._html_search_regex(
            r': <a href="http://www\.thisav\.com/user/[0-9]+/([^"]+)">(?:[^<]+)</a>',
            webpage, 'uploader id', fatal=False)

        info_dict.update({
            'id': video_id,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'title': title,
        })

        return info_dict
