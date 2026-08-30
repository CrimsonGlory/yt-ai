import functools
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    determine_ext,
    extract_attributes,
    float_or_none,
    int_or_none,
    parse_duration,
    parse_iso8601,
    remove_end,
    traverse_obj,
    unified_strdate,
    update_url_query,
    url_or_none,
)


class OnePodcastIE(InfoExtractor):
    IE_NAME = 'onepodcast'
    IE_DESC = 'OnePodcast'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?onepodcast\.it/
        (?:(?:embed|detail)/)?brand/(?P<brand>[^/?#]+)/\d{4}/\d{2}/\d{2}/
        (?:audio|video)/[^/?#]+-(?P<id>\d+)/?
    '''
    _TESTS = [{
        'url': 'https://www.onepodcast.it/brand/onepodcast/2026/05/21/audio/il_prezzo_nascosto_del_digitale-21961623/',
        'md5': 'd7f1d23d215c6677d0726ef54d999ac4',
        'info_dict': {
            'id': '21961623',
            'ext': 'mp3',
            'title': 'Il prezzo nascosto del digitale',
            'description': 'md5:2effccbc89be844d71c1927c93653f03',
            'thumbnail': r're:https://www\.repstatic\.it/video/photo/.+\.jpg',
            'duration': 1555.031,
            'timestamp': 1779315356,
            'upload_date': '20260520',
            'series': "L'energia necessaria",
            'season': 'Stagione 1',
            'episode': 'Il prezzo nascosto del digitale',
            'channel': 'onepodcast',
        },
    }, {
        'url': 'https://www.onepodcast.it/brand/onepodcast/2026/08/26/video/fabiano_sterlacchini_-_il_direttore_dorchestra_dellaprilia_ep50-22586837/',
        'info_dict': {
            'id': '22586837',
            'ext': 'mp4',
            'title': "FABIANO STERLACCHINI - Il direttore d'orchestra dell'Aprilia Ep.50",
            'description': 'md5:45526d4ce86ef8f1816e375da56906b9',
            'thumbnail': r're:https://www\.repstatic\.it/video/photo/.+\.jpg',
            'duration': 5079,
            'timestamp': 1787745600,
            'upload_date': '20260826',
            'channel': 'onepodcast',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.onepodcast.it/embed/brand/onepodcast/2026/08/26/video/fabiano_sterlacchini_-_il_direttore_dorchestra_dellaprilia_ep50-22586837/',
        'only_matching': True,
    }, {
        'url': 'https://www.onepodcast.it/detail/brand/onepodcast/2026/05/21/audio/il_prezzo_nascosto_del_digitale-21961623/',
        'only_matching': True,
    }, {
        'url': 'https://www.onepodcast.it/brand/deejay/2026/08/27/audio/dee_giallo_story_-_depeche_mode_2009-22596513/',
        'only_matching': True,
    }]

    @staticmethod
    def _parse_audio_item(item, video_id, brand=None):
        audio_url = traverse_obj(item, (
            ('audio_url', {url_or_none}),
            ('trt', ('trt_cdn_audio_url', 'trt_audio_url'), {url_or_none}),
            any))
        return {
            'id': video_id,
            'url': audio_url,
            'ext': 'mp3',
            'vcodec': 'none',
            'channel': brand,
            **traverse_obj(item, {
                'title': ('title', {str}),
                'thumbnail': ('image', {url_or_none}),
                'duration': ((('trt', 'trt_lenght_sec', {float_or_none}),
                              ('duration', {parse_duration})), any),
                'upload_date': ('pub_date', {unified_strdate}),
                'series': ('wt', 'tree', 'videolivello3', {str}),
                'season': ('wt', 'tree', 'videolivello4', {str}),
                'episode': ('wt', 'tree', 'videolivello6', {str}),
            }),
        }

    def _extract_video_formats(self, webpage, video_id):
        formats = []
        sources = self._parse_json(self._search_regex(
            r'videoSrc\s*:\s*(["\'])(?P<json>\[.*?])\1', webpage,
            'video sources', default='[]', group='json'), video_id, fatal=False) or []
        for src in sources:
            video_url = url_or_none(src.get('src') if isinstance(src, dict) else src)
            if not video_url:
                continue
            if determine_ext(video_url) == 'm3u8':
                continue
            f = {
                'url': video_url,
                'format_id': 'http',
            }
            mobj = re.search(r'video-rrtv-(\d+)', video_url)
            if mobj:
                f.update({
                    'format_id': f'http-{mobj.group(1)}',
                    'vbr': int(mobj.group(1)),
                })
            formats.append(f)
        return formats

    def _real_extract(self, url):
        brand, video_id = self._match_valid_url(url).group('brand', 'id')
        webpage = self._download_webpage(url, video_id)
        json_ld = self._search_json_ld(webpage, video_id, default={})

        audio_item = traverse_obj(self._search_json(
            r'var\s+audioSource\d+\s*=', webpage, 'audio source', video_id,
            contains_pattern=r'\[(?s:.*?)]', end_pattern=r';', default=None),
            (lambda _, v: isinstance(v, dict), any))
        if audio_item:
            info = self._parse_audio_item(audio_item, video_id, brand)
            if not info.get('url'):
                raise ExtractorError('Unable to extract audio URL', expected=True)
        else:
            formats = self._extract_video_formats(webpage, video_id)
            json_ld_url = url_or_none(json_ld.get('url'))
            if not formats and json_ld_url:
                formats = [{'url': json_ld_url}]
            if not formats:
                raise ExtractorError('Unable to extract media URL', expected=True)
            info = {
                'id': video_id,
                'formats': formats,
                'channel': brand,
                'duration': int_or_none(self._search_regex(
                    r"videoLenght\s*:\s*'(\d+)'", webpage, 'duration', default=None)),
            }

        title = (
            info.get('title')
            or json_ld.get('title')
            or remove_end(self._og_search_title(webpage, default=''), ' - OnePodcast.it')
            or None)
        description = (
            json_ld.get('description')
            or self._og_search_description(webpage, default=None))
        thumbnail = info.get('thumbnail') or json_ld.get('thumbnail') or self._og_search_thumbnail(webpage)
        timestamp = json_ld.get('timestamp') or parse_iso8601(
            self._html_search_meta('article:published_time', webpage, default=None))

        json_ld.pop('url', None)
        return {
            **json_ld,
            **info,
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp or info.get('timestamp'),
            'duration': info.get('duration') or json_ld.get('duration'),
        }


class OnePodcastSerieIE(InfoExtractor):
    IE_NAME = 'onepodcast:serie'
    IE_DESC = 'OnePodcast series'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?onepodcast\.it/
        brand/[^/?#]+/\d{4}/\d{2}/\d{2}/serie/(?P<id>[^/?#]+)/?
    '''
    _PAGE_SIZE = 10
    _TESTS = [{
        'url': 'https://www.onepodcast.it/brand/onepodcast/2023/12/19/serie/delitti_invisibili-14653581/',
        'playlist_mincount': 10,
        'info_dict': {
            'id': 'delitti_invisibili-14653581',
            'title': 'Delitti Invisibili',
        },
    }, {
        'url': 'https://www.onepodcast.it/brand/onepodcast/2025/02/10/serie/tutte-le-volte-che/',
        'only_matching': True,
    }]

    def _fetch_page(self, json_url, serie_id, page):
        page_url = json_url if not page else update_url_query(json_url, {
            'page': page + 1,
            'offset': self._PAGE_SIZE,
        })
        data = self._download_json(
            page_url, serie_id, note=f'Downloading series page {page + 1}')
        for item in traverse_obj(data, ('data', lambda _, v: url_or_none(v.get('url')), {dict})):
            episode_url = item['url']
            episode_id = self._search_regex(
                r'-(\d+)/?(?:$|[?#])', episode_url, 'episode id', default=None)
            yield self.url_result(episode_url, OnePodcastIE, episode_id, item.get('title'))

    def _real_extract(self, url):
        serie_id = self._match_id(url)
        webpage = self._download_webpage(url, serie_id)
        json_url = url_or_none(extract_attributes(self._search_regex(
            r'(<gdwc-audio-player[^>]*>)', webpage, 'series player', default='')).get('data'))
        if not json_url:
            json_url = re.sub(
                r'(https?://(?:www\.)?onepodcast\.it)(?!/json)',
                r'\1/json', url.split('#')[0].split('?')[0])
        title = remove_end(
            self._og_search_title(webpage, default=''), ' - OnePodcast.it') or None
        return self.playlist_result(
            OnDemandPagedList(
                functools.partial(self._fetch_page, json_url, serie_id), self._PAGE_SIZE),
            serie_id, title)
