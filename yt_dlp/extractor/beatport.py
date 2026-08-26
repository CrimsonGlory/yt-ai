from .common import InfoExtractor
from ..utils import (
    float_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class BeatportIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|pro\.)?beatport\.com/track/(?P<display_id>[^/?#]+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://beatport.com/track/synesthesia-original-mix/5379371',
        'md5': 'cfcc245aafcad52a837b2c5a60a472c9',
        'info_dict': {
            'id': '5379371',
            'display_id': 'synesthesia-original-mix',
            'ext': 'mp3',
            'title': 'Froxic - Synesthesia (Original Mix)',
            'track': 'Synesthesia',
            'artists': ['Froxic'],
            'album': 'Synesthesia',
            'duration': 337.968,
            'timestamp': 1398643200,
            'upload_date': '20140428',
            'thumbnail': r're:https://geo-media\.beatport\.com/.+',
            'genres': ['Mainstage'],
        },
    }, {
        'url': 'https://beatport.com/track/love-and-war-original-mix/3756896',
        'only_matching': True,
    }, {
        'url': 'https://beatport.com/track/birds-original-mix/4991738',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, track_id = self._match_valid_url(url).group('display_id', 'id')
        webpage = self._download_webpage(url, display_id, impersonate=True)
        track = traverse_obj(
            self._search_nextjs_data(webpage, track_id),
            ('props', 'pageProps', 'track', {dict}))
        if not track:
            self.raise_no_formats('Unable to extract track metadata', video_id=track_id)

        artists = traverse_obj(track, ('artists', ..., 'name', {str}))
        title = track['name']
        if artists:
            title = f'{", ".join(artists)} - {title}'
        mix = traverse_obj(track, ('mix_name', {str}))
        if mix:
            title = f'{title} ({mix})'

        sample_url = traverse_obj(track, ('sample_url', {url_or_none}))
        if not sample_url:
            self.raise_no_formats('No preview is available for this track', expected=True, video_id=track_id)

        thumbnails, seen = [], set()
        for thumb_id, path in (('image', ('image', 'uri')), ('cover', ('release', 'image', 'uri'))):
            image_url = traverse_obj(track, (*path, {url_or_none}))
            if image_url and image_url not in seen:
                seen.add(image_url)
                thumbnails.append({
                    'id': thumb_id,
                    'url': image_url,
                })

        return {
            'id': track_id,
            'display_id': display_id,
            'title': title,
            'track': traverse_obj(track, ('name', {str})),
            'artists': artists or None,
            'album': traverse_obj(track, ('release', 'name', {str})),
            'duration': float_or_none(track.get('length_ms'), scale=1000),
            'timestamp': unified_timestamp(track.get('publish_date')),
            'thumbnails': thumbnails,
            'genres': traverse_obj(track, ('genre', 'name', {str}, filter, all)),
            'formats': [{
                'url': sample_url,
                'format_id': 'sample',
                'ext': 'mp3',
                'vcodec': 'none',
                'acodec': 'mp3',
            }],
        }
