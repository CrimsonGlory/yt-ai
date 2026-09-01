from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_codecs,
    traverse_obj,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class NovinkyIE(InfoExtractor):
    IE_DESC = 'Novinky.cz'
    _VALID_URL = r'https?://(?:www\.)?novinky\.cz/clanek/(?:[^/?#]*-)?(?P<id>\d+)'
    _API_BASE = 'https://api-web.novinky.cz/v1'
    _TESTS = [{
        'url': 'https://www.novinky.cz/clanek/podcasty-hlas-semira-gerchana-slysite-v-televizi-skoro-kazdy-den-aniz-byste-o-tom-vedeli-40407886',
        'md5': '4e57da00be5feddf8ac3f8a91ce247ac',
        'info_dict': {
            'id': '40407886',
            'ext': 'mp4',
            'title': 'Hlas Semira Gerchána slyšíte v televizi skoro každý den, aniž byste o tom věděli',
            'alt_title': 'Hostem podcastu V českém znění byl Bohdan Tůma',
            'description': 'md5:bea5a1b65096e1ffde125fde62a8d741',
            'thumbnail': r're:https?://d15-a\.sdn\.cz/.+',
            'duration': 1689,
            'timestamp': 1662609600,
            'upload_date': '20220908',
            'uploader': 'Richard Wágner',
        },
    }, {
        'url': 'https://www.novinky.cz/clanek/podcasty-verim-ti-po-znasilneni-sousedem-se-necitila-v-bezpeci-ani-doma-po-dvou-letech-ma-sofie-stale-nocni-mury-40593729',
        'only_matching': True,
    }, {
        'url': 'https://novinky.cz/clanek/40407886',
        'only_matching': True,
    }]

    def _extract_sdn_formats(self, sdn_url, video_id):
        sdn_data = self._download_json(sdn_url, video_id)
        if sdn_data.get('Location'):
            sdn_url = sdn_data['Location']
            sdn_data = self._download_json(sdn_url, video_id)

        formats = []
        for format_id, format_data in (traverse_obj(sdn_data, ('data', 'mp4', {dict})) or {}).items():
            format_rel = traverse_obj(format_data, ('url', {str}))
            if not format_rel:
                continue
            try:
                width, height = format_data.get('resolution')
            except (TypeError, ValueError):
                width, height = None, None
            formats.append({
                'url': urljoin(sdn_url, format_rel),
                'format_id': f'http-{format_id}',
                'tbr': int_or_none(traverse_obj(format_data, 'bandwidth'), scale=1000),
                'width': int_or_none(width),
                'height': int_or_none(height),
                **parse_codecs(traverse_obj(format_data, 'codec')),
            })

        subtitles = {}
        hls_rel = traverse_obj(sdn_data, ('pls', 'hls', 'url', {str}))
        if hls_rel:
            hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                urljoin(sdn_url, hls_rel), video_id, ext='mp4',
                m3u8_id='hls', fatal=False)
            formats.extend(hls_fmts)
            self._merge_subtitles(hls_subs, target=subtitles)

        return formats, subtitles

    def _extract_sdn_entry(self, media, video_id, article):
        sdn_url = url_or_none(
            traverse_obj(media, ('video', 'sdn'))
            or traverse_obj(media, 'liveStreamUrl')
            or traverse_obj(media, 'sdn'))
        if not sdn_url:
            return None

        formats, subtitles = self._extract_sdn_formats(f'{sdn_url}spl2,2,VOD', video_id)
        if not formats:
            return None

        thumbnail = url_or_none(traverse_obj(media, ('caption', 'url')))
        if thumbnail and thumbnail.startswith('//'):
            thumbnail = f'https:{thumbnail}'

        duration = (
            traverse_obj(media, ('video', 'videoInfo', 'durationS', {int_or_none}))
            or int_or_none(traverse_obj(media, ('video', 'videoInfo', 'duration')), scale=1000))

        sub_rel = traverse_obj(media, 'subtitlesRelativeUrl')
        if sub_rel:
            self._merge_subtitles(
                {'cs': [{'url': urljoin(sdn_url, sub_rel), 'ext': 'vtt'}]},
                target=subtitles)

        info = {
            'id': video_id,
            'title': article.get('title') or media.get('title'),
            'alt_title': media.get('title'),
            'description': article.get('perex'),
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': unified_timestamp(article.get('dateOfPublication')),
            'uploader': traverse_obj(
                article, ('authors', 0, 'name'), ('authors', 0, {str})),
            'formats': formats,
            'subtitles': subtitles,
        }
        if media.get('_cls') == 'Live' or media.get('isRunning') is True:
            info['is_live'] = True
        return info

    def _real_extract(self, url):
        article_id = self._match_id(url)
        article = self._download_json(
            f'{self._API_BASE}/documents/{article_id}', article_id,
            query={'embedded': 'caption.(caption,sources),authors'})

        caption = article.get('caption')
        if isinstance(caption, str):
            caption = self._download_json(
                f'{self._API_BASE}/media/{caption}', article_id,
                'Downloading media JSON', fatal=False)

        if not isinstance(caption, dict) or caption.get('_cls') not in ('Video', 'Live'):
            raise ExtractorError('No video found', expected=True)

        entry = self._extract_sdn_entry(caption, article_id, article)
        if not entry:
            raise ExtractorError('No video formats found', expected=True)
        return entry
