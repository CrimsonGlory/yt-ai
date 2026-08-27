import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    filter_dict,
    float_or_none,
    join_nonempty,
    traverse_obj,
    update_url_query,
    url_or_none,
)


class DailyWireBaseIE(InfoExtractor):
    _GRAPHQL_API = 'https://v2server.dailywire.com/app/graphql'
    _API_HEADERS = {
        'Content-Type': 'application/json',
        'Apollographql-Client-Name': 'DW_WEBSITE',
        'Origin': 'https://www.dailywire.com',
        'Referer': 'https://www.dailywire.com/',
    }
    _GRAPHQL_QUERIES = {
        'episode': (
            'query getEpisodeBySlug($slug:String!){episode(where:{slug:$slug}){'
            'id,title,slug,description,createdAt,image,show{id,name,slug},'
            'segments{audio,video,duration},createdBy{firstName,lastName}}}'),
        'videos': (
            'query getVideoBySlug($slug:String!){video(where:{slug:$slug}){'
            'id,name,slug,description,image,thumbnail,videoURL,duration,'
            'createdBy{firstName,lastName},createdAt}}'),
        'podcasts': (
            'query getPodcastEpisodes($where:PodcastEpisodeWhereInput){'
            'listPodcastEpisode(where:$where){id,title,description,slug,thumbnail,'
            'createdAt,audio,audioMuxPlaybackId,duration}}'),
    }
    _GRAPHQL_PATH = {
        'episode': ('data', 'episode'),
        'videos': ('data', 'video'),
        'podcasts': ('data', 'listPodcastEpisode', 0),
    }
    _JSON_PATH = {
        'episode': (
            ('props', 'pageProps', 'initialEpisode'),
            ('props', 'pageProps', 'episodeData', 'episode'),
        ),
        'videos': (
            ('props', 'pageProps', 'videoData', 'video'),
        ),
        'podcasts': (
            ('props', 'pageProps', 'episode'),
        ),
    }

    def _get_json(self, url):
        sites_type, slug = self._match_valid_url(url).group('sites_type', 'id')
        json_data = self._download_json(
            self._GRAPHQL_API, slug, 'Downloading GraphQL JSON',
            data=json.dumps({
                'query': self._GRAPHQL_QUERIES[sites_type],
                'variables': (
                    {'where': {'slug': slug}} if sites_type == 'podcasts'
                    else {'slug': slug}),
            }).encode(),
            headers=self._API_HEADERS, fatal=False)
        data = traverse_obj(json_data, self._GRAPHQL_PATH[sites_type])
        if data:
            return slug, data

        webpage = self._download_webpage(url, slug, fatal=False)
        json_data = self._search_nextjs_data(webpage, slug, default={}) if webpage else {}
        return slug, traverse_obj(json_data, *self._JSON_PATH[sites_type])


