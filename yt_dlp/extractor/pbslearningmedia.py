from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    parse_duration,
    url_or_none,
    urljoin,
)
from ..utils.traversal import traverse_obj


class PBSLearningMediaIE(InfoExtractor):
    IE_NAME = 'pbslearningmedia'
    IE_DESC = 'PBS LearningMedia'
    _VALID_URL = r'https?://(?:[\w-]+\.)?pbslearningmedia\.org/resource/(?P<id>[^/?#]+)'
    _API_BASE = 'https://www.pbslearningmedia.org/api/v2'
    _TESTS = [
        {
            'url': 'https://www.pbslearningmedia.org/resource/1f8f7d1b-6cdf-4859-863d-b4877ad8a67f/skills-the-electric-company/',
            'md5': 'a513f32a0d12f09b894ba4eade7930b0',
            'info_dict': {
                'id': '1f8f7d1b-6cdf-4859-863d-b4877ad8a67f',
                'ext': 'mp4',
                'title': 'Skills | The Electric Company',
                'description': 'md5:3197668653e6c0d25b86630549d8f07e',
                'thumbnail': r're:https?://image\.pbs\.org/.+',
                'duration': 1658,
                'series': 'The Electric Company Full Episodes',
                'channel': 'Electric Company',
                'creators': ['Sesame Workshop'],
                'tags': [
                    'English Language Arts',
                    'Language',
                    'Reading Foundational Skills',
                    'Phonics and Word Recognition',
                    'Vocabulary Acquisition and Use',
                    'Decoding',
                ],
                'language': 'en',
                'subtitles': 'count:1',
            },
            'params': {
                # Progressive MP4 so --test writes a stable first 10KB
                'format': 'b[format_id=mp4-16x9]',
            },
        },
        {
            'url': 'https://wisconsin.pbslearningmedia.org/resource/1f8f7d1b-6cdf-4859-863d-b4877ad8a67f/skills-the-electric-company/?student=true&focus=true',
            'only_matching': True,
        },
        {
            'url': 'https://www.pbslearningmedia.org/resource/video-producer-a-z-career-labs/',
            'only_matching': True,
        },
    ]

    def _extract_media(self, media, video_id):
        formats, subtitles = [], {}
        media_kind = (media.get('type') or '').lower()
        seen = set()

        for media_file in traverse_obj(media, ('files', ..., {dict})) or []:
            media_url = url_or_none(urljoin('https://www.pbslearningmedia.org', media_file.get('url')))
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)
            ext = determine_ext(media_url)
            if ext in ('pdf', 'doc', 'docx', 'ppt', 'pptx', 'zip'):
                continue
            if ext == 'm3u8':
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    media_url, video_id, 'mp4', m3u8_id='hls', fatal=False,
                )
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
                continue
            format_id = traverse_obj(media_file, (('type', 'role'), {str}, any)) or ext or 'http'
            fmt = {
                'url': media_url,
                'ext': ext,
                'format_id': format_id.lower().replace(' ', '-'),
            }
            if media_kind == 'audio' or ext in ('mp3', 'm4a', 'aac'):
                fmt['vcodec'] = 'none'
            formats.append(fmt)

        for caption in traverse_obj(media, ('captions', ..., {dict})) or []:
            caption_url = url_or_none(caption.get('url'))
            if not caption_url:
                continue
            lang = (caption.get('language') or 'en').lower()
            subtitles.setdefault(lang, []).append(
                {
                    'url': caption_url,
                    'ext': determine_ext(caption_url, 'vtt'),
                },
            )
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(f'{self._API_BASE}/resource/{video_id}/', video_id)

        formats, subtitles = [], {}
        duration = None
        for media in traverse_obj(data, ('assets', ..., 'medias', ..., {dict})) or []:
            media_fmts, media_subs = self._extract_media(media, video_id)
            formats.extend(media_fmts)
            self._merge_subtitles(media_subs, target=subtitles)
            duration = duration or parse_duration(media.get('duration'))

        if not formats:
            self.raise_no_formats(
                'No public video or audio is available for this resource', expected=True, video_id=video_id,
            )

        return {
            'id': traverse_obj(data, ('guid', {str})) or video_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': duration,
            'language': traverse_obj(
                data,
                (
                    'assets',
                    ...,
                    'medias',
                    ...,
                    'language',
                    {str},
                    {lambda x: x.lower() if x and len(x) == 2 else None},
                    any,
                ),
            ),
            **traverse_obj(
                data,
                {
                    'title': ('title', {str}),
                    'description': ('description', {clean_html}),
                    'thumbnail': ('poster_image', 'url', {url_or_none}),
                    'series': ('content_project', 'title', {str}),
                    'channel': ('attributions', lambda _, v: v.get('role') == 'brand', 'name', {str}, any),
                    'creators': ('attributions', lambda _, v: v.get('role') == 'producer', 'name', {str}),
                    'tags': ('curriculum_tags', ..., 'name', {str}),
                },
            ),
        }
