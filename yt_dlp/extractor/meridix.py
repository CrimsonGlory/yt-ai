from .common import InfoExtractor


class MeridixIE(InfoExtractor):
    IE_DESC = 'Meridix / Stack Streaming'
    _VALID_URL = r'https?://(?:www\.)?meridix\.com/event/(?:index\.php\?(?:[^#]*?(?:recordid|EventID)=)?)?(?P<id>\d+)'
    _CDN_BASE = 'https://ssports-vod.dlt.qwilted-cds.cqloud.com/vod/_definst_'
    _HEADERS = {'Referer': 'https://www.meridix.com/'}
    _TESTS = [{
        'url': 'https://www.meridix.com/event/245473',
        'md5': '04fc6d5807e12864d99eb67e47da0182',
        'info_dict': {
            'id': '245473',
            'ext': 'mp4',
            'title': '245473',
        },
    }, {
        'url': 'https://www.meridix.com/event/index.php?liveid=triblivehssn6&recordid=245473',
        'only_matching': True,
    }, {
        'url': 'https://meridix.com/event/270523',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # Event HTML is behind Incapsula; Bitmovin still publishes Wowza VOD on Qwilt.
        candidates = (
            f'{self._CDN_BASE}/smil:http_ondemand/{video_id}.smil/playlist.m3u8',
            f'{self._CDN_BASE}/mp4:http_ondemand/{video_id}.mp4/playlist.m3u8',
        )

        formats, subtitles = [], {}
        for candidate in candidates:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                candidate, video_id, 'mp4', m3u8_id='hls',
                headers=self._HEADERS, fatal=False)
            if formats:
                break
        else:
            self.raise_no_formats('No video source', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': self._HEADERS,
        }
