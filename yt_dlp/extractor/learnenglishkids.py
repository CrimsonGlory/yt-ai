from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    extract_attributes,
    remove_end,
    url_or_none,
)
from ..utils.traversal import find_element, traverse_obj


class LearnEnglishKidsIE(InfoExtractor):
    IE_NAME = 'learnenglishkids'
    IE_DESC = 'LearnEnglish Kids'
    _VALID_URL = r'https?://(?:www\.)?learnenglishkids\.britishcouncil\.org/(?:[\w-]+/){2}(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://learnenglishkids.britishcouncil.org/listen-watch/songs/quiet-please',
        'md5': 'f702af3cab5489312190fed08ed762cd',
        'info_dict': {
            'id': 'quiet-please',
            'ext': 'mp4',
            'title': 'Quiet, please',
            'description': 'Practise classroom words and phrases with this song about school.',
            'thumbnail': r're:https?://learnenglishkids\.britishcouncil\.org/video/.+\.jpg',
        },
    }, {
        'url': 'https://learnenglishkids.britishcouncil.org/listen-watch/how-videos/how-brush-your-teeth',
        'info_dict': {
            'id': 'how-brush-your-teeth',
            'ext': 'mp4',
            'title': 'How to brush your teeth',
            'description': 'Do you know what happens if we don\'t brush our teeth properly? Watch this video to learn how to brush your teeth!',
            'thumbnail': r're:https?://learnenglishkids\.britishcouncil\.org/video/.+\.jpg',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://learnenglishkids.britishcouncil.org/listen-watch/songs/scary-skeleton',
        'only_matching': True,
    }, {
        'url': 'https://learnenglishkids.britishcouncil.org/listen-watch/short-stories/goldilocks-three-bears',
        'only_matching': True,
    }, {
        'url': 'https://learnenglishkids.britishcouncil.org/grammar-vocabulary/grammar-videos/grans-adventures',
        'only_matching': True,
    }, {
        'url': 'https://learnenglishkids.britishcouncil.org/listen-watch/video-zone/mr-tumbles-bedtime-routine',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        attrs = extract_attributes(self._search_regex(
            r'(<video(?=[^>]+data-video=)[^>]+>)', webpage, 'video', default=''))
        video_url = traverse_obj(attrs, ('data-video', {url_or_none}))
        if not video_url:
            youtube_url = next(YoutubeIE._extract_embed_urls(url, webpage), None)
            if youtube_url:
                return self.url_result(youtube_url, YoutubeIE)
            raise ExtractorError('No video found', expected=True)

        ext = determine_ext(video_url, 'mp4')
        if ext == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                video_url, video_id, 'mp4', m3u8_id='hls')
        else:
            formats, subtitles = [{'url': video_url, 'ext': ext}], {}

        caption_url = traverse_obj(attrs, ('data-caption', {url_or_none}))
        if caption_url:
            self._merge_subtitles({
                'en': [{'url': caption_url, 'ext': determine_ext(caption_url, 'srt')}],
            }, target=subtitles)

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (
                self._html_search_regex(
                    r'<h1[^>]*>\s*<span>([^<]+)</span>', webpage, 'title', default=None)
                or remove_end(self._html_extract_title(webpage), ' | LearnEnglish Kids')),
            'description': traverse_obj(webpage, (
                {find_element(cls='field--name-field-text-teaser')}, {clean_html})),
            'thumbnail': traverse_obj(attrs, ('data-poster', {url_or_none})),
        }
