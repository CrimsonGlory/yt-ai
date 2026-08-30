from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    parse_iso8601,
    parse_resolution,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class MatreshkaTVIE(InfoExtractor):
    IE_NAME = 'matreshka.tv'
    IE_DESC = 'МатрёшкаТВ'
    _VALID_URL = r'https?://(?:www\.)?matreshka\.tv/(?:embed/)?video/(?P<id>[\w-]+)'
    _AGE_LIMITS = {
        0: 6,   # SIX_PLUS
        1: 18,  # EIGHTEEN_PLUS
        3: 16,  # SIXTEEN_PLUS
        4: 12,  # TWELVE_PLUS
    }
    _TESTS = [{
        'url': 'https://matreshka.tv/video/HwKAY4Id5QA',
        'md5': '848c145cfa4893807eda63c67ef471f6',
        'info_dict': {
            'id': 'HwKAY4Id5QA',
            'ext': 'mp4',
            'title': 'Диалог об алкоголе с Джеком Лондоном (рубрика МЕТРО)',
            'description': '',
            'thumbnail': r're:https?://c4-images\.cmtv\.ru/.+',
            'duration': 1200.36,
            'timestamp': 1762304537,
            'upload_date': '20251105',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'age_limit': 16,
            'channel': 'Стас Васильев, Мятежник Джек, Дмитрий Пучков - бусти смотреть бесплатно',
            'channel_id': 'wgKgXz6-xvY',
            'channel_url': 'https://matreshka.tv/channel/wgKgXz6-xvY',
            'channel_follower_count': int,
            'channel_is_verified': True,
            'tags': [],
        },
    }, {
        'url': 'https://matreshka.tv/embed/video/HwKAY4Id5QA',
        'only_matching': True,
    }, {
        'url': 'https://matreshka.tv/video/KgBAzC_u0gA?playlistID=YwKA4Zq50gA',
        'only_matching': True,
    }]

    def _age_limit(self, value):
        if value is None:
            return None
        return self._AGE_LIMITS.get(value, 0)

    def _extract_formats_and_subtitles(self, video, video_id):
        formats, subtitles = [], {}
        media_urls = []
        for codec, codec_data in (video.get('video_url') or {}).items():
            if not isinstance(codec_data, dict):
                continue
            for media_url in traverse_obj(codec_data, (
                ('src', 'backupSrc'), 'hls', {url_or_none},
            )):
                media_urls.append((codec, media_url))
        if not media_urls:
            for codec, codec_data in (video.get('abr') or {}).items():
                playlist = traverse_obj(codec_data, ('playlists', 'auto', {url_or_none}))
                if playlist:
                    media_urls.append((codec, playlist))

        seen = set()
        for codec, media_url in media_urls:
            if media_url in seen:
                continue
            seen.add(media_url)
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                media_url, video_id, 'mp4', m3u8_id=f'hls-{codec}', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = traverse_obj(self._download_json(
            f'https://matreshka.tv/api/video-service/v1/video/{video_id}',
            video_id), ('data', {dict}, {require('video data')}))

        formats, subtitles = self._extract_formats_and_subtitles(video, video_id)

        for sub in traverse_obj(video, ('subtitle_url', lambda _, v: url_or_none(v['uri']))):
            subtitles.setdefault(sub.get('lng') or 'und', []).append({
                'url': sub['uri'],
                'name': traverse_obj(sub, ('name', {str})),
            })

        if not formats:
            if video.get('for_subscribers'):
                self.raise_login_required(
                    'This video is only available to channel subscribers')
            reason = traverse_obj(video, (
                ('blocking_reason_for_user', 'blocked_reason'), {str}, any))
            self.raise_no_formats(
                reason or 'No video formats found', expected=bool(reason),
                video_id=video_id)

        thumbnails = []
        for img_fmt, sizes in (video.get('cover') or {}).items():
            if not isinstance(sizes, dict):
                continue
            for res, thumb_url in sizes.items():
                thumb_url = url_or_none(thumb_url)
                if not thumb_url:
                    continue
                thumbnails.append({
                    'id': f'{img_fmt}-{res}',
                    'url': thumb_url,
                    **parse_resolution(res),
                })

        channel_id = traverse_obj(video, ('channel', 'id', {str}))

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            **traverse_obj(video, {
                'title': ('name', {str}),
                'description': ('description', {str}),
                'duration': ('duration', {float_or_none(scale=1000)}),
                'timestamp': ('created_at', {parse_iso8601(delimiter=' ')}),
                'view_count': ('views', {int_or_none}),
                'like_count': ('likes', {int_or_none}),
                'dislike_count': ('dislikes', {int_or_none}),
                'tags': ('tags', ..., {str}, all),
                'age_limit': ('children_content', {int_or_none}, {self._age_limit}),
                'channel': ('channel', 'name', {str}),
                'channel_id': ('channel', 'id', {str}),
                'channel_follower_count': ('channel', 'subscribers_count', {int_or_none}),
                'channel_is_verified': ('channel', 'is_verified', {bool}),
            }),
            'channel_url': f'https://matreshka.tv/channel/{channel_id}' if channel_id else None,
        }
