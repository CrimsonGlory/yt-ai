from .common import InfoExtractor
from .vimeo import VimeoIE
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    join_nonempty,
    traverse_obj,
    url_or_none,
)


class NFSAIE(InfoExtractor):
    IE_NAME = 'nfsa'
    IE_DESC = 'National Film and Sound Archive of Australia'
    _VALID_URL = [
        r'https?://(?:www\.)?nfsa\.gov\.au/collection/item/(?P<id>[\w-]+)',
        r'https?://(?:www\.)?nfsa\.gov\.au/collection/curated/asset/(?P<node_id>\d+)-(?P<id>[\w-]+)',
    ]
    _API_URL = 'https://dhoneoxg.api.sanity.io/v2021-10-21/data/query/production'
    _TESTS = [{
        'url': 'https://www.nfsa.gov.au/collection/item/will-power-berlei',
        'md5': '80af7061d956b808b91679796d062649',
        'info_dict': {
            'id': '237987070',
            'ext': 'mp4',
            'title': 'Will-Power by Berlei',
            'description': 'md5:ff4746bc1e1c5205db688a8229891bcb',
            'thumbnail': 'https://cdn.sanity.io/images/dhoneoxg/production/a253398e3654f27f671f1b09b8b4ce64cd44f297-768x576.jpg',
            'duration': 31,
            'release_year': 1968,
            'display_id': 'will-power-berlei',
            'uploader': 'NFSA',
            'uploader_id': 'nfsa',
            'uploader_url': 'https://vimeo.com/nfsa',
        },
        'params': {'format': 'b[protocol=https]'},
        'expected_warnings': ['Failed to parse XML: not well-formed'],
    }, {
        'url': 'https://www.nfsa.gov.au/collection/item/melbourne-police-motor-patrol-clip-1',
        'md5': '5ecfb87bce2f97e598daded8fea08265',
        'info_dict': {
            'id': 'melbourne-police-motor-patrol-clip-1',
            'ext': 'mp4',
            'title': 'With the Melbourne Police Motor Patrol: Clip 1',
            'description': 'md5:d101f5d364e380929f272f0644ffc6d9',
            'thumbnail': 'https://cdn.sanity.io/images/dhoneoxg/production/0831f0d221f156ce69d5150485f1b97329f4496e-1440x990.jpg',
            'release_year': 1930,
            'display_id': 'melbourne-police-motor-patrol-clip-1',
        },
    }, {
        'url': 'https://www.nfsa.gov.au/collection/curated/asset/98200-will-power-berlei',
        'only_matching': True,
    }]

    def _portable_text(self, blocks):
        return join_nonempty(*(
            ''.join(traverse_obj(block, ('children', ..., 'text', {str})) or [])
            for block in traverse_obj(blocks, (..., {dict})) or []
        ), delim='\n\n') or None

    def _fetch_page(self, display_id, node_id):
        if node_id:
            filt = f'_id=="node-{node_id}" || slug.current=="{display_id}"'
        else:
            filt = f'slug.current=="{display_id}"'
        query = (
            f'*[_type=="assetPage" && ({filt})][0]'
            '{_id,title,assetType,'
            'asset{location,url,file{asset->{url,extension,mimeType}}},'
            'featuredImage{asset->{url}},collectionData,body}')
        return traverse_obj(
            self._download_json(self._API_URL, display_id, query={'query': query}),
            ('result', {dict}))

    def _real_extract(self, url):
        groups = self._match_valid_url(url).groupdict()
        display_id, node_id = groups['id'], groups.get('node_id')
        page = self._fetch_page(display_id, node_id)
        if not page:
            raise ExtractorError('Unable to extract NFSA collection item', expected=True)

        info = {
            'display_id': display_id,
            **traverse_obj(page, {
                'title': ('title', {str}),
                'thumbnail': ('featuredImage', 'asset', 'url', {url_or_none}),
                'release_year': ('collectionData', 'year', {int_or_none}),
                'duration': ('collectionData', 'duration', {int_or_none}),
            }),
            'description': self._portable_text(page.get('body')),
        }

        asset_url = traverse_obj(page, ('asset', 'url', {url_or_none}))
        if asset_url and VimeoIE.suitable(asset_url):
            vimeo_id = VimeoIE._match_id(asset_url)
            return self.url_result(
                VimeoIE._smuggle_referrer(
                    f'https://player.vimeo.com/video/{vimeo_id}',
                    f'https://www.nfsa.gov.au/collection/item/{display_id}'),
                ie=VimeoIE, video_id=vimeo_id, url_transparent=True, **info)
        if asset_url:
            return self.url_result(asset_url, url_transparent=True, **info)

        file_url = traverse_obj(page, ('asset', 'file', 'asset', 'url', {url_or_none}))
        if file_url:
            ext = traverse_obj(page, ('asset', 'file', 'asset', 'extension', {str})) or determine_ext(file_url)
            mime = traverse_obj(page, ('asset', 'file', 'asset', 'mimeType', {str})) or ''
            entry = {
                **info,
                'id': display_id,
                'url': file_url,
                'ext': ext,
            }
            if mime.startswith('audio/') or ext in ('mp3', 'm4a', 'wav', 'ogg', 'flac'):
                entry['vcodec'] = 'none'
            return entry

        asset_type = traverse_obj(page, ('assetType', {str})) or 'item'
        raise ExtractorError(f'This NFSA {asset_type} has no downloadable media', expected=True)
