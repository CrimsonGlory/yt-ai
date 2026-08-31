from .common import InfoExtractor
from ..utils import (
    clean_html,
    clean_podcast_url,
    format_field,
    int_or_none,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class SpotifyPodcastersIE(InfoExtractor):
    IE_NAME = 'spotify:podcasters'
    IE_DESC = 'Spotify for Creators (podcasters.spotify.com)'
    _VALID_URL = r'https?://(?:podcasters|creators)\.spotify\.com/pod/(?:show|profile)/(?P<show>[^/?#]+)/(?:embed/)?episodes/(?:[^/?#]*-)?(?P<id>e[0-9a-z]+)'
    _EMBED_REGEX = [rf'<iframe[^>]+\bsrc=["\'](?P<url>{_VALID_URL})']
    _TESTS = [{
        'url': 'https://podcasters.spotify.com/pod/show/thelolpodcast/episodes/Meet-My-Secret-Girlfriend-e2iukcg',
        'md5': 'baa8e00189700dce33f916909f0f6982',
        'info_dict': {
            'id': 'e2iukcg',
            'ext': 'mp3',
            'title': 'Meet My Secret Girlfriend…',
            'description': 'Maverick Has A Secret Girlfriend!',
            'thumbnail': r're:https://.+\.(?:jpg|png)',
            'duration': 2964,
            'timestamp': 1714232706,
            'upload_date': '20240427',
            'series': 'The LOL Podcast',
            'series_id': 'e49c8c60',
            'episode': 'Meet My Secret Girlfriend…',
            'channel': 'The LOL Podcast',
            'channel_id': 'thelolpodcast',
            'channel_url': 'https://creators.spotify.com/pod/profile/thelolpodcast',
            'creators': ['Cash, Maverick, Kate, Harper, Kenzie'],
            'categories': ['Comedy'],
            'language': 'en',
            'age_limit': 0,
        },
    }, {
        'url': 'https://creators.spotify.com/pod/profile/thelolpodcast/episodes/Meet-My-Secret-Girlfriend-e2iukcg',
        'only_matching': True,
    }, {
        'url': 'https://creators.spotify.com/pod/show/thelolpodcast/episodes/Meet-My-Secret-Girlfriend-e2iukcg',
        'only_matching': True,
    }, {
        'url': 'https://podcasters.spotify.com/pod/show/thelolpodcast/embed/episodes/Meet-My-Secret-Girlfriend-e2iukcg',
        'only_matching': True,
    }]
    _API_BASE = 'https://creators.spotify.com/pod/api/v3'

    def _real_extract(self, url):
        episode_id = self._match_id(url)
        data = self._download_json(
            f'{self._API_BASE}/episodes/{episode_id}', episode_id,
            headers={'Accept': 'application/json'})
        episode = traverse_obj(data, ('episode', {dict}, {require('episode')}))
        if episode.get('isDeleted'):
            self.raise_no_formats('This episode has been deleted', expected=True, video_id=episode_id)

        media_url = traverse_obj(data, (
            (('episodeAudios', ..., ('audioUrl', 'url')),
             ('episode', 'episodeEnclosureUrl')),
            {url_or_none}, {clean_podcast_url}, any))
        if not media_url:
            self.raise_no_formats('No public episode media', expected=True, video_id=episode_id)

        return {
            'id': str_or_none(episode.get('episodeId')) or episode_id,
            'url': media_url,
            'vcodec': 'none',
            **traverse_obj(episode, {
                'title': ('title', {str}),
                'description': ('description', {clean_html}),
                'thumbnail': ('episodeImage', {url_or_none}),
                'duration': ('duration', {int_or_none(scale=1000)}),
                'timestamp': ('publishOn', {parse_iso8601}),
                'episode': ('title', {str}),
                'series_id': ('stationId', {str_or_none}),
                'age_limit': ('podcastEpisodeIsExplicit', {lambda x: 18 if x else 0}),
            }),
            **traverse_obj(data, {
                'series': ('podcastMetadata', 'podcastName', {str}),
                'channel': ('podcastMetadata', 'podcastName', {str}),
                'channel_id': ('creator', 'vanitySlug', {str}),
                'channel_url': ('creator', 'vanitySlug', {str}, {
                    format_field(template='https://creators.spotify.com/pod/profile/%s')}),
                'creators': ('podcastMetadata', 'podcastAuthorName', {str}, filter, all, filter),
                'categories': ('podcastMetadata', 'podcastCategory', {str}, filter, all, filter),
                'language': ('podcastMetadata', 'language', {str}),
            }),
        }


class SpotifyPodcastersShowIE(InfoExtractor):
    IE_NAME = 'spotify:podcasters:show'
    IE_DESC = 'Spotify for Creators shows'
    _VALID_URL = r'https?://(?:podcasters|creators)\.spotify\.com/pod/(?:show|profile)/(?P<id>[^/?#]+)/?(?:$|[?#])'
    _TESTS = [{
        'url': 'https://podcasters.spotify.com/pod/show/thelolpodcast',
        'info_dict': {
            'id': 'thelolpodcast',
            'title': 'The LOL Podcast',
            'description': 'New episodes every WEDNESDAY & SATURDAY!',
        },
        'playlist_mincount': 50,
    }, {
        'url': 'https://creators.spotify.com/pod/profile/thelolpodcast',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if SpotifyPodcastersIE.suitable(url) else super().suitable(url)

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)
        state = self._search_json(r'window\.__STATE__\s*=', webpage, 'state', show_id)

        entries = []
        for episode in traverse_obj(state, (
            'episodePreview', 'episodes', lambda _, v: v.get('episodeId') and not v.get('isDeleted'),
        )):
            episode_id = episode['episodeId']
            path = traverse_obj(episode, ('shareLinkPath', {str}))
            episode_url = (
                f'https://creators.spotify.com/pod/profile{path}' if path
                else f'https://creators.spotify.com/pod/profile/{show_id}/episodes/{episode_id}')
            entries.append(self.url_result(
                episode_url, SpotifyPodcastersIE, episode_id, episode.get('title')))

        return self.playlist_result(
            entries, show_id, **traverse_obj(state, ('station', 'podcastMetadata', {
                'title': ('podcastName', {str}),
                'description': ('podcastDescription', {clean_html}),
            })))
