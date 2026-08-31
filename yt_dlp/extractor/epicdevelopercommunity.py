import base64
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    parse_iso8601,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class EpicDeveloperCommunityIE(InfoExtractor):
    IE_NAME = 'epicdevelopercommunity'
    IE_DESC = 'Epic Games Developer Community'
    _VALID_URL = [
        r'https?://(?:www\.)?dev\.epicgames\.com/community/learning/(?:[\w-]+)/(?P<id>[0-9A-Za-z]+)(?:/(?:[\w-]+))?/?',
        r'https?://(?:www\.)?dev\.epicgames\.com/community/api/cms/videos/(?P<embed_id>[\w-]+)/embed\.html',
    ]
    _API_BASE = 'https://dev.epicgames.com/community/api'
    _ENTITY_PATHS = {
        'academic_resources': 'academic-resources',
        'community_tutorial': 'tutorials',
        'course': 'courses',
        'knowledge_base': 'knowledge-base',
        'learning_path': 'paths',
        'livestream': 'livestreams',
        'module': 'module',
        'recommended_community_tutorial': 'recommended-community-tutorial',
        'sample_projects': 'sample-projects',
        'talks_and_demos': 'talks-and-demos',
        'tutorial': 'tutorials',
    }
    _TESTS = [
        {
            'url': 'https://dev.epicgames.com/community/learning/talks-and-demos/4ORW/unreal-engine-serialization-best-practices-and-techniques',
            'md5': '6bbf1066932d40f85f64c5e405acdd94',
            'info_dict': {
                'id': '4ORW',
                'ext': 'mp4',
                'title': 'Serialization Best Practices and Techniques',
                'display_id': 'unreal-engine-serialization-best-practices-and-techniques',
                'description': 'md5:fc7dddcf3e6a4bd33dce8d5fd6dbe884',
                'duration': 2927.96,
                'thumbnail': r're:https?://img\.edc-cdn\.net/.+',
                'timestamp': 1698113356,
                'upload_date': '20231024',
                'uploader': 'JackDCondon',
                'uploader_id': 'oLWYa',
                'uploader_url': 'https://dev.epicgames.com/community/profile/oLWYa/JackDCondon',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'tags': ['blueprint', 'c++', 'engine source'],
                'categories': ['Programming & Scripting'],
            },
            'params': {'format': 'dash-1'},
            # DASH --test only fetches the fMP4 init fragment (~1KB), below the default 10KB check
            'file_minsize': None,
        },
        {
            'url': 'https://dev.epicgames.com/community/learning/talks-and-demos/8reP/unreal-engine-can-the-metaverse-sell-cars-unreal-fest-2022',
            'only_matching': True,
        },
        {
            'url': 'https://dev.epicgames.com/community/learning/tutorials/Kl7d/unreal-engine-part-1-character-basics-and-animation-libraries',
            'only_matching': True,
        },
        {
            'url': 'https://dev.epicgames.com/community/learning/livestreams/RBG7/creating-in-fortnite-marketing-more',
            'only_matching': True,
        },
        {
            'url': 'https://dev.epicgames.com/community/learning/courses/xRe/unreal-engine-unreal-futures-careers-in-animation',
            'only_matching': True,
        },
        {
            'url': 'https://dev.epicgames.com/community/api/cms/videos/V_0hmdLF/embed.html',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        embed_id = mobj.groupdict().get('embed_id')
        if embed_id:
            return self._extract_qstv_video(embed_id)

        video_id = mobj.group('id')
        post = self._download_json(
            f'{self._API_BASE}/learning/post.json',
            video_id,
            query={'hash_id': video_id},
            impersonate=True,
            fatal=False,
            expected_status=404,
        )
        if traverse_obj(post, 'hash_id'):
            return self._extract_post(post, video_id)

        course = self._download_json(
            f'{self._API_BASE}/learning/course.json',
            video_id,
            query={'hash_id': video_id},
            impersonate=True,
            fatal=False,
            expected_status=(404, 500),
        )
        if traverse_obj(course, 'hash_id'):
            return self._extract_course(course, video_id)

        raise ExtractorError('Unable to extract Epic Developer Community media', expected=True)

    def _extract_course(self, course, course_id):
        entries = []
        for entity in traverse_obj(course, ('steps', ..., 'links', ..., 'linked_entity', {dict})):
            entity_id = traverse_obj(entity, ('hash_id', {str}))
            path = self._ENTITY_PATHS.get(entity.get('entity_type'))
            if not entity_id or not path:
                continue
            slug = traverse_obj(entity, ('slug', {str}))
            page_url = f'https://dev.epicgames.com/community/learning/{path}/{entity_id}'
            if slug:
                page_url += f'/{slug}'
            entries.append(
                self.url_result(
                    page_url, ie=self.ie_key(), video_id=entity_id, video_title=traverse_obj(entity, ('title', {str})),
                ),
            )
        if not entries:
            self.raise_no_formats('No media found in course', expected=True, video_id=course_id)
        return self.playlist_result(
            entries, course_id, traverse_obj(course, ('title', {str})), traverse_obj(course, ('description', {str})),
        )

    def _extract_post(self, post, video_id):
        blocks = traverse_obj(post, ('blocks', ..., {dict})) or []
        native_ids = [
            ident
            for ident in (
                traverse_obj(b, ((('video', 'identifier'), 'video_id'), {str}, any))
                for b in blocks
                if b.get('type') == 'video'
            )
            if ident
        ]
        entries = []
        use_block_id = len(native_ids) + sum(1 for b in blocks if b.get('type') == 'external_video') > 1

        for block in blocks:
            block_type = block.get('type')
            if block_type == 'video':
                identifier = traverse_obj(block, ((('video', 'identifier'), 'video_id'), {str}, any))
                if not identifier:
                    continue
                media_id = identifier if use_block_id else video_id
                info = self._extract_qstv_video(identifier, media_id)
                info.update(self._metadata_from_post(post, media_id))
                entries.append(info)
            elif block_type == 'external_video':
                ext_url = url_or_none(unescapeHTML(traverse_obj(block, (('original_url', 'url'), {str}, any))))
                if ext_url:
                    entries.append(
                        self.url_result(
                            ext_url,
                            video_title=traverse_obj(block, ('caption', {str})) or traverse_obj(post, ('title', {str})),
                        ),
                    )

        if not entries:
            self.raise_no_formats('No video found in learning post', expected=True, video_id=video_id)
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries, video_id, traverse_obj(post, ('title', {str})), traverse_obj(post, ('description', {str})),
        )

    def _metadata_from_post(self, post, video_id):
        profile = traverse_obj(post, ('profile', {dict})) or {}
        uploader_id = traverse_obj(profile, ('hash_id', {str}))
        username = traverse_obj(profile, ('username', {str}))
        uploader_url = (
            f'https://dev.epicgames.com/community/profile/{uploader_id}/{username}'
            if uploader_id and username
            else None
        )
        return {
            'id': video_id,
            'display_id': traverse_obj(post, ('slug', {str})) or video_id,
            'uploader_url': uploader_url,
            'categories': traverse_obj(post, ('categories', ..., 'name', {str})),
            **traverse_obj(
                post,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                    'timestamp': (('first_published_at', 'published_at'), {parse_iso8601}, any),
                    'view_count': ('views_count', {int_or_none}),
                    'like_count': ('up_votes_count', {int_or_none}),
                    'comment_count': ('thread_comments_count', {int_or_none}),
                    'tags': ('tags', ..., {str}),
                    'thumbnail': ('thumbnail_image', 'thumbnail_url', {url_or_none}),
                    'uploader': ('profile', 'name', {str}),
                    'uploader_id': ('profile', 'hash_id', {str}),
                },
            ),
        }

    def _extract_qstv_video(self, identifier, video_id=None):
        video_id = video_id or identifier
        embed = self._download_webpage(
            f'{self._API_BASE}/cms/videos/{identifier}/embed.html',
            video_id,
            'Downloading Electra embed',
            impersonate=True,
        )
        qstv_url = self._search_regex(
            r'videoUrl\s*=\s*(["\'])(?P<url>(?:qsep|https?)://(?:cdn\.)?qstv\.on\.epicgames\.com/[^"\']+)\1',
            embed,
            'qstv video URL',
            group='url',
        )
        if qstv_url.startswith('qsep://'):
            qstv_url = f'https://{qstv_url[7:]}'

        playlist = self._download_json(qstv_url, video_id, 'Downloading qstv playlist', impersonate=True)
        formats, subtitles = self._extract_qstv_playlist(playlist, video_id)
        self._merge_subtitles(self._extract_embed_subtitles(embed), target=subtitles)
        if not formats:
            self.raise_no_formats('No video formats found', expected=True, video_id=video_id)

        return {
            'id': video_id,
            'title': identifier,
            'formats': formats,
            'subtitles': subtitles,
            'duration': traverse_obj(playlist, ('playlist', {self._playlist_duration})),
        }

    def _extract_qstv_playlist(self, playlist, video_id):
        payload = traverse_obj(playlist, ('playlist', {str}))
        playlist_type = (traverse_obj(playlist, ('playlistType', {str})) or '').lower()
        decoded = self._decode_playlist_payload(payload)
        if not decoded:
            return [], {}

        if decoded.startswith('#EXTM3U') or 'mpegurl' in playlist_type or 'm3u8' in playlist_type:
            if decoded.startswith(('http://', 'https://')):
                return self._extract_m3u8_formats_and_subtitles(decoded, video_id, 'mp4', m3u8_id='hls', fatal=False)
            return [], {}

        if decoded.lstrip().startswith('<'):
            mpd_doc = self._parse_xml(decoded, video_id)
            formats, subtitles = self._parse_mpd_formats_and_subtitles(mpd_doc, mpd_id='dash')
            duration = parse_duration(mpd_doc.get('mediaPresentationDuration'))
            for f in formats:
                f.setdefault('duration', duration)
            return formats, subtitles

        if decoded.startswith(('http://', 'https://')):
            if 'dash' in playlist_type or decoded.endswith('.mpd'):
                return self._extract_mpd_formats_and_subtitles(decoded, video_id, mpd_id='dash', fatal=False)
            return self._extract_m3u8_formats_and_subtitles(decoded, video_id, 'mp4', m3u8_id='hls', fatal=False)
        return [], {}

    def _decode_playlist_payload(self, payload):
        if not payload:
            return None
        payload = payload.strip()
        if payload.startswith(('<', '#EXTM3U', 'http://', 'https://')):
            return payload
        try:
            decoded = base64.b64decode(payload).decode()
        except (ValueError, UnicodeDecodeError):
            return payload
        return decoded.strip() or payload

    def _playlist_duration(self, payload):
        decoded = self._decode_playlist_payload(payload)
        if not decoded or not decoded.lstrip().startswith('<'):
            return None
        duration = self._search_regex(r'mediaPresentationDuration="([^"]+)"', decoded, 'duration', default=None)
        return parse_duration(duration)

    def _extract_embed_subtitles(self, embed):
        subtitles = {}
        for vtt_url, lang in re.findall(
            r'src:\s*"(https?://[^"]+\.vtt[^"]*)"[^}]*?srclang:\s*"([^"]*)"',
            embed,
        ):
            lang_code = lang.lower()
            if lang_code == 'english':
                lang_code = 'en'
            subtitles.setdefault(lang_code, []).append({'url': vtt_url, 'ext': 'vtt'})
        return subtitles