class DailyWireIE(DailyWireBaseIE):
    _VALID_URL = r'https?://(?:www\.)dailywire(?:\.com)/(?P<sites_type>episode|videos)/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.dailywire.com/episode/1-fauci',
        'info_dict': {
            'id': 'ckzsl50xnqpy30850in3v4bu7',
            'ext': 'mp4',
            'display_id': '1-fauci',
            'title': '1. Fauci',
            'description': 'md5:9df630347ef85081b7e97dd30bc22853',
            'thumbnail': 'https://daily-wire-production.imgix.net/episodes/ckzsl50xnqpy30850in3v4bu7/ckzsl50xnqpy30850in3v4bu7-1648237399554.jpg',
            'creators': ['Caroline Roberts'],
            'series_id': 'ckzplm0a097fn0826r2vc3j7h',
            'series': 'China: The Enemy Within',
        },
    }, {
        'url': 'https://www.dailywire.com/episode/ep-124-bill-maher',
        'md5': 'b363fcc98842ab824732bda2cd705b6b',
        'info_dict': {
            'id': 'cl0ngbaalplc80894sfdo9edf',
            'ext': 'mp3',
            'display_id': 'ep-124-bill-maher',
            'title': 'Ep. 124 - Bill Maher',
            'thumbnail': 'https://daily-wire-production.imgix.net/episodes/cl0ngbaalplc80894sfdo9edf/cl0ngbaalplc80894sfdo9edf-1647065568518.jpg',
            'creators': ['Caroline Roberts'],
            'description': 'md5:adb0de584bcfa9c41374999d9e324e98',
            'series_id': 'cjzvep7270hp00786l9hwccob',
            'series': 'The Sunday Special',
        },
    }, {
        'url': 'https://www.dailywire.com/videos/the-hyperions',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        slug, episode_info = self._get_json(url)
        if not episode_info:
            raise ExtractorError('Unable to extract episode information', expected=True)

        urls = traverse_obj(
            episode_info, (('segments', 'videoUrl'), ..., ('video', 'audio')),
            expected_type=url_or_none) or []
        video_url = traverse_obj(episode_info, 'videoURL', 'videoUrl', expected_type=url_or_none)
        if video_url:
            urls.append(video_url)

        playback_id = traverse_obj(episode_info, 'muxPlaybackId')
        if playback_id and not urls:
            urls.append(update_url_query(
                f'https://stream.media.dailywire.com/{playback_id}.m3u8',
                filter_dict({'token': traverse_obj(episode_info, 'muxPlaybackToken')})))

        formats, subtitles = [], {}
        for url in urls:
            if determine_ext(url) != 'm3u8':
                formats.append({'url': url})
                continue
            format_, subs_ = self._extract_m3u8_formats_and_subtitles(url, slug)
            formats.extend(format_)
            self._merge_subtitles(subs_, target=subtitles)
        return {
            'id': episode_info['id'],
            'display_id': slug,
            'title': traverse_obj(episode_info, 'title', 'name'),
            'description': episode_info.get('description'),
            'creator': join_nonempty(
                ('createdBy', 'firstName'), ('createdBy', 'lastName'),
                from_dict=episode_info, delim=' ') or traverse_obj(episode_info, ('host', 'name')),
            'duration': float_or_none(episode_info.get('duration')),
            'is_live': episode_info.get('isLive'),
            'thumbnail': traverse_obj(
                episode_info, 'thumbnail', 'image', ('images', 'thumbnail', 'land'),
                expected_type=url_or_none),
            'formats': formats,
            'subtitles': subtitles,
            'series_id': traverse_obj(episode_info, ('show', 'id')),
            'series': traverse_obj(episode_info, ('show', 'name'), ('show', 'title')),
        }


class DailyWirePodcastIE(DailyWireBaseIE):
    _VALID_URL = r'https?://(?:www\.)dailywire(?:\.com)/(?P<sites_type>podcasts)/(?P<podcaster>[\w-]+/(?P<id>[\w-]+))'
    _TESTS = [{
        'url': 'https://www.dailywire.com/podcasts/morning-wire/get-ready-for-recession-6-15-22',
        'md5': '3d96a2422ae45a5fb65f7c9507bd8b9f',
        'info_dict': {
            'id': 'cl4f01d0w8pbe0a98ydd0cfn1',
            'ext': 'm4a',
            'display_id': 'get-ready-for-recession-6-15-22',
            'title': 'Get Ready for Recession | 6.15.22',
            'description': 'md5:c4afbadda4e1c38a4496f6d62be55634',
            'thumbnail': r're:https://daily-wire-production\.imgix\.net/podcasts/.+',
            'duration': 900.117667,
        },
    }]

    def _real_extract(self, url):
        slug, episode_info = self._get_json(url)
        if not episode_info:
            raise ExtractorError('Unable to extract podcast episode information', expected=True)

        audio_url = url_or_none(episode_info.get('audio'))
        if not audio_url:
            audio_id = traverse_obj(episode_info, 'audioMuxPlaybackId')
            if audio_id:
                audio_url = f'https://stream.media.dailywire.com/{audio_id}/audio.m4a'

        return {
            'id': episode_info['id'],
            'url': audio_url,
            'display_id': slug,
            'title': episode_info.get('title'),
            'duration': float_or_none(episode_info.get('duration')),
            'thumbnail': episode_info.get('thumbnail'),
            'description': episode_info.get('description'),
        }
