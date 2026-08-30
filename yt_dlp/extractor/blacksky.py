from .bluesky import BlueskyIE
from ..utils import format_field
from ..utils.traversal import traverse_obj


class BlackskyIE(BlueskyIE):
    IE_DESC = 'blacksky.community'
    _VALID_URL = r'https?://(?:www\.)?blacksky\.community/profile/(?P<handle>[\w.:%-]+)/post/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://blacksky.community/profile/did:plc:tpv66pk3fqlpfudmh5zi3hzo/post/3mgjxbnwktk26',
        'md5': '9c215f46738a9b3e1f081fda3485f175',
        'info_dict': {
            'id': '3mgjxbnwktk26',
            'ext': 'mp4',
            'uploader': "DJ ROKO'S INSURANCE ADJUSTER (@Dragoncon for like a lil bit idk)",
            'uploader_id': 'enoch.kim',
            'uploader_url': 'https://blacksky.community/profile/enoch.kim',
            'channel_id': 'did:plc:tpv66pk3fqlpfudmh5zi3hzo',
            'channel_url': 'https://blacksky.community/profile/did:plc:tpv66pk3fqlpfudmh5zi3hzo',
            'thumbnail': r're:https://video\.blacksky\.community/stream/.*\.jpg$',
            'title': 'test',
            'description': 'test',
            'upload_date': '20260308',
            'timestamp': 1772959534,
            'like_count': int,
            'repost_count': int,
            'comment_count': int,
            'tags': [],
        },
    }, {
        'url': 'https://blacksky.community/profile/enoch.kim/post/3mgjxbnwktk26',
        'only_matching': True,
    }]

    def _extract_post(self, handle, post_id):
        query = {
            'uri': f'at://{handle}/app.bsky.feed.post/{post_id}',
            'depth': 0,
            'parentHeight': 0,
        }
        post = traverse_obj(self._download_json(
            'https://api.blacksky.community/xrpc/app.bsky.feed.getPostThread',
            post_id, query=query, fatal=False), ('thread', 'post', {dict}))
        if post:
            return post
        return super()._extract_post(handle, post_id)

    @staticmethod
    def _build_profile_url(path):
        return format_field(path, None, 'https://blacksky.community/profile/%s', default=None)
