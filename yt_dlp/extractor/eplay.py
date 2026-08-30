from .common import InfoExtractor
from ..utils import (
    determine_ext,
    format_field,
    int_or_none,
    mimetype2ext,
    parse_resolution,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class EPlayIE(InfoExtractor):
    IE_NAME = 'eplay'
    IE_DESC = 'ePlay'
    _VALID_URL = r'https?://(?:www\.)?eplay\.com/(?:embed/(?P<embed_user>[^/?#]+)|(?P<user>[^/?#]+)/post)/(?P<id>\d+)(?:/(?P<slug>[^/?#]+))?'
    _TESTS = [{
        'url': 'https://www.eplay.com/lewdneko/post/941547257059160064/harem-in-another-world-vod-part-4',
        'md5': '380981f46a3326f705717087c62f7e34',
        'info_dict': {
            'id': '941547257059160064',
            'ext': 'mp4',
            'title': 'Harem in Another World VOD Part 4',
            'display_id': 'harem-in-another-world-vod-part-4',
            'age_limit': 18,
            'duration': 7493,
            'timestamp': 1769746943,
            'upload_date': '20260130',
            'thumbnail': r're:https://cdn-b\.eplay\.com/.+',
            'uploader': 'lewdneko',
            'uploader_id': '372915739949715456',
            'uploader_url': 'https://www.eplay.com/lewdneko',
            'channel': 'lewdneko',
            'channel_id': '372918831961264129',
            'comment_count': int,
            'like_count': int,
            'categories': ['girls'],
            'width': 1280,
            'height': 720,
        },
    }, {
        'url': 'https://www.eplay.com/lewdneko/post/941547257059160064',
        'only_matching': True,
    }, {
        'url': 'https://www.eplay.com/embed/lewdneko/941547257059160064/941549021707194368',
        'only_matching': True,
    }]

    def _fetch_post(self, video_id, url):
        post = traverse_obj(self._download_json(
            'https://search-cf.eplay.com/posts', video_id, query={'id': video_id},
            fatal=False, headers={
                'Origin': 'https://www.eplay.com',
                'Referer': 'https://www.eplay.com/',
            }), ('results', 0, {dict}))
        if post:
            return post

        webpage = self._download_webpage(url, video_id)
        return traverse_obj(self._search_nextjs_data(webpage, video_id), (
            'props', 'pageProps', 'dehydratedState', 'queries',
            lambda _, v: traverse_obj(v, ('queryKey', 0, 'postId')) == video_id,
            'state', 'data', {dict}, any, {require('post data')}))

    def _parse_media_formats(self, media, video_id):
        formats, subtitles, hls_urls, master = [], {}, [], None
        for fmt in traverse_obj(media, ('formats', lambda _, v: url_or_none(v['url']))):
            media_url = fmt['url']
            ext = mimetype2ext(fmt.get('mimetype')) or determine_ext(media_url)
            label = str_or_none(fmt.get('label'))
            if ext == 'm3u8':
                if label == 'playlist':
                    master = media_url
                else:
                    hls_urls.append(media_url)
                continue
            formats.append({
                'url': media_url,
                'ext': ext,
                'format_id': label,
                'filesize': int_or_none(fmt.get('filesize')) or None,
                'fps': int_or_none(fmt.get('fps')) or None,
                'preference': 1,
                **parse_resolution(fmt.get('size')),
            })

        for hls_url in ((master,) if master else hls_urls):
            if not hls_url:
                continue
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                hls_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)
        return formats, subtitles

    def _extract_video(self, post, media, video_id, username):
        formats, subtitles = self._parse_media_formats(media, video_id)
        if not formats:
            if post.get('unlocked') is False or int_or_none(post.get('price')):
                self.raise_login_required('This post is locked for subscribers or purchasers')
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        uploader = traverse_obj(post, (('author', 'channelOwner'), 'name', {str}, any)) or username
        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'age_limit': 18,
            'display_id': traverse_obj(post, ('slug', {str})),
            'uploader': uploader,
            'uploader_url': format_field(uploader, template='https://www.eplay.com/%s'),
            **traverse_obj(post, {
                'title': ('title', {str}),
                'timestamp': ('publishDate', {unified_timestamp}),
                'uploader_id': ('author', 'id', {str_or_none}),
                'channel': ('channelOwner', 'name', {str}),
                'channel_id': ('channelId', {str_or_none}),
                'comment_count': ('commentsCount', {int_or_none}),
                'like_count': ('reactionsCount', {int_or_none}),
                'categories': ('category', {str}, filter, all, filter),
                'tags': ('tags', ..., {str}),
            }),
            **traverse_obj(media, {
                'duration': ('duration', {int_or_none}),
                'width': ('width', {int_or_none}),
                'height': ('height', {int_or_none}),
                'thumbnail': ('thumbnail', 'url', {url_or_none}),
            }),
        }

    def _real_extract(self, url):
        video_id, username, embed_user = self._match_valid_url(url).group('id', 'user', 'embed_user')
        username = username or embed_user
        post = self._fetch_post(video_id, url)

        if post.get('unlocked') is False and not traverse_obj(post, ('media', ..., 'formats', ..., 'url')):
            self.raise_login_required('This post is locked for subscribers or purchasers')

        videos = traverse_obj(post, ('media', lambda _, v: v['type'] == 'video'))
        if not videos:
            self.raise_no_formats('No video found in this post', expected=True)

        entries = [
            self._extract_video(post, media, str_or_none(media.get('id')) or video_id, username)
            for media in videos]
        if len(entries) > 1:
            return self.playlist_result(
                entries, video_id, traverse_obj(post, ('title', {str})))

        entries[0]['id'] = video_id
        return entries[0]
