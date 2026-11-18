from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    mimetype2ext,
    parse_age_limit,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class XumoIE(InfoExtractor):
    IE_NAME = 'xumo'
    IE_DESC = 'XUMO'
    _VALID_URL = r'https?://(?:www\.)?play\.xumo\.com/(?:[^/?#]+/)+(?P<id>XM[0-9A-Z]{12})'
    _API_BASE = 'https://valencia-app-mds.xumo.com/v2/assets/asset'
    _ASSET_FIELDS = (
        'availableSince', 'connectorId', 'contentType', 'descriptions',
        'episode', 'episodes.episodeTitle', 'genres', 'keywords',
        'originalReleaseYear', 'providers', 'ratings', 'runtime',
        'season', 'season:all', 'seasons', 'title',
    )
    _TESTS = [{
        'url': 'https://play.xumo.com/tv-shows/primal-grill-with-steven-raichlen/XM098RB18OIA8N/XM0LF9UVQRIEDZ',
        'md5': 'f82751795c0b19f10150fbb58b80817e',
        'info_dict': {
            'id': 'XM0LF9UVQRIEDZ',
            'ext': 'mp4',
            'title': 'Smoke Screen',
            'description': 'md5:489bc661f39150ed5040eb74de6fda18',
            'duration': 1442,
            'thumbnail': r're:https?://image\.xumo\.com/.+',
            'timestamp': 1745622030,
            'upload_date': '20250425',
            'release_year': 2008,
            'age_limit': 0,
            'series': 'Primal Grill with Steven Raichlen',
            'series_id': 'XM098RB18OIA8N',
            'season': 'Season 1',
            'season_number': 1,
            'episode': 'Smoke Screen',
            'episode_number': 1,
            'genres': ['Cooking'],
            'tags': ['barbecue', 'grilling', 'smoking', 'cooking instruction', 'hot-smoking'],
        },
    }, {
        'url': 'https://play.xumo.com/tv-shows/primal-grill-with-steven-raichlen/XM098RB18OIA8N',
        'info_dict': {
            'id': 'XM098RB18OIA8N',
            'title': 'Primal Grill with Steven Raichlen',
        },
        'playlist_mincount': 39,
    }, {
        'url': 'https://play.xumo.com/free-movies/lone-star-shark/XM08RIB78GYPVR',
        'only_matching': True,
    }, {
        'url': 'https://play.xumo.com/networks/outdoor-america/99991374/XM09CDP4IRREOU/33877',
        'only_matching': True,
    }, {
        'url': 'https://www.play.xumo.com/free-movies/lone-star-shark/XM08RIB78GYPVR',
        'only_matching': True,
    }]

    def _call_asset_api(self, asset_id, video_id=None, note=None, fatal=True, fields=None):
        return self._download_json(
            f'{self._API_BASE}/{asset_id}.json', video_id or asset_id,
            note=note or 'Downloading asset JSON', fatal=fatal,
            query={'f': ','.join(fields or self._ASSET_FIELDS)})

    def _extract_formats_and_subtitles(self, asset, video_id):
        formats, subtitles = [], {}
        for source in traverse_obj(asset, (
            'providers', ..., 'sources', lambda _, v: url_or_none(v['uri']),
        )):
            produces = source.get('produces') or ''
            # Skip device-specific HLS variants (rtp/tv/vizio).
            if ';' in produces:
                continue
            src = source['uri']
            ext = mimetype2ext(produces) or determine_ext(src)
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', m3u8_id='hls', fatal=False)
            elif ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    src, video_id, mpd_id='dash', fatal=False)
            else:
                continue
            if source.get('drm'):
                for fmt in fmts:
                    fmt['has_drm'] = True
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        for caption in traverse_obj(asset, (
            'providers', ..., 'captions',
            lambda _, v: url_or_none(v.get('url') or v.get('file')),
        )):
            caption_url = url_or_none(caption.get('url') or caption.get('file'))
            subtitles.setdefault(traverse_obj(caption, ('lang', {str})) or 'und', []).append({
                'url': caption_url,
                'ext': mimetype2ext(caption.get('type')) or determine_ext(caption_url),
            })
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        asset = self._call_asset_api(video_id)

        if asset.get('contentType') == 'SERIES':
            entries = []
            for episode in traverse_obj(asset, (
                'seasons', ..., 'episodes', lambda _, v: str_or_none(v.get('id')),
            )):
                episode_id = episode['id']
                entries.append(self.url_result(
                    f'https://play.xumo.com/tv-shows/_/{episode_id}',
                    ie=self.ie_key(), video_id=episode_id,
                    video_title=traverse_obj(episode, (
                        ('episodeTitle', 'title'), {str}, any))))
            return self.playlist_result(
                entries, video_id, traverse_obj(asset, ('title', {str})))

        formats, subtitles = self._extract_formats_and_subtitles(asset, video_id)
        if not formats:
            self.raise_no_formats('No playable sources found', expected=True, video_id=video_id)

        is_episode = asset.get('contentType') == 'EPISODIC'
        connector_id = traverse_obj(asset, ('connectorId', {str}))
        series = None
        if is_episode and connector_id and connector_id != video_id:
            series = traverse_obj(self._call_asset_api(
                connector_id, video_id, note='Downloading series JSON',
                fatal=False, fields=('title',)), ('title', {str}))

        info = {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': f'https://image.xumo.com/v1/assets/asset/{video_id}/800x450.webp',
            **traverse_obj(asset, {
                'title': ('title', {str}),
                'description': ('descriptions', ('large', 'medium', 'small', 'tiny'), {str}, filter, any),
                'duration': ('runtime', {int_or_none}),
                'release_year': ('originalReleaseYear', {int_or_none}),
                'timestamp': ('availableSince', {unified_timestamp}),
                'age_limit': ('ratings', ..., 'code', {parse_age_limit}, any),
                'genres': ('genres', ..., 'value', {str}, filter),
                'tags': ('keywords', ..., {str}, filter),
            }),
        }
        if is_episode:
            info.update({
                'series': series,
                'series_id': connector_id,
                **traverse_obj(asset, {
                    'season_number': ('season', {int_or_none}),
                    'episode': ('title', {str}),
                    'episode_number': ('episode', {int_or_none}),
                }),
            })
        return info
