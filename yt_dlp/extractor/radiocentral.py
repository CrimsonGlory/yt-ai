from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    strip_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class RadioCentralIE(InfoExtractor):
    IE_NAME = 'radiocentral'
    IE_DESC = 'Radio Central'
    _VALID_URL = [
        r'https?://(?:www\.)?radiocentral\.ch/podcasts/(?P<slug>[\w-]+)-(?P<id>\d+)',
        r'https?://(?:www\.)?radiocentral\.ch/podcasts(?:/seite/(?P<page>\d+))?/?(?:$|[?#])',
    ]
    _TESTS = [{
        'url': 'https://www.radiocentral.ch/podcasts/schwinger-ganz-persoenlich-152508388',
        'info_dict': {
            'id': '152508388',
            'title': 'Schwinger ganz persönlich',
            'thumbnail': r're:https?://static\.az-cdn\.ch/.+',
            'timestamp': 1689173415,
            'upload_date': '20230712',
        },
        'playlist': [{
            'md5': 'f684c0ae79a790e53030c7a4d6b4e60c',
            'info_dict': {
                'id': '153152719',
                'ext': 'mp3',
                'title': 'Vorschau Unspunnen Schwinget - Teil 10 mit Christian Stucki',
                'timestamp': 1692956798,
                'upload_date': '20230825',
                'series': 'Schwinger ganz persönlich',
                'thumbnail': r're:https?://static\.az-cdn\.ch/.+',
            },
        }],
        'params': {'playlistend': 1},
    }, {
        'url': 'https://www.radiocentral.ch/podcasts/schwinger-ganz-persoenlich-152508388',
        'info_dict': {
            'id': '152508388',
            'title': 'Schwinger ganz persönlich',
            'thumbnail': r're:https?://static\.az-cdn\.ch/.+',
            'timestamp': 1689173415,
            'upload_date': '20230712',
        },
        'playlist_mincount': 11,
    }, {
        'url': 'https://www.radiocentral.ch/podcasts/landlerabig-landlerzmorga-152588992',
        'only_matching': True,
    }, {
        'url': 'https://www.radiocentral.ch/podcasts/',
        'info_dict': {
            'id': 'podcasts',
            'title': str,
        },
        'playlist_mincount': 8,
    }, {
        'url': 'https://www.radiocentral.ch/podcasts/seite/2',
        'only_matching': True,
    }]

    def _deref(self, data, ref):
        if isinstance(ref, dict):
            node_id = ref.get('id')
            if node_id in data:
                return data[node_id]
        elif isinstance(ref, str) and ref in data:
            return data[ref]
        return ref

    def _image_url(self, data, image_ref):
        image = self._deref(data, image_ref)
        if not isinstance(image, dict):
            return
        nested = image.get('image')
        if isinstance(nested, dict):
            image = self._deref(data, nested) or image
        return traverse_obj(image, (
            ('imageUrl({"name":"n-large2x-16x9-far"})',
             'imageUrl({"name":"base-url"})'), {url_or_none}, any))

    def _parse_audio_asset(self, data, asset_ref, series, series_thumb):
        asset = self._deref(data, asset_ref)
        if not isinstance(asset, dict):
            return
        audio_rel = self._deref(data, asset.get('audio'))
        audio_url = traverse_obj(
            audio_rel if isinstance(audio_rel, dict) else asset,
            ('audioUrl', {url_or_none}))
        if not audio_url:
            return
        asset_id = traverse_obj(asset, ('id', {str})) or ''
        audio_id = self._search_regex(
            r'(\d+)$', asset_id, 'audio id', default=None) or self._search_regex(
            r'/extfile/([0-9a-f]+)', audio_url, 'audio id', default=None)
        if not audio_id:
            return
        dc = self._deref(data, asset.get('dc'))
        return {
            'id': audio_id,
            'title': strip_or_none(asset.get('title')) or audio_id,
            'description': strip_or_none(asset.get('description')),
            'url': audio_url,
            'ext': 'mp3',
            'vcodec': 'none',
            'thumbnail': self._image_url(data, asset.get('stillImage')) or series_thumb,
            'timestamp': traverse_obj(dc, (('created', 'effective'), {parse_iso8601}, any)),
            'series': series,
        }

    def _extract_index(self, url, page):
        playlist_id = f'podcasts-{page}' if page else 'podcasts'
        webpage = self._download_webpage(url, playlist_id)
        data = self._search_json(
            r'window\.__APOLLO_STATE__\s*=', webpage, 'apollo state', playlist_id)
        entries, seen = [], set()
        for key, ref in (data.get('ROOT_QUERY') or {}).items():
            if 'NewsArticle:' not in key:
                continue
            article = self._deref(data, ref)
            if not isinstance(article, dict):
                continue
            page_url = traverse_obj(self._deref(data, article.get('urls')), (
                ('absolute', 'relative'), {url_or_none}, any))
            if not page_url or '/podcasts/' not in page_url:
                continue
            video_id = self._search_regex(
                r'-(\d+)/?$', page_url, 'podcast id', default=None)
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            entries.append(self.url_result(
                urljoin('https://www.radiocentral.ch/', page_url),
                RadioCentralIE, video_id, strip_or_none(article.get('title'))))
        if not entries:
            raise ExtractorError('No podcasts found', expected=True)
        return self.playlist_result(
            entries, playlist_id,
            strip_or_none(self._og_search_title(webpage, default=None)) or 'Podcasts')

    def _extract_podcast(self, url, article_id):
        webpage = self._download_webpage(url, article_id)
        data = self._search_json(
            r'window\.__APOLLO_STATE__\s*=', webpage, 'apollo state', article_id)
        article = data.get(f'NewsArticle:NewsArticle:{article_id}')
        if not isinstance(article, dict):
            raise ExtractorError('Unable to extract article data')

        title = strip_or_none(article.get('title'))
        thumbnail = (
            self._image_url(data, article.get('mainAsset'))
            or self._image_url(data, article.get('ogImage'))
            or self._og_search_thumbnail(webpage))
        json_ld = self._search_json_ld(webpage, article_id, default={})
        dc = self._deref(data, article.get('dc'))

        segment_entries, block_entries = [], []
        for block_ref in traverse_obj(article, ('blocks', lambda _, v: v)):
            block = self._deref(data, block_ref)
            if not isinstance(block, dict):
                continue
            typename = block.get('__typename')
            if typename == 'ShowSegmentsEnrichmentBlock':
                segments = self._deref(data, traverse_obj(block, (
                    lambda k, _: str(k).startswith('showSegments'), any)))
                for asset_ref in traverse_obj(segments, ('data', lambda _, v: v)) or []:
                    entry = self._parse_audio_asset(data, asset_ref, title, thumbnail)
                    if entry:
                        segment_entries.append(entry)
            elif typename == 'AudioEnrichmentBlock':
                entry = self._parse_audio_asset(data, block, title, thumbnail)
                if entry:
                    block_entries.append(entry)

        entries = segment_entries or block_entries
        if not entries:
            raise ExtractorError('No audio found', expected=True)

        return self.playlist_result(
            entries, article_id, title or json_ld.get('title'),
            strip_or_none(article.get('lead')) or json_ld.get('description'),
            thumbnail=thumbnail,
            timestamp=traverse_obj(dc, (
                ('effective', 'created'), {parse_iso8601}, any)) or json_ld.get('timestamp'))

    def _real_extract(self, url):
        groups = self._match_valid_url(url).groupdict()
        article_id = groups.get('id')
        if article_id:
            return self._extract_podcast(url, article_id)
        return self._extract_index(url, groups.get('page'))
