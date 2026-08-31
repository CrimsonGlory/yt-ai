import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    orderedSet,
    parse_duration,
    parse_resolution,
    remove_end,
    url_or_none,
)


class HQPornerIE(InfoExtractor):
    IE_DESC = 'hqporner.com'
    _VALID_URL = (
        r'https?://(?:www\.|m\.)?hqporner\.com/hdporn/'
        r'(?P<id>\d+)(?:-(?P<display_id>[^/?#.]+))?(?:\.html)?'
    )
    _TESTS = [{
        'url': 'https://hqporner.com/hdporn/86482-all_night_rager.html',
        'md5': '69cd373eb38aa82209c0450e0b9fc730',
        'info_dict': {
            'id': '86482',
            'display_id': 'all_night_rager',
            'ext': 'mp4',
            'title': 'All Night Rager',
            'description': 'Watch porn video All Night Rager in high definition for free. Video duration is 40min 34sec. Tags related to this video: big natural tits, pornstar, cougar, mommy, moms in control.',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 2434,
            'age_limit': 18,
            'cast': ['Ava Addams', 'Kimmy Granger', 'Keiran Lee'],
            'categories': [
                '1080p', 'big ass', 'big dick', 'big tits', 'bisexual',
                'brunette', 'mature', 'milf', 'old and young', 'pussy licking',
                'small tits', 'teen', 'threesome',
            ],
            'tags': ['big natural tits', 'pornstar', 'cougar', 'mommy', 'moms in control'],
        },
    }, {
        'url': 'https://www.hqporner.com/hdporn/86482-all_night_rager.html',
        'only_matching': True,
    }, {
        'url': 'https://m.hqporner.com/hdporn/86482-all_night_rager.html',
        'only_matching': True,
    }, {
        'url': 'https://hqporner.com/hdporn/127669-vanilla_is_not_for_this_slut.html',
        'only_matching': True,
    }]

    @staticmethod
    def _absolutize(url):
        if url and url.startswith('//'):
            url = f'https:{url}'
        return url_or_none(url)

    def _extract_embed_url(self, webpage):
        return self._absolutize(self._search_regex(
            (r'<iframe[^>]+src=["\']((?:https?:)?//(?:www\.)?mydaddy\.cc/video/[^"\']+)["\']',
             r'<iframe[^>]+src=["\']((?:https?:)?//[^"\']+)["\'][^>]*\sallowfullscreen',
             r'(?:altplayer|nativeplayer)\.php\?i=((?:https?:)?//[^"\'&]+)'),
            webpage, 'embed URL', default=None))

    def _extract_player_formats(self, player, player_url, video_id):
        player = player.replace('\\"', '"')
        formats, thumbnail, seen = [], None, set()

        def add_format(fmt):
            video_url = self._absolutize(fmt.get('url'))
            if not video_url or video_url in seen:
                return
            ext = determine_ext(video_url, default_ext=fmt.get('ext'))
            if ext not in ('mp4', 'webm', 'm3u8', 'mpd'):
                return
            seen.add(video_url)
            fmt['url'] = video_url
            fmt.setdefault('ext', ext)
            fmt.setdefault('http_headers', {})['Referer'] = player_url
            if not fmt.get('height'):
                fmt.update(parse_resolution(video_url) or {})
            formats.append(fmt)

        for entry in self._parse_html5_media_entries(player_url, player, video_id) or []:
            thumbnail = thumbnail or self._absolutize(entry.get('thumbnail'))
            for fmt in entry.get('formats') or []:
                add_format(fmt)

        if not formats:
            for mobj in re.finditer(r'(?:https?:)?//[^\s"\'<>\\]+\.mp4', player):
                add_format({
                    'url': self._absolutize(mobj.group(0)),
                    'ext': 'mp4',
                    **(parse_resolution(mobj.group(0)) or {}),
                })
        return formats, thumbnail

    def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        webpage = self._download_webpage(url, video_id)

        embed_url = self._extract_embed_url(webpage)
        if not embed_url:
            raise ExtractorError('Unable to extract player iframe', expected=True)

        player = self._download_webpage(
            embed_url, video_id, 'Downloading player', headers={'Referer': url})
        formats, thumbnail = self._extract_player_formats(player, embed_url, video_id)
        if not formats:
            raise ExtractorError('No video source found', expected=True)

        description = self._html_search_meta('description', webpage, default=None)
        tag_str = self._search_regex(
            r'Tags related to this video:\s*(.+?)\.?\s*$',
            description or '', 'tags', default=None)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': remove_end(
                self._html_extract_title(webpage), ' - HQporner.com') or video_id,
            'description': description,
            'thumbnail': thumbnail,
            'duration': parse_duration(self._html_search_regex(
                r'class="icon fa-clock-o">([^<]+)', webpage, 'duration', default=None)),
            'age_limit': self._rta_search(webpage) or 18,
            'cast': orderedSet(re.findall(
                r'<a[^>]+href="/actress/[^"]+"[^>]*>([^<]+)', webpage)) or None,
            'categories': orderedSet(re.findall(
                r'<a[^>]+href="/category/[^"]+"[^>]*>([^<]+)', webpage)) or None,
            'tags': [t.strip() for t in tag_str.split(',') if t.strip()] if tag_str else None,
            'formats': formats,
        }
