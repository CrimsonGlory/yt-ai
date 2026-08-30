from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    format_field,
    int_or_none,
    str_or_none,
    traverse_obj,
    url_or_none,
)
from ..utils.traversal import require


class MissEvanIE(InfoExtractor):
    IE_NAME = 'missevan'
    IE_DESC = 'MissEvan / 猫耳FM'
    _VALID_URL = r'https?://(?:www\.|m\.|fm\.)?missevan\.com/(?:sound/player\?(?:[^#]*&)?id=|sound/)(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.missevan.com/sound/player?id=5203294',
        'md5': '15fb55ef0db06645ae8f4f0092f008b1',
        'info_dict': {
            'id': '5203294',
            'ext': 'm4a',
            'title': '1700W福利 《重生之将门毒后》第一季 白噪音·睿王府日常',
            'description': 'md5:e25e91d0d5342201016f8ad6b713e3a7',
            'thumbnail': r're:https?://static\.maoercdn\.com/.+',
            'duration': 1809.432,
            'timestamp': 1651734070,
            'upload_date': '20220505',
            'uploader': '重生之将门毒后广播剧',
            'uploader_id': '13689170',
            'uploader_url': 'https://www.missevan.com/13689170',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://www.missevan.com/sound/5203294',
        'only_matching': True,
    }, {
        'url': 'https://m.missevan.com/sound/player?id=5203294',
        'only_matching': True,
    }]

    _AUDIO_KEYS = (
        ('soundurl_32', '32', 32),
        ('soundurl_64', '64', 64),
        ('soundurl_128', '128', 128),
        ('soundurl', 'original', None),
    )

    def _real_extract(self, url):
        sound_id = self._match_id(url)

        info = {}
        for _ in range(3):
            data = self._download_json(
                'https://www.missevan.com/sound/getsound', sound_id,
                query={'soundid': sound_id},
                headers={'Referer': f'https://www.missevan.com/sound/player?id={sound_id}'})
            info = traverse_obj(data, ('info', {dict})) or {}
            if info.get('sound'):
                break
            redirect = traverse_obj(info, ('redirect', {int_or_none}, {str_or_none}))
            if not redirect:
                raise ExtractorError(info.get('message') or 'Audio not found', expected=True)
            sound_id = redirect
        else:
            raise ExtractorError('Too many sound redirects', expected=True)

        sound = traverse_obj(info, ('sound', {dict}, {require('sound info')}))
        sound_id = str_or_none(sound.get('id')) or sound_id

        formats, hls_urls = [], []
        for key, format_id, abr in self._AUDIO_KEYS:
            media_url = url_or_none(sound.get(key))
            if not media_url:
                continue
            if determine_ext(media_url) == 'm3u8':
                hls_urls.append((media_url, format_id))
                continue
            formats.append({
                'format_id': format_id,
                'url': media_url,
                'abr': abr,
                'vcodec': 'none',
                'ext': determine_ext(media_url, 'm4a'),
                'quality': 1 if format_id == 'original' else 0,
            })

        video_url = url_or_none(sound.get('videourl'))
        if video_url and determine_ext(video_url) != 'm3u8':
            formats.append({
                'format_id': 'video',
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
            })

        has_drm = bool(traverse_obj(sound, ('dash', 'audio', ..., 'bilidrm_uri', {str})))
        if not formats and hls_urls and not has_drm:
            for hls_url, format_id in hls_urls:
                hls_fmts = self._extract_m3u8_formats(
                    hls_url, sound_id, 'm4a', m3u8_id=format_id, fatal=False)
                formats.extend(hls_fmts)
            has_drm = has_drm or (formats and all(f.get('has_drm') for f in formats))
            if has_drm:
                formats = []

        if not formats:
            if sound.get('need_pay') or traverse_obj(sound, ('pay_type', {int_or_none}), default=0):
                self.raise_login_required(
                    'This audio is only available to paid users', metadata_available=True)
            elif has_drm or hls_urls:
                self.report_drm(sound_id)
            else:
                self.raise_no_formats('No audio formats found', expected=True, video_id=sound_id)

        return {
            'id': sound_id,
            'formats': formats,
            **traverse_obj(sound, {
                'title': ('soundstr', {str}),
                'description': ('intro', {clean_html}),
                'thumbnail': ('front_cover', {url_or_none}),
                'duration': ('duration', {float_or_none(scale=1000)}),
                'timestamp': ('create_time', {int_or_none}),
                'uploader': ('username', {str}),
                'uploader_id': ('user_id', {int_or_none}, {str_or_none}),
                'view_count': ('view_count', {int_or_none}),
                'like_count': ('favorite_count', {int_or_none}),
                'comment_count': ('comment_count', {int_or_none}),
            }),
            'tags': traverse_obj(info, ('tags', ..., 'name', {str}, filter, all, filter)),
            'uploader_url': format_field(
                traverse_obj(sound, ('user_id', {int_or_none})),
                None, 'https://www.missevan.com/%s'),
        }
