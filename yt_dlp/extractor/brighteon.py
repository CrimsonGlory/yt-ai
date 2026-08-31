import functools

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    OnDemandPagedList,
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    mimetype2ext,
    parse_iso8601,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class BrighteonIE(InfoExtractor):
    IE_NAME = 'brighteon'
    IE_DESC = 'Brighteon'
    _VALID_URL = r'https?://(?:www\.)?brighteon\.com/(?:embed/)?(?P<id>[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})'
    _EMBED_REGEX = [rf'<(?:iframe|script)[^>]+\bsrc=(["\'])(?P<url>{_VALID_URL})']
    _TESTS = [{
        'url': 'https://www.brighteon.com/90b78697-72f1-4468-9972-e3a654bccebe',
        'md5': '7ebe335f25cb90066b89463008acc06c',
        'info_dict': {
            'id': '90b78697-72f1-4468-9972-e3a654bccebe',
            'ext': 'mp4',
            'title': 'Why Fruits & Vegetables Have Lost Their Vitamins - Documentary - HaloRockDocs',
            'description': 'md5:94867febeb1f685d6064eeb447491174',
            'thumbnail': r're:https?://photos\.brighteon\.com/.+',
            'duration': 3007.96,
            'timestamp': 1695595835,
            'upload_date': '20230924',
            'channel': 'HaloRock™',
            'channel_id': '14818bc8-ad15-419f-9aeb-aa4b01696fc8',
            'channel_url': 'https://www.brighteon.com/channels/HaloRock',
            'uploader': 'patblack',
            'uploader_id': '35d470d2-1cf4-4073-afae-69afb031ca85',
            'channel_follower_count': int,
            'like_count': int,
            'view_count': int,
            'tags': ['vegetables', 'lost', 'documentary', 'why', 'fruits', 'vitamins', 'their', 'halorock', 'halorockdocs'],
            'categories': ['Food & Recipes'],
        },
        'params': {'format': 'dash-1'},
    }, {
        'url': 'https://www.brighteon.com/embed/90b78697-72f1-4468-9972-e3a654bccebe',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = traverse_obj(
            self._search_nextjs_data(webpage, video_id),
            ('props', 'pageProps', {dict})) or {}
        video = traverse_obj(page_props, ('video', {dict}))
        if not video:
            raise ExtractorError('Unable to extract video data', expected=True)

        formats, subtitles = [], {}
        for source in traverse_obj(video, ('source', ..., {dict})):
            src = url_or_none(source.get('src'))
            if not src:
                continue
            ext = determine_ext(src) or mimetype2ext(source.get('type'))
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', m3u8_id='hls', fatal=False)
            elif ext == 'mpd':
                try:
                    fmts, subs = self._extract_mpd_formats_and_subtitles(
                        src, video_id, mpd_id='dash', fatal=False)
                except KeyError as e:
                    self.report_warning(f'MPD extraction failed: {e}')
                    continue
            else:
                formats.append({
                    'url': src,
                    'ext': ext,
                    'format_id': ext,
                })
                continue
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        audio_url = traverse_obj(video, ('audio', {url_or_none}))
        if audio_url:
            formats.append({
                'format_id': 'http-audio',
                'url': audio_url,
                'vcodec': 'none',
                'ext': determine_ext(audio_url, 'mp3'),
            })

        if not formats:
            if video.get('isPremium'):
                self.raise_login_required(
                    'This video is only available to Brighteon premium members')
            if video.get('isUpcoming'):
                self.raise_no_formats('This video has not been published yet', expected=True)
            self.raise_no_formats('No video formats found', expected=True)

        channel = traverse_obj(page_props, ('channel', {dict})) or {}
        channel_slug = traverse_obj(channel, ('shortUrl', {str}))

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(video, {
                'title': ('name', {str}),
                'description': ('description', {clean_html}),
                'thumbnail': (('thumbnail', 'poster'), {url_or_none}, any),
                'duration': ('durationMS', {float_or_none(scale=1000)}),
                'timestamp': ('createdAt', {parse_iso8601}),
                'tags': ('tags', ..., {str}),
                'like_count': ('likes', {int_or_none}),
                'view_count': ('analytics', 'videoView', {int_or_none}),
                'categories': ('categoryName', {str}, filter, all),
            }),
            **traverse_obj(channel, {
                'channel': ('name', {str}),
                'channel_id': ('id', {str}),
                'uploader': ('userName', {str}),
                'uploader_id': ('ownerId', {str}),
                'channel_follower_count': ('subscriptions', {int_or_none}),
            }),
            'channel_url': (
                f'https://www.brighteon.com/channels/{channel_slug}' if channel_slug else None),
        }


class BrighteonChannelIE(InfoExtractor):
    IE_NAME = 'brighteon:channel'
    IE_DESC = 'Brighteon channels'
    _VALID_URL = r'https?://(?:www\.)?brighteon\.com/channels/(?P<id>[^/?#]+)'
    _PAGE_SIZE = 60
    _TESTS = [{
        'url': 'https://www.brighteon.com/channels/HFamily',
        'info_dict': {
            'id': 'f44cede8-8896-4344-9a68-0cba31c639db',
            'title': 'Hagenaars Family',
            'description': 'md5:b5e69f50f59f985a141925927eb0c634',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'https://www.brighteon.com/channels/brighteontv',
        'only_matching': True,
    }]

    def _fetch_page(self, channel_slug, page):
        data = self._download_json(
            f'https://www.brighteon.com/api-v3/channels/{channel_slug}/videos',
            channel_slug, f'Downloading videos page {page + 1}',
            query={'page': page + 1})
        for video in traverse_obj(data, ('videos', lambda _, v: v['id'])):
            video_id = video['id']
            yield self.url_result(
                f'https://www.brighteon.com/{video_id}', BrighteonIE,
                video_id, video.get('name'))

    def _real_extract(self, url):
        channel_slug = self._match_id(url)
        channel = traverse_obj(self._download_json(
            f'https://www.brighteon.com/api-v3/channels/{channel_slug}',
            channel_slug, 'Downloading channel metadata'), ('channel', {dict})) or {}
        return self.playlist_result(
            OnDemandPagedList(
                functools.partial(self._fetch_page, channel_slug), self._PAGE_SIZE),
            playlist_id=traverse_obj(channel, ('id', {str})) or channel_slug,
            playlist_title=traverse_obj(channel, ('name', {str})) or channel_slug,
            playlist_description=traverse_obj(channel, ('description', {clean_html})))
