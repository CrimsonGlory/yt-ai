import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_duration,
    parse_qs,
    strip_or_none,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class AmericanArchiveIE(InfoExtractor):
    IE_NAME = 'americanarchive'
    IE_DESC = 'American Archive of Public Broadcasting'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?americanarchive\.org/
        (?:catalog|media|api|embed)/
        (?P<id>cpb-aacip[-_][0-9a-z]+(?:[-_][0-9a-z]+)*)
        (?:/download)?
    '''
    _TESTS = [{
        'url': 'https://americanarchive.org/catalog/cpb-aacip_507-0v89g5gw88',
        'md5': '36d21de6df4d45b78d3159ed86616f92',
        'info_dict': {
            'id': 'cpb-aacip-507-0v89g5gw88',
            'ext': 'mp4',
            'title': 'The NewsHour with Jim Lehrer',
            'description': 'md5:fd848084ccce224dc9d07024376959e4',
            'thumbnail': 'https://s3.amazonaws.com/americanarchive.org/thumbnail/cpb-aacip-507-0v89g5gw88.jpg',
            'duration': 3549,
            'release_date': '19960215',
            'release_year': 1996,
            'series': 'The NewsHour with Jim Lehrer',
            'creators': ['NewsHour Productions'],
            'creator': 'NewsHour Productions',
            'tags': [
                'Education', 'Social Issues', 'Literature', 'Technology',
                'Film and Television', 'Race and Ethnicity',
                'Military Forces and Armaments', 'Politics and Government',
            ],
        },
    }, {
        'url': 'https://americanarchive.org/catalog/cpb-aacip-507-0v89g5gw88',
        'only_matching': True,
    }, {
        'url': 'https://americanarchive.org/media/cpb-aacip-507-0v89g5gw88',
        'only_matching': True,
    }, {
        'url': 'https://americanarchive.org/catalog/cpb-aacip-5a070554fe5',
        'only_matching': True,
    }, {
        'url': 'https://americanarchive.org/catalog/cpb-aacip_384-29p2nm8h',
        'only_matching': True,
    }]
    _API_URL = 'https://americanarchive.org/api/{0}'
    _MEDIA_URL = 'https://americanarchive.org/media/{0}'
    _CATALOG_URL = 'https://americanarchive.org/catalog/{0}'
    _THUMB_URL = 'https://s3.amazonaws.com/americanarchive.org/thumbnail/{0}.jpg'
    _CAPTION_VTT_URL = 'https://s3.amazonaws.com/americanarchive.org/captions/{0}/{0}.vtt'
    _CAPTION_SRT_URL = 'https://s3.amazonaws.com/americanarchive.org/captions/{0}/{0}.srt1.srt'
    _REFERER = 'https://americanarchive.org/'

    @staticmethod
    def _normalize_guid(video_id):
        return re.sub(r'^cpb-aacip.', 'cpb-aacip-', video_id)

    @staticmethod
    def _strip_xml_ns(elem):
        for el in elem.iter():
            if isinstance(el.tag, str) and el.tag.startswith('{'):
                el.tag = el.tag.rsplit('}', 1)[-1]
        return elem

    @staticmethod
    def _xml_text(elem, tag):
        for child in elem.findall(tag):
            text = strip_or_none(child.text)
            if text:
                return text
        return None

    @staticmethod
    def _parse_aapb_duration(text):
        return parse_duration(re.sub(r';.*', '', text or ''))

    def _parse_pbcore(self, pbcore):
        titles = []
        series = episode = None
        for title_el in pbcore.findall('pbcoreTitle'):
            text = strip_or_none(title_el.text)
            if not text:
                continue
            title_type = title_el.get('titleType')
            if title_type == 'Series':
                series = series or text
            elif title_type == 'Episode':
                episode = episode or text
            if title_type != 'Alternative':
                titles.append(text)

        description = None
        for desc_el in pbcore.findall('pbcoreDescription'):
            text = clean_html(desc_el.text)
            if text:
                description = text
                if desc_el.get('descriptionType') in (None, 'Episode', 'Program', 'Description'):
                    break

        creators = []
        for creator_el in pbcore.iter('creator'):
            text = strip_or_none(creator_el.text)
            if text and text not in creators:
                creators.append(text)

        genres, topics = [], []
        for genre_el in pbcore.findall('pbcoreGenre'):
            text = strip_or_none(genre_el.text)
            if not text:
                continue
            if genre_el.get('annotation') == 'topic':
                topics.append(text)
            else:
                genres.append(text)

        access_level = None
        for anno_el in pbcore.findall('pbcoreAnnotation'):
            if anno_el.get('annotationType') == 'Level of User Access':
                access_level = strip_or_none(anno_el.text)
                break

        duration = None
        for dur_el in pbcore.iter('essenceTrackDuration'):
            duration = self._parse_aapb_duration(dur_el.text)
            if duration:
                break

        ci_ids = [
            strip_or_none(el.text)
            for el in pbcore.findall('pbcoreIdentifier')
            if el.get('source') == 'Sony Ci'
        ]
        ci_ids = [ci_id for ci_id in ci_ids if ci_id]

        return {
            'title': join_nonempty(*titles, delim='; ') or None,
            'description': description,
            'series': series,
            'episode': episode,
            'creators': creators or None,
            'genres': genres or None,
            'tags': (topics or genres) or None,
            'release_date': unified_strdate(self._xml_text(pbcore, 'pbcoreAssetDate'), False),
            'duration': duration,
            'access_level': access_level,
            'ci_ids': ci_ids,
        }

    def _raise_unavailable(self, video_id, access_level, status=None):
        if access_level == 'On Location':
            raise ExtractorError(
                'This recording is only available on location at GBH and the Library of Congress',
                expected=True, video_id=video_id)
        if access_level == 'Private':
            raise ExtractorError(
                'This recording is not available online',
                expected=True, video_id=video_id)
        if status == 404:
            raise ExtractorError(
                'This recording has not been digitized',
                expected=True, video_id=video_id)
        raise ExtractorError(
            'This recording is not available for streaming',
            expected=True, video_id=video_id)

    def _extract_captions(self, video_id):
        for caption_url, ext in (
            (self._CAPTION_VTT_URL.format(video_id), 'vtt'),
            (self._CAPTION_SRT_URL.format(video_id), 'srt'),
        ):
            if self._is_valid_url(caption_url, video_id, 'captions'):
                return {'en': [{'url': caption_url, 'ext': ext}]}
        return {}

    def _request_media(self, path, video_id, headers, query, note):
        urlh = self._request_webpage(
            path, video_id, note=note, headers=headers, query=query,
            expected_status=(401, 403, 404), fatal=False)
        if urlh is False:
            return None, None, None
        try:
            status = int_or_none(getattr(urlh, 'status', None))
            if status in (401, 403, 404):
                return status, None, None
            return status, urlh.url, (urlh.headers.get('Content-Type') or '').lower()
        finally:
            urlh.close()

    def _extract_stream(self, video_id, part, access_level):
        headers = {'Referer': self._REFERER}
        query = {'part': str(part or 1)}
        formats, subtitles = [], {}

        dl_status, dl_url, _ = self._request_media(
            f'{self._MEDIA_URL.format(video_id)}/download', video_id,
            headers, query, 'Downloading media file redirect')
        if dl_url:
            formats.append({
                'url': dl_url,
                'format_id': 'http',
                'ext': determine_ext(dl_url, 'mp4'),
                'http_headers': headers,
                'quality': 1,
            })

        hls_status, stream_url, content_type = self._request_media(
            self._MEDIA_URL.format(video_id), video_id,
            headers, query, 'Downloading media redirect')
        if stream_url:
            ext = determine_ext(stream_url, '')
            if ext == 'm3u8' or 'mpegurl' in content_type:
                hls_fmts, hls_subs = self._extract_m3u8_formats_and_subtitles(
                    stream_url, video_id, 'mp4', m3u8_id='hls',
                    headers=headers, fatal=False)
                formats.extend(hls_fmts)
                self._merge_subtitles(hls_subs, target=subtitles)
            elif not formats:
                formats.append({
                    'url': stream_url,
                    'ext': ext or 'mp4',
                    'http_headers': headers,
                })

        if not formats:
            self._raise_unavailable(
                video_id, access_level, dl_status or hls_status)
        return formats, subtitles

    def _real_extract(self, url):
        video_id = self._normalize_guid(self._match_id(url))
        part = int_or_none(traverse_obj(parse_qs(url), ('part', 0)))

        info = {
            'id': video_id,
            'thumbnail': self._THUMB_URL.format(video_id),
        }

        pbcore = self._download_xml(
            self._API_URL.format(video_id), video_id,
            note='Downloading PBCore metadata', fatal=False,
            headers={'Accept': 'text/xml'})
        access_level = None
        ci_ids = []
        if pbcore is not False and pbcore is not None:
            self._strip_xml_ns(pbcore)
            parsed = self._parse_pbcore(pbcore)
            access_level = parsed.pop('access_level', None)
            ci_ids = parsed.pop('ci_ids', []) or []
            info.update({k: v for k, v in parsed.items() if v is not None})

        if not info.get('title'):
            webpage = self._download_webpage(
                self._CATALOG_URL.format(video_id), video_id, fatal=False)
            if webpage:
                info['title'] = self._og_search_title(webpage, default=None)
                info.setdefault(
                    'description',
                    self._og_search_description(webpage, default=None))
                info['thumbnail'] = url_or_none(
                    self._og_search_thumbnail(webpage, default=None)) or info.get('thumbnail')

        ci_count = len(ci_ids)
        if ci_count > 1 and not part:
            entries = [
                self.url_result(
                    f'{self._CATALOG_URL.format(video_id)}?part={idx}',
                    ie=self.ie_key(), video_id=f'{video_id}-p{idx}')
                for idx in range(1, ci_count + 1)
            ]
            return self.playlist_result(
                entries, video_id, info.get('title'), info.get('description'))

        if ci_count > 1:
            info['id'] = f'{video_id}-p{part or 1}'

        formats, subtitles = self._extract_stream(video_id, part, access_level)
        self._merge_subtitles(self._extract_captions(video_id), target=subtitles)
        info.update({
            'formats': formats,
            'subtitles': subtitles,
        })
        return info
