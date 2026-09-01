from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_duration,
    str_or_none,
    unified_timestamp,
    url_or_none,
    urlencode_postdata,
    urljoin,
)
from ..utils.traversal import traverse_obj


class NowTVTRIE(InfoExtractor):
    IE_NAME = 'nowtv.com.tr'
    IE_DESC = 'NOW (formerly FOX Turkey)'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?(?:nowtv|fox)\.com\.tr/
        (?P<show>[\w-]+)/
        (?P<kind>bolum|fragman|ozel-sahne|bulten|one-cikan-haber)/
        (?P<id>[^/?#]+)
        (?:/(?P<slug>[\w-]+))?
        /?(?:$|[?#])
    '''
    _TESTS = [{
        'url': 'https://www.nowtv.com.tr/Ask-Mantik-Intikam/bolum/22',
        'md5': '2e93ac87321a9bfaacf1db2205fd174e',
        'info_dict': {
            'id': '80464',
            'ext': 'mp4',
            'display_id': '22',
            'title': 'Aşk Mantık İntikam - 22. Bölüm',
            'description': 'md5:479b7285dd1912ea9b00eb7be03057ab',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png)',
            'duration': 6876,
            'timestamp': 1637352000,
            'upload_date': '20211119',
            'series': 'Aşk Mantık İntikam',
            'series_id': '1588',
            'season': 'Season 1',
            'season_number': 1,
            'episode': '22. Bölüm',
            'episode_number': 22,
        },
    }, {
        'url': 'https://www.nowtv.com.tr/Omur-Usta/fragman/1-Bolum-1-Fragman',
        'only_matching': True,
    }, {
        'url': 'https://www.nowtv.com.tr/Kiskanmak/ozel-sahne/133990/cihan-ve-nuzhet-arasinda-gerginlik',
        'only_matching': True,
    }, {
        'url': 'https://www.nowtv.com.tr/NOW-Ana-Haber/one-cikan-haber/135211/komedyene-sorusturmaya-tepki',
        'only_matching': True,
    }, {
        'url': 'https://www.fox.com.tr/Ask-Mantik-Intikam/bolum/22',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video = self._search_json(
            r'\bvideo\s*:', webpage, 'video data', display_id, default={})
        video_id = traverse_obj(
            video, ('id', {int_or_none}, {str_or_none})) or self._search_regex(
            r'\bdata-video-id=["\'](\d+)', webpage, 'video id')

        stream = self._download_json(
            urljoin(url, '/ajax/stream'), video_id,
            data=urlencode_postdata({'video_id': video_id}),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': url,
            })
        stream_url = traverse_obj(stream, ('video_url', {url_or_none}))
        if not stream_url:
            raise ExtractorError(
                traverse_obj(stream, ('message', {str}))
                or f'No stream URL (code {traverse_obj(stream, "code")})',
                expected=True)

        ext = determine_ext(stream_url, 'mp4')
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats, subtitles = [{'url': stream_url, 'ext': ext}], {}

        series = traverse_obj(video, ('program', 'name', {str}))
        episode = traverse_obj(video, ('name', {str}))
        publish_at = join_nonempty(
            traverse_obj(video, ('publish_on_date', {str})),
            traverse_obj(video, ('publish_on_time', {str})), delim=' ')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': join_nonempty(series, episode, delim=' - ') or self._og_search_title(webpage),
            'description': (
                clean_html(traverse_obj(video, (('summary', 'meta_description', 'description'), {str}, any)))
                or self._og_search_description(webpage)),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': parse_duration(traverse_obj(video, ('duration', {str}))),
            'timestamp': unified_timestamp(publish_at),
            'series': series,
            'series_id': traverse_obj(video, ('program_id', {int_or_none}, {str_or_none})),
            'season_number': traverse_obj(video, ('season', {int_or_none})),
            'episode': episode,
            'episode_number': traverse_obj(video, ('bolum_no', {int_or_none})),
            'formats': formats,
            'subtitles': subtitles,
        }
