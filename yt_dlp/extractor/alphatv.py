from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    determine_ext,
    traverse_obj,
    unescapeHTML,
    unified_timestamp,
    url_or_none,
)


class AlphaTVIE(InfoExtractor):
    IE_NAME = 'alphatv'
    IE_DESC = 'Alpha TV'
    _GEO_COUNTRIES = ['GR']
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?alphatv\.gr/
        (?:
            (?:series|show|newscast)/[^/?#]+/(?:episode|show-episode|broadcast)/(?P<id>\d+)(?:-[^/?#]*)?
            |(?P<live>live)
        )
        /?(?:$|[?#])
    '''
    _TESTS = [{
        'url': 'https://www.alphatv.gr/series/to-soi-soy/episode/687764-s6-epeisodio-40/',
        'md5': '02d8733daf31dd41ad190b23cbc44ff2',
        'info_dict': {
            'id': '687764',
            'ext': 'mp4',
            'title': 'Σ6 - ΕΠΕΙΣΟΔΙΟ 40 | AlphaTV',
            'description': 'md5:ae9915f548c4e1114d009e01264804d3',
            'thumbnail': r're:https://www\.alphatv\.gr/wp-content/uploads/.+\.jpg',
            'timestamp': 1776453049,
            'upload_date': '20260417',
            'series': 'Το Σόι σου',
            'episode': 'Σ6 - ΕΠΕΙΣΟΔΙΟ 40 | AlphaTV',
            'episode_number': 40,
        },
    }, {
        'url': 'https://www.alphatv.gr/show/whipe-out-usa/show-episode/738039-s9-epeisodio-2/',
        'only_matching': True,
    }, {
        'url': 'https://www.alphatv.gr/newscast/alpha-news/broadcast/741563-mesimeriano-deltio-30-8-20206/',
        'only_matching': True,
    }, {
        'url': 'https://www.alphatv.gr/live/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        is_live = bool(mobj.group('live'))
        video_id = mobj.group('id') or 'live'
        webpage = self._download_webpage(url, video_id)

        video_url = url_or_none(unescapeHTML(self._search_regex(
            r'\bdata-video-url=(["\'])(?P<url>(?:https?:)?//.+?)\1',
            webpage, 'video url', default=None, group='url')))
        if not video_url:
            video_url = traverse_obj(
                list(self._yield_json_ld(webpage, video_id, fatal=False)),
                (..., '@graph', lambda _, v: v.get('@type') == 'VideoObject',
                 ('embedUrl', 'contentUrl'), {url_or_none}), get_all=False)

        if not video_url:
            youtube_url = next(YoutubeIE._extract_embed_urls(url, webpage), None)
            if youtube_url:
                return self.url_result(youtube_url, YoutubeIE)
            raise ExtractorError('Unable to extract video URL', expected=True)

        ext = determine_ext(video_url, 'mp4')
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                video_url, video_id, 'mp4', m3u8_id='hls', live=is_live)
        else:
            formats, subtitles = [{'url': video_url, 'ext': ext}], {}

        info = self._search_json_ld(webpage, video_id, default={})
        info.pop('url', None)
        info.pop('ext', None)
        if (info.get('season_number') or 0) > 100:
            info.pop('season_number', None)

        info.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (self._og_search_title(webpage, default=None)
                      or info.get('title')
                      or self._html_extract_title(webpage)),
            'description': info.get('description') or self._og_search_description(webpage, default=None),
            'thumbnail': (info.get('thumbnail')
                          or traverse_obj(info, ('thumbnails', 0, 'url'))
                          or self._og_search_thumbnail(webpage, default=None)),
            'timestamp': info.get('timestamp') or unified_timestamp(
                self._html_search_meta('article:published_time', webpage, default=None)),
        })
        if is_live:
            info['live_status'] = 'is_live'
        return info
