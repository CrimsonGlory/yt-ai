from .common import InfoExtractor


class BalapanIE(InfoExtractor):
    IE_DESC = 'Balapan TV livestream'
    _VALID_URL = r'https?://(?:www\.)?balapan\.tv/(?P<id>live)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://balapan.tv/live',
        'info_dict': {
            'id': 'live',
            'ext': 'mp4',
            'title': r're:«Balapan» телеарнасының тікелей көрсетілімі\. Тікелей эфир \d{4}-\d{2}-\d{2} \d{2}:\d{2}',
            'description': 'md5:6e32372846b63e6add480ea8f1632640',
            'thumbnail': r're:https?://.+\.(?:jpe?g|png)',
            'is_live': True,
            'live_status': 'is_live',
        },
    }, {
        'url': 'https://www.balapan.tv/live/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_url = self._search_regex(
            r'<iframe[^>]+src=["\'](https?://player\.rtrk\.kz/[^"\']+)',
            webpage, 'player URL')
        player_page = self._download_webpage(
            player_url, video_id, 'Downloading player',
            headers={'Referer': url})

        m3u8_url = self._search_regex(
            r'(?:var\s+)?source\s*=\s*(["\'])(?P<url>https?://[^"\']+\.m3u8(?:[^"\']*)?)\1',
            player_page, 'm3u8 URL', group='url')

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', live=True)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage, default=None) or 'Balapan',
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': True,
        }
