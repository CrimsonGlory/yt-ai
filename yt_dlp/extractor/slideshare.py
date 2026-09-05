import json

from .common import InfoExtractor
from ..networking.exceptions import HTTPError
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class SlideshareIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?slideshare\.net/
        (?:
            slideshows?/(?P<slug>[^/#?]+)/(?P<id>\d+)
            | (?!(?:search|explore|category|account|login|signup|upload)(?:/|$))
              (?P<user>[^/#?]+)/(?P<title>[^/#?]+)
        )
        /?(?:[?#]|$)
    '''
    _TESTS = [{
        'url': 'https://www.slideshare.net/slideshow/slideshare-rebrand-announcement-deck-2025/283262633',
        'md5': '9799a935b278f9de635f0a35b8c60982',
        'info_dict': {
            'id': '283262633',
            'ext': 'webp',
            'title': 'Introducing the new Slideshare',
            'description': 'We\'ve rebranded! Slide through and see what\'s new.',
            'thumbnail': r're:https://cdn\.slidesharecdn\.com/.+',
            'timestamp': 1758239774,
            'upload_date': '20250918',
            'uploader': 'Slideshare',
            'uploader_id': 'Slideshare',
            'uploader_url': 'https://www.slideshare.net/Slideshare',
            'view_count': int,
            'like_count': int,
            'display_id': 'slideshare-rebrand-announcement-deck-2025',
        },
    }, {
        'url': 'http://www.slideshare.net/Dataversity/keynote-presentation-managing-scale-and-complexity',
        'info_dict': {
            'id': '25665706',
            'ext': 'mp4',
            'title': 'Managing Scale and Complexity',
        },
        'skip': 'This slideshow has been removed',
    }, {
        'url': 'https://www.slideshare.net/jimmyfavian/concepto-de-riesgo-2012309',
        'only_matching': True,
    }]
    _API_URL = 'https://api.slidesharecdn.com/graphql'
    _GRAPHQL_QUERY = '''
        query SlideshowByQuery($query: SlideshowQuery!) {
            slideshow(query: $query) {
                ... on SlideshowSingle {
                    id
                    title
                    description
                    thumbnail
                    createdAt
                    views
                    likes
                    strippedTitle
                    user {
                        id
                        login
                        name
                    }
                    slides {
                        ... on ImageUrls {
                            urls {
                                baseUrl
                                jpegSrcset
                            }
                        }
                        ... on ImageSizes {
                            host
                            title
                            imageLocation
                            imageSizes {
                                quality
                                width
                            }
                        }
                    }
                }
                ... on SlideshowLocked { isLocked }
                ... on SlideshowPrivate { isPrivate isViewable }
                ... on SlideshowRemoved { isRemoved }
                ... on SlideshowNotFound { isNotFound }
            }
        }
    '''

    def _call_graphql(self, video_id, slug=None):
        query = {'id': video_id}
        if slug:
            query['strippedTitle'] = slug
        data = self._download_json(
            self._API_URL, video_id,
            data=json.dumps({
                'query': self._GRAPHQL_QUERY,
                'variables': {'query': query},
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://www.slideshare.net',
                'Referer': 'https://www.slideshare.net/',
            },
            impersonate=True)
        return traverse_obj(data, ('data', 'slideshow', {dict})) or {}

    def _extract_slideshow_from_webpage(self, url, display_id):
        try:
            webpage = self._download_webpage(url, display_id, impersonate=True)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status in (404, 410):
                raise ExtractorError(
                    'This slideshow has been removed', expected=True, video_id=display_id) from e
            raise
        return traverse_obj(
            self._search_nextjs_data(webpage, display_id),
            ('props', 'pageProps', 'slideshow', {dict})) or {}

    def _raise_unavailable(self, slideshow, video_id):
        if slideshow.get('isRemoved'):
            raise ExtractorError('This slideshow has been removed', expected=True, video_id=video_id)
        if slideshow.get('isNotFound'):
            raise ExtractorError('Unable to find slideshow', expected=True, video_id=video_id)
        if slideshow.get('isLocked') or (slideshow.get('isPrivate') and not slideshow.get('isViewable')):
            raise ExtractorError('This slideshow is private', expected=True, video_id=video_id)

    def _slide_url(self, slides, index=1):
        host = traverse_obj(slides, ('host', {url_or_none}))
        location = traverse_obj(slides, ('imageLocation', {str}))
        sizes = traverse_obj(slides, ('imageSizes', ..., {dict})) or []
        if host and location and sizes:
            best = max(sizes, key=lambda s: s.get('width') or 0)
            quality, width = best.get('quality'), best.get('width')
            title = traverse_obj(slides, ('title', {str})) or 'slide'
            if quality and width:
                return f'{host.rstrip("/")}/{location}/{quality}/{title}-{index}-{width}.jpg'
        return traverse_obj(slides, ('urls', -1, 'baseUrl', {url_or_none}))

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        slideshow_id = mobj.group('id')
        slug = mobj.group('slug') or mobj.group('title')
        display_id = slideshow_id or slug

        slideshow = None
        if slideshow_id:
            try:
                slideshow = self._call_graphql(slideshow_id, slug)
            except ExtractorError as e:
                if e.expected:
                    raise
                slideshow = None
        if not slideshow or not slideshow.get('id'):
            if slideshow:
                self._raise_unavailable(slideshow, display_id)
            slideshow = self._extract_slideshow_from_webpage(url, display_id)

        self._raise_unavailable(slideshow, display_id)
        slideshow_id = str_or_none(slideshow.get('id')) or slideshow_id
        if not slideshow_id:
            raise ExtractorError('Unable to extract slideshow id')

        slide_url = self._slide_url(slideshow.get('slides'))
        if not slide_url:
            raise ExtractorError('Unable to extract slide image', video_id=slideshow_id)

        user = traverse_obj(slideshow, ('user', {dict})) or {}
        uploader_id = str_or_none(user.get('login'))

        return {
            'id': slideshow_id,
            'display_id': str_or_none(slideshow.get('strippedTitle')) or slug,
            'url': slide_url,
            'ext': 'webp',
            'title': slideshow.get('title') or slug,
            'description': str_or_none(slideshow.get('description')),
            'thumbnail': url_or_none(slideshow.get('thumbnail')),
            'timestamp': unified_timestamp(slideshow.get('createdAt')),
            'uploader': str_or_none(user.get('name')) or uploader_id,
            'uploader_id': uploader_id,
            'uploader_url': f'https://www.slideshare.net/{uploader_id}' if uploader_id else None,
            'view_count': int_or_none(slideshow.get('views')),
            'like_count': int_or_none(slideshow.get('likes')),
        }
