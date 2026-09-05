from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PodomaticIE(InfoExtractor):
    IE_NAME = 'podomatic'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?P<channel>[^.]+)\.podomatic\.com/entry|
                            (?:www\.)?podomatic\.com/podcasts/(?P<channel_2>[^/]+)/episodes
                        )/
                        (?P<id>[^/?#&]+)
                '''

    _TESTS = [{
        'url': 'https://www.podomatic.com/podcasts/judgejules/episodes/2026-08-27T21_17_53-07_00',
        'md5': '9ad35fa3b52a62789af982c5ed683285',
        'info_dict': {
            'id': '2026-08-27T21_17_53-07_00',
            'ext': 'mp3',
            'title': 'JUDGE JULES PRESENTS THE GLOBAL WARM UP EPISODE 1173',
            'description': 'md5:d4d892d5fb52e5686d12bd36025cd788',
            'uploader': 'JUDGE JULES PRESENTS THE GLOBAL WARM UP',
            'uploader_id': 'judgejules',
            'duration': 7200,
            'thumbnail': 'https://assets.podomatic.net/ts/5b/af/4e/judgejules/300x300_17860488.jpg?1787902187',
            'timestamp': 1787890673,
            'upload_date': '20260828',
        },
    }, {
        'url': 'http://scienceteachingtips.podomatic.com/entry/2009-01-02T16_03_35-08_00',
        'skip': 'video gone',
        'md5': '84bb855fcf3429e6bf72460e1eed782d',
        'info_dict': {
            'id': '2009-01-02T16_03_35-08_00',
            'ext': 'mp3',
            'uploader': 'Science Teaching Tips',
            'uploader_id': 'scienceteachingtips',
            'title': '64.  When the Moon Hits Your Eye',
            'duration': 446,
        },
    }, {
        'url': 'http://ostbahnhof.podomatic.com/entry/2013-11-15T16_31_21-08_00',
        'skip': 'video gone',
        'md5': 'd2cf443931b6148e27638650e2638297',
        'info_dict': {
            'id': '2013-11-15T16_31_21-08_00',
            'ext': 'mp3',
            'uploader': 'Ostbahnhof / Techno Mix',
            'uploader_id': 'ostbahnhof',
            'title': 'Einunddreizig',
            'duration': 3799,
        },
    }, {
        'url': 'https://www.podomatic.com/podcasts/scienceteachingtips/episodes/2009-01-02T16_03_35-08_00',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        channel = mobj.group('channel') or mobj.group('channel_2')

        webpage = self._download_webpage(url, video_id)
        episode_guid = self._search_regex(
            r'(?:podomatic://episode/|/embed/html5/episode/)(\d+)',
            webpage, 'episode id', default=None)

        episode = {}
        if episode_guid:
            api = self._download_json(
                f'https://www.podomatic.com/v2/episodes/{episode_guid}',
                video_id, query={'podcast': 'true'}, fatal=False)
            episode = traverse_obj(api, ('episode', {dict})) or {}

        json_ld = self._search_json_ld(webpage, video_id, default={})
        video_url = (
            url_or_none(episode.get('download_media_url'))
            or url_or_none(episode.get('media_url'))
            or url_or_none(json_ld.get('url') or json_ld.get('contentUrl'))
            or self._og_search_property('audio', webpage, default=None)
            or self._og_search_video_url(webpage, default=None)
            or f'https://{channel}.podomatic.com/enclosure/{video_id}.mp3')

        return {
            'id': video_id,
            'url': video_url,
            'vcodec': 'none',
            'title': (
                episode.get('title')
                or json_ld.get('title')
                or self._og_search_title(webpage, default=video_id)),
            'description': (
                clean_html(episode.get('description_html'))
                or episode.get('description')
                or json_ld.get('description')
                or self._og_search_description(webpage)),
            'uploader': (
                episode.get('podcast_title')
                or traverse_obj(episode, ('profile', 'profile_name', {str}))
                or json_ld.get('uploader')
                or channel),
            'uploader_id': episode.get('podcast_subdomain') or channel,
            'thumbnail': (
                url_or_none(episode.get('large_image_url'))
                or url_or_none(episode.get('xl_image_url'))
                or url_or_none(episode.get('image_url'))
                or json_ld.get('thumbnails')
                or self._og_search_thumbnail(webpage)),
            'duration': int_or_none(episode.get('duration')),
            'timestamp': unified_timestamp(episode.get('published_datetime')),
        }
