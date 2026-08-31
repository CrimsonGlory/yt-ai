import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    parse_qs,
    str_or_none,
    unescapeHTML,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class MeansTVIE(InfoExtractor):
    IE_NAME = 'means.tv'
    IE_DESC = 'Means TV'
    _VALID_URL = (
        r'https?://(?:www\.)?means\.tv/programs/(?P<id>[\w-]+)(?:/(?:program_content|collection_homepage))?(?:[?#]|$)'
    )
    _TESTS = [
        {
            'url': 'https://means.tv/programs/mmn-daily_122024',
            'md5': '69e9e05c136d083c6f814bd4acb77fb0',
            'info_dict': {
                'id': '3382018',
                'ext': 'mp4',
                'display_id': 'mmn-daily_122024',
                'title': 'December 20, 2024 | MMN Daily',
                'description': 'We crown the “Rich Dick of the Year”',
                'uploader': 'Sam Sacks',
                'duration': 1201,
                'timestamp': 1734700311,
                'upload_date': '20241220',
                'thumbnail': r're:https://alpha\.uscreencdn\.com/.+',
            },
        },
        {
            'url': 'https://means.tv/programs/mmn',
            'info_dict': {
                'id': 'mmn',
                'title': 'Means Morning News',
            },
            'playlist_mincount': 50,
            'params': {
                'extract_flat': True,
                'skip_download': True,
            },
        },
        {
            'url': 'https://means.tv/programs/mmn?cid=4003569&permalink=mmn-daily_122024',
            'only_matching': True,
        },
        {
            'url': 'https://means.tv/programs/mmn-daily_122024/program_content',
            'only_matching': True,
        },
        {
            'url': 'https://means.tv/programs/mmn-daily_082826',
            'only_matching': True,
        },
        {
            'url': 'https://means.tv/programs/20250122_hakim_color-revolution',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        permalink = traverse_obj(parse_qs(url), ('permalink', 0))
        display_id = permalink or self._match_id(url)

        if not permalink and '/program_content' not in url:
            turbo = self._download_webpage(
                f'https://means.tv/programs/{display_id}.turbo_stream',
                display_id,
                'Downloading program type',
                fatal=False,
            )
            if turbo and 'program_collection_homepage' in turbo:
                return self._extract_collection(display_id)

        return self._extract_video(display_id)

    def _extract_collection(self, playlist_id):
        webpage = self._download_webpage(
            f'https://means.tv/programs/{playlist_id}/collection_homepage',
            playlist_id,
            'Downloading collection homepage',
        )
        permalinks = re.findall(r'data-playlist-modal-subject-permalink-param="([^"]+)"', webpage)
        if not permalinks:
            self.raise_no_formats('Unable to extract collection videos', expected=True, video_id=playlist_id)

        return self.playlist_from_matches(
            permalinks,
            playlist_id,
            self._html_search_regex(r'<h1[^>]*>\s*([^<]+?)\s*</h1>', webpage, 'title', default=None),
            getter=lambda slug: f'https://means.tv/programs/{slug}',
            ie=self.ie_key(),
        )

    def _extract_video(self, display_id):
        webpage = self._download_webpage(f'https://means.tv/programs/{display_id}', display_id)
        json_ld = self._search_json_ld(webpage, display_id, default={})
        for key in ('url', 'ext', 'formats'):
            json_ld.pop(key, None)

        program_content = self._download_webpage(
            f'https://means.tv/programs/{display_id}/program_content', display_id, 'Downloading program content',
        )

        if 'data-blocked-in-user-country="true"' in program_content:
            self.raise_geo_restricted()

        m3u8_url = self._search_regex(
            r'<source[^>]+src="(https://[^"]+\.m3u8[^"]*)"', program_content, 'm3u8 URL', default=None,
        )
        if 'program-video-free-preview' in program_content or not m3u8_url:
            self.raise_login_required(
                'This video is only available to Means TV subscribers', metadata_available=True, method='cookies',
            )

        formats, subtitles = [], {}
        if m3u8_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(m3u8_url, display_id, 'mp4', m3u8_id='hls')

        for track_tag in re.findall(r'<track[^>]+>', program_content):
            attrs = extract_attributes(track_tag)
            src = url_or_none(unescapeHTML(attrs.get('src')))
            if not src:
                continue
            lang = (attrs.get('srclang') or attrs.get('lang') or 'en').strip()
            subtitles.setdefault(lang, []).append({'url': src})

        stats = (
            self._parse_json(
                unescapeHTML(
                    self._search_regex(
                        r'data-program-video-stats-value="([^"]+)"', program_content, 'video stats', default='{}',
                    ),
                ),
                display_id,
                fatal=False,
            )
            or {}
        )

        video_id = str_or_none(stats.get('content_id')) or self._html_search_regex(
            r'data-program-id="(\d+)"', program_content, 'program id', default=display_id,
        )

        return {
            **json_ld,
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(
                stats,
                {
                    'title': ('content_title', {str}),
                    'uploader': ('author_title', {str}),
                },
            ),
            'thumbnail': url_or_none(
                unescapeHTML(
                    self._search_regex(r'<video[^>]+poster="([^"]+)"', program_content, 'poster', default=None),
                ),
            ),
        }
