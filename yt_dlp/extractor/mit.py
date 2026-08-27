import json
import re

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    ExtractorError,
    clean_html,
    get_element_by_id,
    url_or_none,
)


class TechTVMITIE(InfoExtractor):
    IE_NAME = 'techtv.mit.edu'
    _VALID_URL = r'https?://techtv\.mit\.edu/(?:videos|embeds)/(?P<id>\d+)'

    _TEST = {
        'url': 'http://techtv.mit.edu/videos/25418-mit-dna-learning-center-set',
        'skip': 'video gone',
        'md5': '00a3a27ee20d44bcaa0933ccec4a2cf7',
        'info_dict': {
            'id': '25418',
            'ext': 'mp4',
            'title': 'MIT DNA and Protein Sets',
            'description': 'md5:46f5c69ce434f0a97e7c628cc142802d',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        raw_page = self._download_webpage(
            f'http://techtv.mit.edu/videos/{video_id}', video_id)
        clean_page = re.compile(r'<!--.*?-->', re.S).sub('', raw_page)

        base_url = self._proto_relative_url(self._search_regex(
            r'ipadUrl: \'(.+?cloudfront.net/)', raw_page, 'base url'), 'http:')
        formats_json = self._search_regex(
            r'bitrates: (\[.+?\])', raw_page, 'video formats')
        formats_mit = json.loads(formats_json)
        formats = [
            {
                'format_id': f['label'],
                'url': base_url + f['url'].partition(':')[2],
                'ext': f['url'].partition(':')[0],
                'format': f['label'],
                'width': f['width'],
                'vbr': f['bitrate'],
            }
            for f in formats_mit
        ]

        title = get_element_by_id('edit-title', clean_page)
        description = clean_html(get_element_by_id('edit-description', clean_page))
        thumbnail = self._search_regex(
            r'playlist:.*?url: \'(.+?)\'',
            raw_page, 'thumbnail', flags=re.DOTALL)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
        }


class OCWMITIE(InfoExtractor):
    IE_NAME = 'ocw.mit.edu'
    _VALID_URL = r'https?://(?:www\.)?ocw\.mit\.edu/courses/(?:[^/?#]+/)*(?P<id>[^/?#]+)'
    _BASE_URL = 'http://ocw.mit.edu/'

    _TESTS = [
        {
            'url': 'https://ocw.mit.edu/courses/6-041-probabilistic-systems-analysis-and-applied-probability-fall-2010/resources/lecture-7-multiple-variables-expectations-independence/',
            'md5': '4935dbfbedba8d4340ab02af35afd921',
            'info_dict': {
                'id': 'EObHWIEKGjA',
                'ext': 'mp4',
                'title': 'Lecture 7: Multiple Discrete Random Variables: Expectations, Conditioning, Independence',
                'description': 'In this lecture, the professor discussed multiple random variables, expectations, and binomial distribution.',
                'display_id': 'lecture-7-multiple-variables-expectations-independence',
            },
        },
        {
            'url': 'http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-041-probabilistic-systems-analysis-and-applied-probability-fall-2010/video-lectures/lecture-7-multiple-variables-expectations-independence/',
            'only_matching': True,
        },
        {
            'url': 'http://ocw.mit.edu/courses/mathematics/18-01sc-single-variable-calculus-fall-2010/1.-differentiation/part-a-definition-and-basic-rules/session-1-introduction-to-derivatives/',
            'skip': 'video gone',
            'info_dict': {
                'id': '7K1sB05pE0A',
                'ext': 'mp4',
                'title': 'Session 1: Introduction to Derivatives',
                'upload_date': '20090818',
                'uploader_id': 'MIT',
                'uploader': 'MIT OpenCourseWare',
                'description': 'This section contains lecture video excerpts, lecture notes, an interactive mathlet with supporting documents, and problem solving videos.',
            },
        },
    ]

    def _extract_youtube(self, webpage):
        youtube_id = self._search_regex(
            r'(?:youtube\.com/embed/|video-player-)(?P<id>[\w-]{11})',
            webpage, 'youtube id', default=None)
        if youtube_id:
            return youtube_id, f'https://www.youtube.com/watch?v={youtube_id}'

        embed_media = re.search(r'ocw_embed_(?:chapter_)?media\((.+?)\)', webpage)
        if not embed_media:
            return None, None
        metadata = re.split(r', ?', re.sub(r'[\'"]', '', embed_media.group(1)))
        youtube_url = metadata[1]
        return YoutubeIE.extract_id(youtube_url), youtube_url

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        webpage_title = self._html_extract_title(webpage)
        title = webpage_title.split('|')[0].strip() if webpage_title else None
        description = clean_html(self._search_regex(
            r'(?s)<strong>Description:</strong>\s*(.+?)</p>',
            webpage, 'description', default=None)) or self._html_search_meta(
            'Description', webpage)

        download_url = url_or_none(self._search_regex(
            r'data-downloadlink\s*=\s*"([^"]+)"',
            webpage, 'download url', default=None))
        youtube_id, youtube_url = self._extract_youtube(webpage)

        if download_url:
            return {
                'id': youtube_id or display_id,
                'display_id': display_id,
                'title': title,
                'description': description,
                'url': download_url,
            }

        if youtube_url:
            return {
                '_type': 'url_transparent',
                'id': youtube_id,
                'title': title,
                'description': description,
                'url': youtube_url,
                'ie_key': 'Youtube',
            }

        raise ExtractorError('Unable to find embedded video.')
