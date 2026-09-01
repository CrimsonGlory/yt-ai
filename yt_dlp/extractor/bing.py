import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    orderedSet,
    parse_qs,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BingIE(InfoExtractor):
    IE_NAME = 'bing'
    IE_DESC = 'Bing Videos'
    _VALID_URL = r'https?://(?:(?:www|www2|cn|ssl|m)\.)?bing\.com/(?:videos|video)/(?:search|riverview/relatedvideo)(?:[/?#]|$)'
    _TESTS = [{
        'url': 'https://www.bing.com/videos/riverview/relatedvideo?q=search+for+loved+ones+continues+in+nepal&mid=1BFBA1A847FD7B9A1D7C1BFBA1A847FD7B9A1D7C',
        'md5': '4a916468671e8e5ebddd590fd230f78b',
        'info_dict': {
            'id': '269123141763',
            'ext': 'mp4',
            'title': 'Search for loved ones continues in Nepal after floods',
            'description': 'md5:5624875c666b41e93541f0167d64c846',
            'duration': 94,
            'timestamp': 1788217444,
            'upload_date': '20260831',
            'thumbnail': r're:https?://media-cldnry\.s-nbcnews\.com/.+',
            'display_id': '269123141763',
        },
        'params': {'format': 'best[protocol^=http]'},
        'add_ie': ['NBCNews'],
    }, {
        'url': 'https://www.bing.com/videos/search?q=cantajuego+lo+mejor+de&FORM=HDRSC3',
        'info_dict': {
            'id': 'cantajuego lo mejor de',
            'title': 'cantajuego lo mejor de',
        },
        'playlist_mincount': 5,
        'params': {
            'skip_download': True,
            'extract_flat': 'in_playlist',
        },
    }, {
        'url': 'https://www.bing.com/videos/search?q=news&view=detail&mid=1BFBA1A847FD7B9A1D7C1BFBA1A847FD7B9A1D7C',
        'only_matching': True,
    }, {
        'url': 'https://www.bing.com/video/search?q=news',
        'only_matching': True,
    }]
    _API_URL = 'https://www.bing.com/videos/api/custom/details'

    def _call_details_api(self, display_id, *, video_id=None, query=None, modules, fatal=True):
        api_query = {
            'vdpp': 'rvrv',
            'mmcaptn': 'Bing.Video',
            'modules': modules,
        }
        if video_id:
            api_query['id'] = video_id
        if query:
            api_query['q'] = query
        return self._download_json(
            self._API_URL, display_id, query=api_query, fatal=fatal,
            headers={'Referer': 'https://www.bing.com/videos'})

    def _extract_source_url(self, video):
        return traverse_obj(video, (('contentUrl', 'hostPageUrl'), {url_or_none}, any))

    def _extract_video(self, video_id):
        data = self._call_details_api(video_id, video_id=video_id, modules='VideoResult')
        video = traverse_obj(data, (
            ('videoResult', ('videoByIdResults', 'value', 0)), {dict}, any))
        source_url = self._extract_source_url(video)
        if not source_url:
            raise ExtractorError('Unable to extract Bing video source URL', expected=True)
        return self.url_result(source_url)

    def _search_entries_from_api(self, query):
        data = self._call_details_api(
            query, query=query, modules='queryresultvideos', fatal=False)
        return orderedSet(filter(None, traverse_obj(data, (
            'videoVerticalQueryResults', 'value', ...,
            ('contentUrl', 'hostPageUrl'), {url_or_none}, any,
        )) or []))

    def _search_entries_from_webpage(self, query):
        webpage = self._download_webpage(
            'https://www.bing.com/videos/search', query, query={'q': query})
        urls = []
        for mobj in re.finditer(r'\bmmeta="(\{[^"]+\})"', webpage):
            meta = self._parse_json(unescapeHTML(mobj.group(1)), query, fatal=False) or {}
            urls.append(url_or_none(meta.get('murl')))
        return orderedSet(filter(None, urls))

    def _extract_search(self, query):
        urls = self._search_entries_from_api(query) or self._search_entries_from_webpage(query)
        if not urls:
            raise ExtractorError('Unable to extract Bing video search results', expected=True)
        return self.playlist_result(
            (self.url_result(url) for url in urls), query, query)

    def _real_extract(self, url):
        qs = parse_qs(url)
        video_id = traverse_obj(qs, ('mid', 0, {str}))
        query = traverse_obj(qs, ('q', 0, {str}))
        if video_id:
            return self._extract_video(video_id)
        if query:
            return self._extract_search(query)
        raise ExtractorError('Unable to extract Bing video id or search query', expected=True)
