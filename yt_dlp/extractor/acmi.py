from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ACMIIE(InfoExtractor):
    IE_NAME = 'acmi'
    IE_DESC = 'ACMI: Your museum of screen culture'
    _VALID_URL = r'https?://(?:www\.)?acmi\.net\.au/works/(?P<id>\d+)(?:--[^/?#]*)?'
    _API_WORK_URL = 'https://admin.acmi.net.au/xos/works/{}/'
    _TESTS = [
        {
            'url': 'https://www.acmi.net.au/works/82806--priceless-places-australias-national-estate-wilderness/',
            'md5': 'a6f053ffeca70345219ccee18224df12',
            'info_dict': {
                'id': '82806',
                'ext': 'mp4',
                'title': "Priceless places: Australia's National Estate wilderness",
                'description': 'md5:810f81f86586574d44ef08bad1653dac',
                'thumbnail': r're:https?://xos-prod-media\.s3[^/]+/.+',
                'duration': 906.96,
                'release_year': 1993,
                'creators': ['Kestrel Films & Video (Australia)', 'Wilderness Society (Australia)'],
                'display_id': '82806',
            },
        },
        {
            'url': 'https://www.acmi.net.au/works/113982--living-inside/',
            'only_matching': True,
        },
        {
            'url': 'https://www.acmi.net.au/works/82806/',
            'only_matching': True,
        },
    ]

    def _extract_formats(self, video):
        formats = []
        seen = set()
        for url_key, format_id, meta_key in (
            ('resource', 'access', 'access_metadata'),
            ('web_resource', 'web', 'web_metadata'),
        ):
            media_url = url_or_none(video.get(url_key))
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)
            meta = video.get(meta_key) or {}
            formats.append(
                {
                    'url': media_url,
                    'format_id': format_id,
                    'ext': determine_ext(media_url, 'mp4'),
                    'width': int_or_none(meta.get('width')),
                    'height': int_or_none(meta.get('height')),
                    'filesize': int_or_none(meta.get('file_size_bytes')),
                    'vbr': float_or_none(meta.get('video_bit_rate'), 1000),
                    'abr': float_or_none(meta.get('audio_bit_rate'), 1000),
                    'tbr': float_or_none(meta.get('overall_bit_rate'), 1000),
                    'fps': float_or_none(meta.get('video_frame_rate')),
                    'vcodec': str_or_none(meta.get('video_codec')),
                    'acodec': str_or_none(meta.get('audio_codec')),
                    'asr': int_or_none(meta.get('audio_sample_rate')),
                    'audio_channels': int_or_none(meta.get('audio_channels')),
                },
            )
        return formats

    def _extract_subtitles(self, video):
        subtitles = {}
        for track in traverse_obj(video, ('caption_tracks', ..., {dict})) or []:
            track_url = url_or_none(track.get('url'))
            if not track_url:
                continue
            lang = traverse_obj(track, 'locale', {str}) or 'en'
            subtitles.setdefault(lang, []).append(
                {
                    'url': track_url,
                    'ext': determine_ext(track_url, 'vtt'),
                    'name': traverse_obj(track, 'label', {str}),
                },
            )
        if not subtitles:
            vtt_url = url_or_none(video.get('subtitles_vtt')) or url_or_none(video.get('subtitles'))
            if vtt_url:
                subtitles['en'] = [{'url': vtt_url, 'ext': determine_ext(vtt_url, 'vtt')}]
        return subtitles

    def _work_metadata(self, work):
        release_year = int_or_none(str(work.get('first_production_date') or '')[:4])
        return {
            'title': traverse_obj(work, 'title', {str}),
            'description': clean_html(work.get('description')) or clean_html(work.get('brief_description')),
            'thumbnail': traverse_obj(work, ('thumbnail', 'image_url', {url_or_none})),
            'release_year': release_year if release_year and 1000 <= release_year <= 2100 else None,
            'creators': traverse_obj(work, ('creators_primary', ..., 'name', {str})),
        }

    def _parse_video(self, work, video, work_id, video_id):
        formats = self._extract_formats(video)
        if not formats:
            self.raise_no_formats('No video source', expected=True, video_id=video_id)
        return {
            **self._work_metadata(work),
            'id': video_id,
            'display_id': work_id,
            'formats': formats,
            'subtitles': self._extract_subtitles(video),
            'duration': float_or_none(video.get('duration_secs')),
            'thumbnail': (
                url_or_none(video.get('snapshot'))
                or traverse_obj(work, ('thumbnail', 'image_url', {url_or_none}))),
        }

    def _real_extract(self, url):
        work_id = self._match_id(url)
        work = self._download_json(self._API_WORK_URL.format(work_id), work_id, headers={'Accept': 'application/json'})
        if not isinstance(work, dict):
            raise ExtractorError('Unable to extract ACMI work', expected=True)

        videos = traverse_obj(work, ('videos', ..., {dict})) or []
        if not videos:
            link = traverse_obj(work, ('video_links', 0, 'uri', {url_or_none}))
            if link:
                return self.url_result(link, url_transparent=True, video_id=work_id, **self._work_metadata(work))
            raise ExtractorError('No public video is available for this ACMI work', expected=True)

        entries = []
        for video in videos:
            video_id = work_id if len(videos) == 1 else str_or_none(video.get('id')) or work_id
            entries.append(self._parse_video(work, video, work_id, video_id))
        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(
            entries,
            work_id,
            traverse_obj(work, 'title', {str}),
            clean_html(work.get('description')) or clean_html(work.get('brief_description')),
        )
