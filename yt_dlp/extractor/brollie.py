import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BrollieIE(InfoExtractor):
    IE_NAME = 'brollie'
    IE_DESC = 'Brollie'
    _VALID_URL = r'https?://(?:www\.)?(?:watch\.)?brollie\.com\.au/apps/(?P<app_id>\d+)/(?P<id>[^?#]+)'
    _TESTS = [{
        'url': 'https://watch.brollie.com.au/apps/845/home/recently-added/freedom',
        'md5': '6703941478b37341b26beb4a8898e827',
        'info_dict': {
            'id': '6a8ed2d63bbc223466bdad9b',
            'ext': 'mp4',
            'display_id': 'freedom',
            'title': 'Freedom',
            'description': 'md5:598c86af6a9cb19a0cb881abe7487885',
            'thumbnail': r're:https?://assets\.maz\.tv/.+',
            'duration': 5871,
            'cast': ['Jon Blake', 'Candy Raymond', 'Jad Capelija'],
            'creators': ['Scott Hicks'],
        },
    }, {
        'url': 'https://watch.brollie.com.au/apps/845/3226659-3327197/a2f4fbcf33028dc3d07a3f641dc360cb-3617160-3721508/02aa61fd38c6793075b70243d3f23148-4403199-4520612',
        'only_matching': True,
    }, {
        'url': 'https://watch.brollie.com.au/apps/845/tv-shows/tv-shows/round-the-twist/round-the-twist-season-1',
        'only_matching': True,
    }, {
        'url': 'https://brollie.com.au/apps/845/home/recently-added/freedom',
        'only_matching': True,
    }]
    _ORIGIN = 'https://watch.brollie.com.au'
    _API_HEADERS = {
        'Accept': 'application/json',
        'Origin': _ORIGIN,
        'Referer': f'{_ORIGIN}/',
    }
    _LINEAGE_RE = re.compile(
        r'(?:\d+-\d+|[0-9a-f]{8,}-\d+-\d+)(?:/(?:\d+-\d+|[0-9a-f]{8,}-\d+-\d+))*', re.I)
    _config = None
    _policy = None

    def _call_json(self, url, video_id, note='Downloading JSON metadata', **kwargs):
        headers = {**self._API_HEADERS, **kwargs.pop('headers', {})}
        return self._download_json(url, video_id, note, headers=headers, **kwargs)

    def _get_config(self, video_id):
        if self._config is None:
            webpage = self._download_webpage(
                f'{self._ORIGIN}/configuration.js', video_id,
                'Downloading app configuration')
            self._config = self._search_json(
                r'var\s+configData\s*=', webpage, 'config', video_id)
        return self._config

    def _get_policy(self, app_id, api_key, video_id):
        if self._policy is None:
            self._policy = self._call_json(
                'https://api.maz.tv/policy', video_id, 'Downloading geo policy',
                data=json.dumps({
                    'app_id': int(app_id),
                    'key': api_key,
                    'language': 'en',
                }).encode(),
                headers={'Content-Type': 'application/json'})
        return self._policy

    def _download_item_feed(self, app_id, path, policy, api_key, video_id, page=1, param=None):
        if not param:
            param = 'lineage' if self._LINEAGE_RE.fullmatch(path) else 'slug'
        return self._call_json(
            'https://api.maz.tv/v1/item_feeds/list', video_id,
            'Downloading item feed', query={
                'device': 'tv',
                'app_id': app_id,
                'locale_id': policy['locale_id'],
                'language': traverse_obj(policy, ('languages', 0, {str})) or 'en',
                'key': api_key,
                param: path,
                'page': page,
                'per_page': 50,
            })

    def _fetch_item(self, app_id, path, policy, api_key, video_id):
        first_param = 'lineage' if self._LINEAGE_RE.fullmatch(path) else 'slug'
        data = self._download_item_feed(
            app_id, path, policy, api_key, video_id, param=first_param)
        if traverse_obj(data, ('parent', {dict})):
            return data
        other = 'slug' if first_param == 'lineage' else 'lineage'
        return self._download_item_feed(
            app_id, path, policy, api_key, video_id, param=other)

    def _extract_video(self, item, app_id, api_key, policy, display_id):
        cid = traverse_obj(item, ('cid', {str_or_none}))
        if not cid:
            raise ExtractorError('Unable to extract video id', video_id=display_id)

        stream = self._call_json(
            'https://api.maz.tv/v1/streams/anonymous', display_id,
            'Downloading stream metadata',
            data=json.dumps({
                'cid': cid,
                'progress': 0,
                'platform': 'web',
                'first_play': True,
                'key': api_key,
                'app_id': int(app_id),
                'language': traverse_obj(policy, ('languages', 0, {str})) or 'en',
                'locale_id': policy['locale_id'],
            }).encode(),
            headers={'Content-Type': 'application/json'})

        if traverse_obj(stream, 'drm'):
            self.report_drm(display_id)

        error = traverse_obj(stream, ('error', {str}))
        if error:
            if re.search(r'sign in|log in|login', error, re.I):
                self.raise_login_required(error, metadata_available=True)
            raise ExtractorError(error, expected=True, video_id=display_id)

        stream_url = traverse_obj(stream, (
            ('url', ('files', ('m3u8', 'mpd', 'mp4'))), {url_or_none}, any))
        if not stream_url:
            self.raise_login_required(
                'No playback URL returned; this title may require a free Brollie account',
                metadata_available=True)

        video_id = traverse_obj(stream, ('video_id', {str})) or cid
        stream_type = traverse_obj(stream, ('type', {str})) or determine_ext(stream_url)
        if stream_type == 'm3u8' or determine_ext(stream_url) == 'm3u8':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                stream_url, video_id, 'mp4', m3u8_id='hls')
        elif stream_type == 'mpd' or determine_ext(stream_url) == 'mpd':
            formats, subtitles = self._extract_mpd_formats_and_subtitles(
                stream_url, video_id, mpd_id='dash')
        else:
            formats, subtitles = [{'url': stream_url}], {}

        parent_titles = traverse_obj(item, ('parent_titles', ..., {str})) or []
        is_episode = 'Episode' in (item.get('catalogType') or '')

        return {
            'id': video_id,
            'display_id': traverse_obj(item, ('slug_identifier', {str})) or display_id,
            'formats': formats,
            'subtitles': subtitles,
            'cast': traverse_obj(item, ('role', 'actor', {lambda v: re.split(r',\s*', v) if v else None})),
            'creators': traverse_obj(item, ('role', 'director', {lambda v: re.split(r',\s*', v) if v else None})),
            'series': parent_titles[-2] if is_episode and len(parent_titles) >= 2 else None,
            'season': parent_titles[-1] if is_episode and parent_titles else None,
            'age_limit': 18 if item.get('mature') else None,
            'is_live': bool(stream.get('on_air')),
            **traverse_obj(item, {
                'title': ('title', {str}),
                'description': ('summary', {str}),
                'duration': ('duration', {int_or_none}),
                'thumbnail': (('cover', 'previewImage', 'portraitCover'), 'url', {url_or_none}, any),
            }),
        }

    def _entries(self, first_data, app_id, path, policy, api_key, display_id):
        page = 1
        data = first_data
        param = 'lineage' if self._LINEAGE_RE.fullmatch(path) else 'slug'
        while True:
            for item in traverse_obj(data, ('content', ..., {dict})):
                slug = traverse_obj(item, (('slug', 'lineage'), {str}, any))
                if not slug:
                    continue
                yield self.url_result(
                    f'{self._ORIGIN}/apps/{app_id}/{slug}', ie=self.ie_key(),
                    video_id=traverse_obj(item, ('cid', {str_or_none})),
                    video_title=traverse_obj(item, ('title', {str})))
            if data.get('last_page') or not traverse_obj(data, ('content', {list})):
                break
            page += 1
            if page > 50:
                break
            data = self._download_item_feed(
                app_id, path, policy, api_key, display_id, page=page, param=param)

    def _real_extract(self, url):
        app_id, path = self._match_valid_url(url).group('app_id', 'id')
        path = path.strip('/')
        display_id = path.split('/')[-1]

        config = self._get_config(display_id)
        api_key = traverse_obj(config, ('api_key', {str}))
        if not api_key:
            raise ExtractorError('Unable to extract API key')

        policy = self._get_policy(app_id, api_key, display_id)
        if not traverse_obj(policy, ('locale_id', {int_or_none})):
            raise ExtractorError('Unable to extract locale', expected=True)

        data = self._fetch_item(app_id, path, policy, api_key, display_id)
        parent = traverse_obj(data, ('parent', {dict}))
        if not parent:
            raise ExtractorError(
                'Unable to find this title; it may have been removed',
                expected=True, video_id=display_id)

        item_type = parent.get('type')
        if item_type in ('vid', 'video', 'live'):
            return self._extract_video(parent, app_id, api_key, policy, display_id)
        if item_type in ('saved', 'search'):
            raise ExtractorError('This page is not a video', expected=True, video_id=display_id)

        return self.playlist_result(
            self._entries(data, app_id, path, policy, api_key, display_id),
            playlist_id=traverse_obj(parent, ('cid', {str_or_none})) or display_id,
            playlist_title=traverse_obj(parent, ('title', {str})),
            playlist_description=traverse_obj(parent, ('summary', {str})))
