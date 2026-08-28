import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    make_archive_id,
    unified_timestamp,
    urljoin,
)
from ..utils.traversal import traverse_obj


class NintendoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nintendo\.com/(?:(?P<locale>\w{2}(?:-\w{2})?)/)?nintendo-direct/(?P<slug>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.nintendo.com/nintendo-direct/09-04-2019/',
        'md5': 'f78dea299e005dcf8bf22bbb54839d23',
        'info_dict': {
            'ext': 'mp4',
            'id': '2oPmiviVePUA1IqAZzjuVh',
            'display_id': '09-04-2019',
            'title': 'Nintendo Direct 9.4.2019',
            'timestamp': 1567580400,
            'description': 'md5:8aac2780361d8cb772b6d1de66d7d6f4',
            'upload_date': '20190904',
            'age_limit': 17,
            'thumbnail': 'https://assets.nintendo.com/Nintendo%20Direct/Archive/thumbnail/archive-thumb-090419',
            '_old_archive_ids': ['nintendo J2bXdmaTE6fe3dWJTPcc7m23FNbc_A1V'],
        },
    }, {
        'url': 'https://www.nintendo.com/en-ca/nintendo-direct/08-31-2023/',
        'md5': '8738579a3242460088d6464d04314437',
        'info_dict': {
            'ext': 'mp4',
            'id': '2TB2w2rJhNYF84qQ9E57hU',
            'display_id': '08-31-2023',
            'title': 'Super Mario Bros. Wonder Direct 8.31.2023',
            'timestamp': 1693465200,
            'description': 'md5:3067c5b824bcfdae9090a7f38ab2d200',
            'tags': ['Mild Fantasy Violence', 'In-Game Purchases'],
            'upload_date': '20230831',
            'age_limit': 6,
            'thumbnail': 'https://assets.nintendo.com/Nintendo%20Direct/2023/JFdJ7XGbvFbC/306x172_Direct_thumbnail',
        },
    }, {
        'url': 'https://www.nintendo.com/us/nintendo-direct/50-fact-extravaganza/',
        'only_matching': True,
    }]

    def _create_asset_url(self, path):
        return urljoin('https://assets.nintendo.com/', urllib.parse.quote(path))

    def _extract_direct_info(self, url, slug, parsed_locale):
        webpage = self._download_webpage(url, slug)
        state = traverse_obj(
            self._search_nextjs_data(webpage, slug),
            ('props', 'pageProps', 'initialApolloState', {dict})) or {}

        def deref(obj):
            ref = traverse_obj(obj, ('__ref', {str}))
            return state.get(ref, obj)

        candidates = [
            value for value in state.values()
            if isinstance(value, dict)
            and value.get('__typename') == 'NintendoDirect'
            and value.get('slug') == slug
        ]
        direct_info = next((
            item for item in candidates if item.get('locale') == parsed_locale
        ), None) or traverse_obj(candidates, 0)
        if not direct_info:
            return None

        return {
            **direct_info,
            'contentRating': deref(direct_info.get('contentRating')),
            'contentDescriptors': [
                deref(item) for item in (direct_info.get('contentDescriptors') or [])
            ],
        }

    def _real_extract(self, url):
        locale, slug = self._match_valid_url(url).group('locale', 'slug')

        language, _, country = (locale or 'US').rpartition('-')
        parsed_locale = f'{language.lower() or "en"}_{country.upper()}'
        self.write_debug(f'Using locale {parsed_locale} (from {locale})', only_once=True)

        # graph.nintendo.com currently 500s; Direct pages embed the same payload
        # in Next.js `__NEXT_DATA__` / Apollo cache.
        direct_info = self._extract_direct_info(url, slug, parsed_locale)
        if not direct_info:
            raise ExtractorError(f'No Nintendo Direct with id {slug} exists', expected=True)

        result = traverse_obj(direct_info, {
            'id': ('id', {str}),
            'title': ('name', {str}),
            'timestamp': ('startDate', {unified_timestamp}),
            'description': ('description', 'text', {str}),
            'age_limit': ('contentRating', 'order', {int}),
            'tags': ('contentDescriptors', ..., 'label', {str}),
            'thumbnail': ('thumbnail', 'publicId', {self._create_asset_url}),
        })
        result['display_id'] = slug

        asset_id = traverse_obj(direct_info, ('video', 'publicId', {str}))
        if not asset_id:
            youtube_id = traverse_obj(direct_info, ('liveStream', {str}))
            if not youtube_id:
                self.raise_no_formats('Could not find any video formats', video_id=slug)

            return self.url_result(youtube_id, **result, url_transparent=True)

        if asset_id.startswith('Legacy Videos/'):
            result['_old_archive_ids'] = [make_archive_id(self, asset_id[14:])]
        result['formats'] = self._extract_m3u8_formats(
            self._create_asset_url(f'/video/upload/sp_full_hd/v1/{asset_id}.m3u8'), slug)

        return result
