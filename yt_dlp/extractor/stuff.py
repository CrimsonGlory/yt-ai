from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    parse_duration,
    parse_iso8601,
    smuggle_url,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class StuffIE(InfoExtractor):
    IE_NAME = 'stuff'
    IE_DESC = 'Stuff.co.nz'
    _VALID_URL = r'https?://(?:www\.)?stuff\.co\.nz/(?:a/)?(?:[\w-]+/){1,2}(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.stuff.co.nz/nz-news/360880160/extraordinary-aerial-video-shows-scale-and-ferocity-tongariro-fire',
        'md5': 'c7db05c8f659ec31e48f25df50228f81',
        'info_dict': {
            'id': '6384842477112',
            'ext': 'mp4',
            'title': 'Extraordinary aerial video shows scale and ferocity of Tongariro fire',
            'description': 'Vision taken from the air shows the fire on Saturday afternoon.',
            'duration': 36.873,
            'timestamp': 1762635539,
            'upload_date': '20251108',
            'uploader_id': '3921507366001',
            'thumbnail': r're:https?://.+\.jpg',
            'tags': ['fire', 'video moments', 'playlist include', 'nz news'],
        },
        'add_ie': [BrightcoveNewIE.ie_key()],
    }, {
        'url': 'https://www.stuff.co.nz/world-news/361026897/dont-panic-theyre-using-human-brains-power-data-centres',
        'info_dict': {
            'id': '361026897',
            'ext': 'mp4',
            'title': 'Don’t panic ... but they’re using human brains to power data centres',
            'description': 'md5:31a70e26c123a02d83d76af55a90364a',
            'uploader': 'Stuff',
            'duration': 99,
            'thumbnail': r're:https://www\.stuff\.co\.nz/media/images/.+',
            'timestamp': 1788064383,
            'upload_date': '20260830',
        },
        'params': {'skip_download': 'm3u8'},
    }, {
        'url': 'https://www.stuff.co.nz/nz-news/361026674/hawkes-bay-braces-severe-gales-snow-moves-alpine-roads',
        'info_dict': {
            'id': '361026674',
            'title': 'Snow could fall in Dunedin and Invercargill, with damaging winds further north',
        },
        'playlist_mincount': 2,
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.stuff.co.nz/a/nz-news/360880160/extraordinary-aerial-video-shows-scale-and-ferocity-tongariro-fire',
        'only_matching': True,
    }, {
        'url': 'https://stuff.co.nz/nz-news/360880160',
        'only_matching': True,
    }]

    _API_URL = 'https://www.stuff.co.nz/api/v1.0/stuff/story/{}'
    _BRIGHTCOVE_URL_TMPL = (
        'https://players.brightcove.net/{account}/{player}_default/index.html?videoId={video_id}')
    _ACCOUNT_PLAYERS = {
        '3921507366001': 'Syx4Zr1Keb',
        '6005208634001': 'zJ82aTPuA',
        '6416072001001': 'xM1wY8GAZ',
    }

    def _brightcove_result(self, account_id, video_id, webpage_url):
        bc_url = self._BRIGHTCOVE_URL_TMPL.format(
            account=account_id,
            player=self._ACCOUNT_PLAYERS.get(account_id, 'default'),
            video_id=video_id)
        return self.url_result(
            smuggle_url(bc_url, {'referrer': webpage_url}), BrightcoveNewIE, video_id)

    def _extract_hosted_formats(self, item, video_id):
        formats, subtitles = [], {}
        sources = traverse_obj(item, ('playback', 'sources', ..., {dict})) or []
        if not sources:
            media_url = url_or_none(item.get('url'))
            if media_url:
                sources = [{'url': media_url}]
        for src in sources:
            media_url = url_or_none(src.get('url'))
            if not media_url:
                continue
            fmt = (src.get('format') or '').lower()
            ext = determine_ext(media_url)
            if fmt == 'hls' or ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                formats.append({
                    'url': media_url,
                    'ext': ext or 'mp4',
                    'format_id': fmt or ext or 'http',
                })
        return formats, subtitles

    def _hosted_entry(self, asset, item, story, display_id):
        formats, subtitles = self._extract_hosted_formats(item, display_id)
        if not formats:
            return None
        return {
            'id': traverse_obj(item, ('assetId', {str_or_none})) or display_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': (
                traverse_obj(asset, ('title', {str}))
                or traverse_obj(story, ('content', 'title', {str}), ('teaser', 'title', {str}))),
            'description': (
                traverse_obj(asset, ('caption', {str}))
                or traverse_obj(story, ('content', 'intro', {str}), ('teaser', 'intro', {str}))),
            'thumbnail': (
                traverse_obj(item, ('poster', {url_or_none}))
                or traverse_obj(story, ('teaser', 'image', 'url', {url_or_none}))),
            'duration': parse_duration(item.get('duration')),
            'timestamp': parse_iso8601(story.get('publishedDate')),
            'uploader': traverse_obj(asset, ('creditline', {str}), ('source', {str})),
        }

    def _asset_entry(self, asset, story, display_id, webpage_url):
        item = traverse_obj(asset, ('item', {dict})) or {}
        bc_id = traverse_obj(item, ('id', {str_or_none}))
        account_id = traverse_obj(item, ('accountId', {str_or_none}))
        if bc_id and account_id:
            return self._brightcove_result(account_id, bc_id, webpage_url)
        if item.get('url') or traverse_obj(item, ('playback', 'sources')):
            return self._hosted_entry(asset, item, story, display_id)
        return None

    def _real_extract(self, url):
        display_id = self._match_id(url)
        story = self._download_json(self._API_URL.format(display_id), display_id)

        assets = []
        hero = traverse_obj(story, ('content', 'asset', {dict}))
        if hero:
            assets.append(hero)
        assets.extend(traverse_obj(story, (
            'content', 'contentBody', 'assets', ..., {dict})) or [])

        entries, seen = [], set()
        for asset in assets:
            item = traverse_obj(asset, ('item', {dict})) or {}
            key = item.get('id') or item.get('url') or item.get('assetId')
            if not key or key in seen:
                continue
            entry = self._asset_entry(asset, story, display_id, url)
            if not entry:
                continue
            seen.add(key)
            entries.append(entry)

        if not entries:
            raise ExtractorError('This article does not have a video.', expected=True)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, display_id, traverse_obj(
                story, ('content', 'title', {str}), ('teaser', 'title', {str})))
