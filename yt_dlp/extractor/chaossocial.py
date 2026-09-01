from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    truncate_string,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ChaosSocialIE(InfoExtractor):
    IE_NAME = 'chaos.social'
    IE_DESC = 'chaos.social'
    _VALID_URL = r'https?://(?:www\.)?chaos\.social/(?:web/|deck/)?(?:@[^/#?]+|users/[^/#?]+/statuses)/(?P<id>\d+)'
    _TESTS = [{
        # Federated video from yt-dlp#5589
        'url': 'https://chaos.social/web/@strassenkrampf@mastodon.social/109355027724966618',
        'md5': '7723aeea4bb111382898c1114f0e5600',
        'info_dict': {
            'id': '109355027724966618',
            'ext': 'mp4',
            'title': 'Alles wie immer, in der halb fertigen Fahrradstraße #Charlottenstraße.',
            'description': 'Alles wie immer, in der halb fertigen Fahrradstraße #Charlottenstraße.',
            'uploader': 'Straßenkrampf',
            'uploader_id': 'strassenkrampf@mastodon.social',
            'uploader_url': 'https://mastodon.social/@strassenkrampf',
            'thumbnail': r're:https://.+\.png',
            'duration': float,
            'timestamp': 1668625299,
            'upload_date': '20221116',
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
            'tags': ['Charlottenstraße'],
            'age_limit': 0,
            'language': 'en',
        },
    }, {
        # Local audio from yt-dlp#5589
        'url': 'https://chaos.social/@wikinaut/109367413999728260',
        'md5': 'd70b7bfbc7539941626ef42c51b0538b',
        'info_dict': {
            'id': '109367413999728260',
            'ext': 'mp3',
            'title': '@ceelight',
            'alt_title': 'Shaft (Intro)',
            'description': '@ceelight',
            'uploader': 'Wikinaut',
            'uploader_id': 'wikinaut',
            'uploader_url': 'https://chaos.social/@wikinaut',
            'duration': float,
            'timestamp': 1668814300,
            'upload_date': '20221118',
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
            'age_limit': 0,
            'language': 'de',
            'vcodec': 'none',
        },
    }, {
        'url': 'https://chaos.social/web/@wikinaut@chaos.social/109367413999728260',
        'only_matching': True,
    }, {
        'url': 'https://chaos.social/users/wikinaut/statuses/109367413999728260',
        'only_matching': True,
    }, {
        'url': 'https://chaos.social/@strassenkrampf@mastodon.social/109355027724966618',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        status = self._download_json(
            f'https://chaos.social/api/v1/statuses/{video_id}', video_id,
            headers={'Accept': 'application/json'})
        status = traverse_obj(status, ('reblog', {dict})) or status

        if traverse_obj(status, ('visibility', {str})) in ('private', 'direct'):
            self.raise_login_required('This post is private')

        attachments = traverse_obj(status, (
            'media_attachments', lambda _, v: (
                v['type'] in ('video', 'gifv', 'audio')
                and url_or_none(v.get('url') or v.get('remote_url'))), {dict}))
        if not attachments:
            self.raise_no_formats(
                'No video or audio attachment in this post', expected=True, video_id=video_id)

        description = clean_html(status.get('content')) or None
        uploader = strip_or_none(traverse_obj(
            status, ('account', 'display_name', {str}))) or traverse_obj(
            status, ('account', 'username', {str}))
        title = truncate_string(description, left=72) or (
            f'{uploader} on chaos.social' if uploader else f'chaos.social #{video_id}')
        common = {
            'title': title,
            'description': description,
            'age_limit': 18 if status.get('sensitive') else 0,
            **traverse_obj(status, {
                'timestamp': ('created_at', {parse_iso8601}),
                'uploader_id': ('account', 'acct', {str}),
                'uploader_url': ('account', 'url', {url_or_none}),
                'like_count': ('favourites_count', {int_or_none}),
                'comment_count': ('replies_count', {int_or_none}),
                'repost_count': ('reblogs_count', {int_or_none}),
                'tags': ('tags', ..., 'name', {str}),
                'language': ('language', {str}),
            }),
            'uploader': uploader,
        }

        entries = [
            self._extract_attachment(video_id, media, idx, common)
            for idx, media in enumerate(attachments)]
        if len(entries) == 1:
            entries[0]['id'] = video_id
            return entries[0]
        return self.playlist_result(entries, video_id, title, description)

    def _extract_attachment(self, status_id, media, idx, common):
        media_url = url_or_none(media.get('url')) or url_or_none(media.get('remote_url'))
        orig = traverse_obj(media, ('meta', 'original', {dict})) or {}
        is_audio = media.get('type') == 'audio'
        ext = determine_ext(media_url, 'mp3' if is_audio else 'mp4')

        return {
            **common,
            'id': f'{status_id}-{idx}',
            'alt_title': strip_or_none(media.get('description')),
            'thumbnail': url_or_none(media.get('preview_url')) or url_or_none(
                media.get('preview_remote_url')),
            'duration': float_or_none(orig.get('duration')),
            'formats': [{
                'url': media_url,
                'ext': ext,
                'width': int_or_none(orig.get('width')),
                'height': int_or_none(orig.get('height')),
                'tbr': int_or_none(orig.get('bitrate'), scale=1000),
                'fps': self._parse_frame_rate(orig.get('frame_rate')),
                'vcodec': 'none' if is_audio else None,
            }],
        }

    @staticmethod
    def _parse_frame_rate(value):
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return None
        num, sep, den = value.partition('/')
        n = float_or_none(num)
        if not sep:
            return n
        d = float_or_none(den)
        return n / d if n is not None and d else None
