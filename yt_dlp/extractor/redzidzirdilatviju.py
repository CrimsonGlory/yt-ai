import re
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    url_or_none,
)
from ..utils.traversal import require, traverse_obj


class RedziDzirdiLatvijuIE(InfoExtractor):
    IE_NAME = 'redzidzirdilatviju'
    IE_DESC = 'Redzi, dzirdi Latviju!'
    _VALID_URL = (
        r'https?://(?:www\.)?redzidzirdilatviju\.lv/(?:[a-z]{2}/)?search/(?P<media_type>movie|sound)/(?P<id>\d+)'
    )
    _SOLR_API = 'https://www.redzidzirdilatviju.lv/index'
    _HLS_BASE = 'https://filmas.arhivi.lv:30443/s'
    _TESTS = [
        {
            'url': 'https://redzidzirdilatviju.lv/en/search/movie/175277',
            'md5': '4ccf18d325f6e6d38c7db58b2e5fcc99',
            'info_dict': {
                'id': '175277',
                'ext': 'mp4',
                'title': 'Krievijas imperatora Nikolaja II vizīte Rīgā',
                'description': 'md5:01fa6bdd7d176d9f861e39d9fedf6c64',
                'display_id': 'LNA_KFFDA_F51_1_4973',
                'duration': 318,
                'release_year': 1910,
                'categories': ['hronika'],
            },
        },
        {
            'url': 'https://redzidzirdilatviju.lv/lv/search/movie/175277',
            'only_matching': True,
        },
        {
            'url': 'https://www.redzidzirdilatviju.lv/en/search/movie/175277',
            'only_matching': True,
        },
        {
            'url': 'https://redzidzirdilatviju.lv/en/search/sound/132031',
            'only_matching': True,
        },
    ]

    def _rewrite_archive_url(self, url):
        url = url_or_none(url)
        if not url:
            return None
        return re.sub(r'^https?://[^/]+', 'https://filmas.arhivi.lv', url)

    def _real_extract(self, url):
        media_type, video_id = self._match_valid_url(url).group('media_type', 'id')
        data = self._download_json(
            self._SOLR_API,
            video_id,
            query={
                'wt': 'json',
                'rows': '1',
                'q': f'ss_item_type:{media_type} AND ss_item_entity_id:{video_id}',
            },
        )
        doc = traverse_obj(data, ('response', 'docs', 0, {dict}, {require('document', expected=True)}))

        info = {
            'id': video_id,
            **traverse_obj(
                doc,
                {
                    'title': (f'ts_{media_type}$field_title', {str}),
                    'description': (f'tm_{media_type}$field_annotation', 0, {str}),
                    'display_id': (f'ss_{media_type}$field_identifier', {str}),
                },
            ),
        }

        if media_type == 'sound':
            audio_url = traverse_obj(
                doc, ('tm_sound$field_sound_samples$field_sound_file$file$url', 0, {self._rewrite_archive_url}),
            )
            if not audio_url:
                raise ExtractorError('No public audio is available for this document', expected=True)
            info.update(
                {
                    'url': audio_url,
                    'ext': 'mp3',
                    **traverse_obj(
                        doc,
                        {
                            'duration': ('is_sound$field_sound_duration', {int_or_none}),
                            'release_year': ('ds_sound$field_date_year$value', {str}, {lambda x: x[:4]}, {int_or_none}),
                        },
                    ),
                },
            )
            return info

        video_name = traverse_obj(doc, ('ss_movie$field_video$file$name', {str}))
        if not video_name:
            raise ExtractorError('No public video is available for this document', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            f'{self._HLS_BASE}/{urllib.parse.quote(video_name)}/playlist.m3u8', video_id, 'mp4', m3u8_id='hls',
        )
        info.update(
            {
                'formats': formats,
                'subtitles': subtitles,
                **traverse_obj(
                    doc,
                    {
                        'duration': ('ss_movie$field_duration_calc', {parse_duration}),
                        'release_year': ('ds_movie$field_date_year$value', {str}, {lambda x: x[:4]}, {int_or_none}),
                        'categories': ('sm_movie$field_genre$name', ..., {str}, all),
                    },
                ),
            },
        )
        return info
