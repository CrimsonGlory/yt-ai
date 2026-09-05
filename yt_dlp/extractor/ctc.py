from .common import InfoExtractor
from ..utils import (
    int_or_none,
    join_nonempty,
    parse_iso8601,
    str_or_none,
    url_or_none,
    urljoin,
)
from ..utils.traversal import require, traverse_obj


class CTCBaseIE(InfoExtractor):
    _API_BASE = 'https://ctc.ru/api/page/v1/'
    _SITE_ORIGIN = 'https://ctc.ru'

    def _download_page_data(self, path, video_id):
        return self._download_json(
            f'{self._API_BASE}{path.strip("/")}/', video_id, impersonate=True)


class CTCIE(CTCBaseIE):
    IE_NAME = 'ctc'
    IE_DESC = 'СТС'
    _VALID_URL = (
        r'https?://(?:www\.)?ctc\.ru/'
        r'(?P<id>projects/[^/?#]+/[^/?#]+/video/'
        r'(?:(?P<season>\d+)-sezon/(?P<episode>\d+)-(?:serija|vypusk)|\d+))/'
        r'?(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://ctc.ru/projects/serials/molodezhka/video/1-sezon/1-serija/',
        'md5': '52e530738cb771f2636cddd86631914e',
        'info_dict': {
            'id': '98793',
            'ext': 'mp4',
            'display_id': 'projects/serials/molodezhka/video/1-sezon/1-serija',
            'title': 'Молодёжка - 1 серия',
            'description': 'md5:dffcc3f3d627e484ad8721567d513926',
            'duration': 2852,
            'thumbnail': 'md5:992366ffc01de7f8cb83ff44be7093d6',
            'timestamp': 1381168620,
            'upload_date': '20131007',
            'age_limit': 16,
            'series': 'Молодёжка',
            'season': '1 сезон',
            'season_number': 1,
            'episode': '1 серия',
            'episode_number': 1,
        },
    }, {
        'url': 'https://ctc.ru/projects/show/improvizatory/video/1-sezon/1-vypusk/',
        'only_matching': True,
    }, {
        'url': 'https://ctc.ru/projects/serials/molodezhka/video/244692/',
        'only_matching': True,
    }, {
        'url': 'https://www.ctc.ru/projects/serials/molodezhka/video/1-sezon/1-serija/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id')
        page = self._download_page_data(display_id, display_id)
        item = traverse_obj(page, (
            'content', lambda _, v: url_or_none(v.get('videoUrl') or v.get('trackUrl')),
            any, {require('player data')}))
        player_url = traverse_obj(
            item, (('videoUrl', 'trackUrl'), {url_or_none}, any, {require('player URL')}))
        video_id = traverse_obj(item, ('trackHubId', {str_or_none})) or display_id.split('/')[-1]

        playlist = self._download_json(
            player_url.replace('/player/', '/playlist/'), video_id,
            'Downloading playlist JSON', headers={'X-Referer': self._SITE_ORIGIN},
            impersonate=True)
        playlist_item = traverse_obj(
            playlist, ('playlist', 'items', 0, {dict}, {require('playlist item')}))

        formats, subtitles, has_drm = [], {}, False
        seen_urls = set()
        for stream in traverse_obj(playlist_item, ('streams', lambda _, v: url_or_none(v['url']))):
            stream_url = stream['url']
            if stream_url in seen_urls:
                continue
            seen_urls.add(stream_url)
            if stream.get('drm_type'):
                has_drm = True
                continue
            protocol = (stream.get('protocol') or '').upper()
            if protocol == 'HLS':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    stream_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            elif protocol == 'DASH':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    stream_url, video_id, mpd_id='dash', fatal=False)
            else:
                continue
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        error_code = traverse_obj(playlist_item, ('errors', 0, 'code', {int_or_none}))
        if not formats:
            if error_code == 102:
                self.raise_geo_restricted(countries=['RU'])
            if error_code == 103 or playlist_item.get('paid') or item.get('isPaid'):
                self.raise_login_required(
                    'This video is only available for registered users with a subscription')
            if has_drm:
                self.report_drm(video_id)
            self.raise_no_formats(
                traverse_obj(playlist_item, ('errors', 0, 'details', {str})) or 'No video formats found',
                expected=True, video_id=video_id)

        title = join_nonempty(
            traverse_obj(playlist_item, ('project_name', {str})),
            traverse_obj(playlist_item, ('episode_name', {str})),
            delim=' - ') or join_nonempty(
            traverse_obj(item, ('title', {str})),
            traverse_obj(item, ('subtitle', {str})), delim=' - ')
        thumbnails = traverse_obj(item, ('thumbnail', lambda _, v: url_or_none(v['url']), {
            'url': ('url', {url_or_none}),
            'width': ('width', {int_or_none}),
            'height': ('height', {int_or_none}),
        }))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'thumbnail': traverse_obj(playlist_item, ('thumbnail_url', {url_or_none})),
            'season_number': int_or_none(mobj.group('season')),
            'episode_number': int_or_none(mobj.group('episode')),
            **traverse_obj(item, {
                'description': ('description', {str}),
                'age_limit': ('ageLimit', {int_or_none}),
            }),
            **traverse_obj(page, {
                'timestamp': ('ogMarkup', 'trackData', 'uploadDate', {parse_iso8601}),
            }),
            **traverse_obj(playlist_item, {
                'duration': ('duration', {int_or_none}),
                'series': ('project_name', {str}),
                'season': ('season_name', {str}),
                'episode': ('episode_name', {str}),
                'age_limit': ('min_age', {int_or_none}),
            }),
        }


class CTCSeasonIE(CTCBaseIE):
    IE_NAME = 'ctc:season'
    IE_DESC = 'СТС seasons'
    _VALID_URL = (
        r'https?://(?:www\.)?ctc\.ru/'
        r'(?P<id>projects/[^/?#]+/[^/?#]+/video/\d+-sezon)/?'
        r'(?:[?#]|$)')
    _TESTS = [{
        'url': 'https://ctc.ru/projects/serials/molodezhka/video/1-sezon/',
        'playlist_mincount': 20,
        'info_dict': {
            'id': '3729',
            'title': 'Молодёжка',
            'description': 'Сериал Молодежка 1 сезон смотреть онлайн на СТС в хорошем качестве',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        page = self._download_page_data(display_id, display_id)
        season = traverse_obj(page, (
            'content', lambda _, v: v['type'] == 'season-track', any, {dict})) or {}

        entries = []
        for episode in traverse_obj(season, ('widgets', lambda _, v: v.get('popupUrl'))):
            episode_id = traverse_obj(episode, ('trackHubId', {str_or_none}))
            entries.append(self.url_result(
                urljoin(self._SITE_ORIGIN, episode['popupUrl']), CTCIE, episode_id,
                traverse_obj(episode, ('title', {str}))))

        return self.playlist_result(
            entries,
            traverse_obj(season, ('seasonHubId', {str_or_none})) or display_id,
            traverse_obj(season, ('projectName', {str})),
            traverse_obj(season, ('description', {str})))
