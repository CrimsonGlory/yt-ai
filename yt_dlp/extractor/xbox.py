from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class XboxIE(InfoExtractor):
    IE_NAME = 'xbox'
    IE_DESC = 'Xbox store trailers'
    _VALID_URL = r'(?i)https?://(?:www\.)?xbox\.com/(?:(?P<locale>[a-z]{2}(?:-[a-z]{2})?)/)?games/store/[^/?#]+/(?P<id>[0-9a-z]{12})'
    _TESTS = [{
        'url': 'https://www.xbox.com/en-us/games/store/omori/9p8wmq1s4tf9',
        'md5': '8d725854bd0310284181b61f8a33abb5',
        'info_dict': {
            'id': 'ebaa9ba3-843d-1b12-dfa4-5f6c76e471cd',
            'ext': 'mp4',
            'display_id': '9P8WMQ1S4TF9',
            'title': 'OMORI Trailer',
            'alt_title': 'HeroTrailer',
            'description': 'md5:292d85629dc579b138406d670add3e4f',
            'thumbnail': r're:https?://store-images\.s-microsoft\.com/.+',
            'creator': 'OMOCAT',
            'creators': ['OMOCAT'],
            'uploader': 'OMOCAT',
            'age_limit': 18,
            'series': 'OMORI',
            'series_id': '9P8WMQ1S4TF9',
            'width': 1920,
            'height': 1080,
        },
        'params': {
            'format': 'bestvideo[protocol=https]',
        },
    }, {
        'url': 'https://www.xbox.com/en-US/games/store/bloomtown-a-different-story/9pkvs1b3jztp',
        'info_dict': {
            'id': '9PKVS1B3JZTP',
            'title': 'Bloomtown: A Different Story',
            'description': 'md5:e592eb3810a9af9a0644802be7b292af',
        },
        'playlist_mincount': 3,
    }, {
        'url': 'https://www.xbox.com/en-GB/games/store/omori/9P8WMQ1S4TF9',
        'only_matching': True,
    }, {
        'url': 'https://www.xbox.com/en-us/games/store/omori/9p8wmq1s4tf9/0010',
        'only_matching': True,
    }]
    _CATALOG_URL = 'https://displaycatalog.mp.microsoft.com/v7.0/products'
    _TRAILER_ID_RE = r'([0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})'

    def _catalog_locale(self, locale):
        locale = (locale or 'en-US').replace('_', '-')
        lang, _, region = locale.partition('-')
        market = (region or 'US').upper()
        return f'{lang.lower()}-{market}', market

    def _trailer_id(self, trailer, product_id, idx):
        return (
            str_or_none(trailer.get('TrailerId'))
            or self._search_regex(
                self._TRAILER_ID_RE,
                trailer.get('HLS') or trailer.get('DASH') or trailer.get('Uri') or trailer.get('url') or '',
                'trailer id', default=None)
            or f'{product_id}-{idx}')

    def _extract_trailer_formats(self, trailer, video_id):
        formats, subtitles = [], {}
        hls = url_or_none(self._proto_relative_url(trailer.get('HLS') or trailer.get('url')))
        dash = url_or_none(self._proto_relative_url(trailer.get('DASH')))
        uri = url_or_none(self._proto_relative_url(trailer.get('Uri')))
        cc = url_or_none(self._proto_relative_url(trailer.get('CC')))

        if hls:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                hls, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if dash:
            fmts, subs = self._extract_mpd_formats_and_subtitles(
                dash, video_id, mpd_id='dash', fatal=False)
            for fmt in fmts:
                fmt['preference'] = 1
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        if uri and uri not in (hls, dash):
            ext = determine_ext(uri)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    uri, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    uri, video_id, mpd_id='dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append({
                    'url': uri,
                    'ext': ext or 'mp4',
                    'format_id': 'http',
                    'width': int_or_none(trailer.get('Width')),
                    'height': int_or_none(trailer.get('Height')),
                    'filesize': int_or_none(trailer.get('FileSizeInBytes')),
                    'vcodec': trailer.get('VideoEncoding') or None,
                    'acodec': trailer.get('AudioEncoding') or None,
                })
        if cc:
            subtitles.setdefault('en', []).append({'url': cc})
        return formats, subtitles

    def _extract_trailer(self, trailer, product_id, product_title, metadata, idx):
        video_id = self._trailer_id(trailer, product_id, idx)
        formats, subtitles = self._extract_trailer_formats(trailer, video_id)
        if not formats:
            return None
        self._remove_duplicate_formats(formats)
        title = trailer.get('Caption') or trailer.get('title') or product_title
        thumbnail = url_or_none(self._proto_relative_url(
            traverse_obj(trailer, ('PreviewImage', 'Uri'))
            or traverse_obj(trailer, ('previewImage', 'url'))))
        return {
            **metadata,
            'id': video_id,
            'display_id': product_id,
            'title': title,
            'alt_title': trailer.get('VideoPurpose') or trailer.get('purpose'),
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
            'width': int_or_none(trailer.get('Width')),
            'height': int_or_none(trailer.get('Height')),
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        product_id = mobj.group('id').upper()
        language, market = self._catalog_locale(mobj.group('locale'))

        catalog = self._download_json(self._CATALOG_URL, product_id, query={
            'bigIds': product_id,
            'market': market,
            'languages': language,
        })
        product = traverse_obj(catalog, ('Products', 0, {dict}))
        if not product:
            raise ExtractorError(f'Xbox product {product_id} not found', expected=True)

        lp = traverse_obj(product, ('LocalizedProperties', 0, {dict})) or {}
        product_title = lp.get('ProductTitle')
        description = lp.get('ProductDescription')
        metadata = {
            'series': product_title,
            'series_id': product_id,
            'description': description,
            'creator': lp.get('DeveloperName'),
            'uploader': lp.get('PublisherName'),
            'age_limit': traverse_obj(product, ('MarketProperties', 0, 'MinimumUserAge', {int_or_none})),
        }

        entries = []
        seen = set()
        for idx, trailer in enumerate(traverse_obj(lp, (
            ('CMSVideos', 'Videos'), ..., {dict},
        )), 1):
            entry = self._extract_trailer(trailer, product_id, product_title, metadata, idx)
            if not entry or entry['id'] in seen:
                continue
            seen.add(entry['id'])
            entries.append(entry)

        if not entries:
            raise ExtractorError(
                f'No trailers found for {product_title or product_id}', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, product_id, product_title, description)
