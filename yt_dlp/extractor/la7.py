import base64
import json
import re

from .common import (
    ExtractorError,
    InfoExtractor,
)
from ..utils import (
    float_or_none,
    int_or_none,
    join_nonempty,
    parse_duration,
    parse_qs,
    unified_strdate,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class LA7IE(InfoExtractor):
    IE_NAME = 'la7play.it'
    _VALID_URL = (
        r'https?://(?:www\.)?(?:la7play\.it|la7\.it)(?P<path>/(?:[^/?#]+/)*(?P<id>[^/?#]+))',
        r'https?://tg\.la7\.it/repliche-tgla7\?(?:[^#]*&)?id=(?P<id>[^&#]+)',
    )
    _EMBED_REGEX = [r'<iframe[^>]+src=(["\'])(?P<url>https?://(?:www\.)?la7(?:play)?\.it/embedded/la7\?[^"\']+)\1']

    _TESTS = [{
        # Full episode, "rivedila7" path segment (entity type NodeReplica)
        'url': 'https://www.la7play.it/bellidentrobellifuori/rivedila7/belli-dentro-belli-fuori-puntata-del-932024-09-03-2024-530432',
        'md5': 'f01608c9e2507cd637c399ae2c476ffb',
        'info_dict': {
            'id': 'belli-dentro-belli-fuori-puntata-del-932024-09-03-2024-530432',
            'ext': 'mp4',
            'title': 'Belli dentro belli fuori - Puntata del  9/3/2024',
            'duration': 1796,
            'thumbnail': 'https://images.la7play.it/video/111/0_po1fdrop/belli-dentro-belli-fuori-puntata-del-9-3-2024/scena-854x480.webp',
            'timestamp': 1709981573,
            'upload_date': '20240309',
            'modified_timestamp': 1710144374,
            'modified_date': '20240311',
        },
    }, {
        # Full episode, "episodi" path segment (entity type NodeReplica)
        'url': 'https://www.la7play.it/mercanti-dellanima-lai-e-il-nostro-futuro/episodi/st-1-episodio-2-395896',
        'md5': 'bbb51a9313f8bdaa1ee777edfedb1207',
        'info_dict': {
            'id': 'st-1-episodio-2-395896',
            'ext': 'mp4',
            'title': 'St. 1 Episodio 2',
            'description': 'md5:196f0586d0bc174addda6af1d3d1e574',
            'duration': 3946,
            'thumbnail': 'https://images.la7play.it/video/0/400/0_0usrx8nr_0_wwaki72o_2/st-1-episodio-2/scena-854x480.webp',
            'season': 'Season 1',
            'season_number': 1,
            'episode': 'Episode 2',
            'episode_number': 2,
            'timestamp': 1791845946,
            'upload_date': '20261012',
            'modified_timestamp': 1792070405,
            'modified_date': '20261015',
        },
    }, {
        # Full episode, "puntate" path segment (entity type NodeReplica)
        'url': 'https://www.la7play.it/in-onda/puntate/puntata-del-1-11-2026-398431',
        'md5': 'd67876ec61b92393fdf09e2dc2575982',
        'info_dict': {
            'id': 'puntata-del-1-11-2026-398431',
            'ext': 'mp4',
            'title': 'D\'Alema, un ex comunista tra il \'68 e Meloni - Puntata del 1/11/2026',
            'description': 'md5:cd6bf6963b1de91d4c7ac62b26dc1c31',
            'duration': 4406,
            'thumbnail': 'https://images.la7play.it/video/0/406/0_h6jds5l2_0_fh960gys_2/d-alema-un-ex-comunista-tra-il-68-e-meloni-puntata-del-1-11/scena-854x480.webp',
            'season': 'Season 29',
            'season_number': 29,
            'episode': 'Episode 7',
            'episode_number': 7,
            'timestamp': 1793570167,
            'upload_date': '20261101',
            'modified_timestamp': 1793604614,
            'modified_date': '20261102',
        },
    }, {
        # Clip/video (entity type NodeVideo)
        'url': 'https://www.la7play.it/in-onda/video/crisi-in-venezuela-lintervista-a-luciana-castellina-05-01-2026-626950',
        'md5': '00de82356f72c66112a77d3718bba21e',
        'info_dict': {
            'id': 'crisi-in-venezuela-lintervista-a-luciana-castellina-05-01-2026-626950',
            'ext': 'mp4',
            'title': 'Crisi in Venezuela, l\'intervista a Luciana Castellina',
            'duration': 102,
            'description': 'md5:e5b7a733dffc04a24249afd0278b769f',
            'thumbnail': 'https://images.la7play.it/video/111/0_2544fg79/crisi-in-venezuela-l-intervista-a-luciana-castellina/scena-854x480.webp',
            'timestamp': 1767647390,
            'upload_date': '20260105',
            'modified_timestamp': 1767647725,
            'modified_date': '20260105',
        },
    }, {
        # Single path segment, also: video with only one resolution
        'url': 'https://www.la7play.it/dream-bike-20-09-2026-393369',
        'md5': '29a2adcda6d8b5b626b9aef19421996e',
        'info_dict': {
            'id': 'dream-bike-20-09-2026-393369',
            'ext': 'mp4',
            'title': 'Puntata del 23/9/2026',
            'duration': 1782,
            'thumbnail': 'https://images.la7play.it/video/0/397/0_c4lgs673_0_zzscdbmp_2/puntata-del-23-9-2026/scena-854x480.webp',
            'season': 'Season 1',
            'season_number': 1,
            'episode': 'Episode 1',
            'episode_number': 1,
            'timestamp': 1789858785,
            'upload_date': '20260919',
            'modified_timestamp': 1793618784,
            'modified_date': '20261102',
        },
    }, {
        # Video with reconstructed direct HTTPS URL
        'url': 'https://www.la7play.it/otto-e-mezzo/rivedila7/otto-e-mezzo-26-06-2026-650566',
        'md5': '1b3fbd1be2a867730cb644d976e8af4a',
        'info_dict': {
            'id': 'otto-e-mezzo-26-06-2026-650566',
            'ext': 'mp4',
            'title': 'La regola del caos - Otto e Mezzo - Puntata del 26/6/2026',
            'duration': 2197,
            'thumbnail': 'https://images.la7play.it/video/111/0_bbomr2tk/la-regola-del-caos-otto-e-mezzo-puntata-del-26-6-2026/scena-854x480.webp',
            'timestamp': 1782503632,
            'upload_date': '20260626',
            'modified_timestamp': 1782540689,
            'modified_date': '20260627',
        },
        'params': {
            'format': 'b[protocol=https]',
        },
    }, {
        # Video with subtitiles
        'url': 'https://www.la7play.it/piazzapulita/video/dal-dibattito/bortone-aboliamo-la-parola-maranza-e-classista-e-razzista-30-10-2026-398286',
        'md5': '5b3a510d617e77b0ec890fbb31378136',
        'info_dict': {
            'id': 'bortone-aboliamo-la-parola-maranza-e-classista-e-razzista-30-10-2026-398286',
            'ext': 'mp4',
            'title': 'Bortone: "Aboliamo la parola maranza, è classista e razzista"',
            'description': 'md5:f626210b971efed522d6baf348704209',
            'duration': 82,
            'thumbnail': 'https://images.la7play.it/video/111/0_r2k05j89/bortone-aboliamo-la-parola-maranza-e-classista-e-razzista/scena-854x480.webp',
            'timestamp': 1793348588,
            'upload_date': '20261030',
            'modified_timestamp': 1793348708,
            'modified_date': '20261030',
            'subtitles': 'count:2',
        },
    }, {
        # la7.it still redirects here; same GraphQL path
        'url': 'http://www.la7.it/in-onda/video/carovita-schlein-benzina-sopra-i-due-euro-bollette-care-tassino-subito-gli-extraprofitti-delle-02-09-2026-655938',
        'info_dict': {
            'id': 'carovita-schlein-benzina-sopra-i-due-euro-bollette-care-tassino-subito-gli-extraprofitti-delle-02-09-2026-655938',
            'ext': 'mp4',
            'title': 'md5:fae53e9a9e9a6d9648ce83debd5e9caa',
            'description': 'md5:f32d760ca229e4cbd2881a078ec2f4ba',
            'thumbnail': r're:https://images\.la7play\.it/.+',
            'upload_date': '20260902',
            'timestamp': 1788339901,
            'modified_date': '20260902',
            'modified_timestamp': 1788339960,
            'duration': 111,
        },
    }, {
        'url': 'http://www.la7.it/omnibus/rivedila7/omnibus-news-02-07-2016-189077',
        'only_matching': True,
    }, {
        'url': 'https://www.la7play.it/embedded/la7?content=400066',
        'only_matching': True,
    }, {
        'url': 'https://www.la7.it/embedded/la7?tid=player&content=400066',
        'only_matching': True,
    }, {
        'url': 'https://tg.la7.it/repliche-tgla7?id=400066',
        'only_matching': True,
    }]
    _HOST = 'https://awsvodpkg.iltrovatore.it'

    @classmethod
    def suitable(cls, url):
        return False if any(ie.suitable(url) for ie in (LA7PodcastEpisodeIE, LA7PodcastIE)) else super().suitable(url)

    # Endpoints IDs are hardcoded in the JS bundle,
    # but may never be called because of Next.js hydration.
    # Actual call parameters can be extracted via the mobile app:
    # https://play.google.com/store/apps/details?id=it.la7.it
    def _call_api(self, video_id, endpoint_desc, endpoint_id, payload):
        serialized = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        return self._download_json(
            f'https://www.la7play.it/api/gql/{endpoint_id}/{serialized}', video_id,
            note=f'Downloading {endpoint_desc}',
            errnote=f'Failed to download {endpoint_desc}')['data']['route']

    def _generate_mp4_url(self, quality, m3u8_formats):
        for f in m3u8_formats:
            if quality.startswith('//'):
                quality = quality[1:]
            if f['vcodec'] == 'none' or quality not in f['url']:
                continue

            http_f = f.copy()
            del http_f['manifest_url']
            http_f.update({
                'format_id': join_nonempty('https', http_f['format_id'].removeprefix('hls-')),
                'url': f'{self._HOST}{quality}.mp4',
                'protocol': 'https',
            })
            yield http_f

    def _canonical_play_url(self, content_id):
        webpage = self._download_webpage(
            f'https://www.la7play.it/embedded/la7?content={content_id}', content_id)
        return self._search_regex(
            (r'<link\s+rel="canonical"\s*href="(https?://[^"]+)"',
             r'<link\s+href="(https?://[^"]+)"\s*rel="canonical"'),
            webpage, 'canonical URL')

    def _real_extract(self, url):
        groups = self._match_valid_url(url).groupdict()
        video_id, path = groups['id'], groups.get('path')
        content_id = traverse_obj(url, ({parse_qs}, 'content', 0))
        if not path or path.rstrip('/') == '/embedded/la7':
            canonical = self._canonical_play_url(content_id or video_id)
            if canonical != url:
                return self.url_result(canonical, ie=self.ie_key())
            raise ExtractorError('Unable to resolve video URL', expected=True)

        type_info = self._call_api(
            video_id, 'entity type info', 'cf87a75d078158e9', {'path': path})

        type_name = traverse_obj(type_info, ('entity', '__typename', {str}))
        self.write_debug(f'Entity type: {type_name}')
        match type_name:
            case 'NodeVideo':
                endpoint_id = '9e6877beb0b950cb'
            case 'NodeReplica':
                endpoint_id = 'a9448166e3cd0b3d'
            case 'NodeEventoSingolo':
                endpoint_id = '150c651a74b13c6d'
            case 'NodeLiveStreaming':
                self.report_drm(video_id)
            case 'NodePaginaHub' | 'NodeGuidaTv' | 'NodeAggregatoreTassonomie' | None:
                raise ExtractorError('There is no video for this URL', expected=True)
            case _:
                raise ExtractorError(f'Unsupported entity type "{type_name}"')

        data = self._call_api(video_id, 'video data', endpoint_id, {
            'path': traverse_obj(type_info, ('entity', 'path', {str})) or path,
        })['entity']

        # Example remote URLs:
        # //content/entry/data/0/608/0_wsbps6kq_0_edzqb9id_1.mp4,/content/entry/data/0/608/0_wsbps6kq_0_bvd3ckkf_1.mp4
        # /nk/content/entry/data/0/400/0_0usrx8nr_0_djtnz3hm_2.mp4,/nk/content/entry/data/0/400/0_0usrx8nr_0_4lup3o64_2.mp4
        # /nk/content/entry/data/0/397/0_c4lgs673_0_ualutund_2.mp4
        video_path = data['uploadVideo']['cf_remote_url'].replace('.mp4', '')

        formats = self._extract_mpd_formats(
            f'{self._HOST}/local/dash/,{video_path},.mp4.urlset/manifest.mpd',
            video_id, mpd_id='dash', fatal=False)
        m3u8_formats = self._extract_m3u8_formats(
            f'{self._HOST}/local/hls/,{video_path},.mp4.urlset/master.m3u8',
            # _generate_mp4_url depends on the m3u8_id value being 'hls'
            video_id, 'mp4', m3u8_id='hls', fatal=False)
        formats.extend(m3u8_formats)

        # Only older videos have direct HTTP links
        if traverse_obj(data, ('uploadVideo', 'cf_old_entry_id', {str})):
            for q in filter(None, video_path.split(',')):
                formats.extend(self._generate_mp4_url(q, m3u8_formats))

        subtitles = {}
        for sub in traverse_obj(data, (
            'uploadVideo', 'subtitles', lambda _, v: v['lang'] and url_or_none(v['url']),
        )):
            subtitles.setdefault(sub['lang'], []).append({'url': sub['url']})

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(data, {
                'title': ('title', {str}),
                'description': ('body', 'plainValue', {str}),
                'duration': ('uploadVideo', 'cf_duration', {int_or_none}),
                'season_number': ('uploadVideo', 'stagione', {int_or_none}),
                'episode_number': ('uploadVideo', 'episodio', {int_or_none}),
                'timestamp': ('created', 'timestamp', {int_or_none}),
                'modified_timestamp': ('changed', 'timestamp', {int_or_none}),
                'thumbnail': ('uploadVideo', 'cf_thumbnail_url', {url_or_none}),
            }),
        }


class LA7PodcastEpisodeIE(InfoExtractor):
    IE_NAME = 'la7.it:pod:episode'
    _VALID_URL = r'https?://(?:www\.)?la7(?:play)?\.it/[^/]+/podcast/([^/]+-)?(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://www.la7.it/voicetown/podcast/la-carezza-delle-memoria-di-carlo-verdone-23-03-2021-371497',
        'skip': 'native MP3 gone; page redirects to la7play.it (Spotify/Apple/Amazon only)',
        'md5': '7737d4d79b3c1a34b3de3e16297119ed',
        'params': {'skip_download': True},
        'info_dict': {
            'id': '371497',
            'ext': 'mp3',
            'title': '"La carezza delle memoria" di Carlo Verdone',
            'description': 'md5:bd032fc75933400d72afde6f2753e4d7',
            'thumbnail': 'https://www.la7.it/sites/default/files/podcast/371497.jpg',
            'upload_date': '20210323',
        },
    }, {
        # embed url
        'url': 'https://www.la7.it/embed/podcast/371497',
        'only_matching': True,
    }, {
        # date already in the title
        'url': 'https://www.la7.it/propagandalive/podcast/lintervista-di-diego-bianchi-ad-annalisa-cuzzocrea-puntata-del-1932021-20-03-2021-371130',
        'only_matching': True,
    }, {
        # title same as show_title
        'url': 'https://www.la7.it/otto-e-mezzo/podcast/otto-e-mezzo-26-03-2021-372340',
        'only_matching': True,
    }, {
        'url': 'https://www.la7play.it/voicetown/podcast/la-carezza-delle-memoria-di-carlo-verdone-23-03-2021-371497',
        'only_matching': True,
    }]

    def _extract_info(self, webpage, video_id=None, ppn=None, url=None):
        if not video_id:
            video_id = self._search_regex(
                r'data-nid=([\'"])(?P<vid>\d+)\1',
                webpage, 'video_id', group='vid')

        media_url = url_or_none(self._search_regex(
            (r'src\s*:\s*([\'"])(?P<url>\S+?mp3.+?)\1',
             r'data-podcast\s*=\s*([\'"])(?P<url>\S+?mp3.+?)\1'),
            webpage, 'media_url', group='url', default=None))
        if not media_url:
            raise ExtractorError(
                'Native MP3 is gone; this podcast is only on Spotify/Apple/Amazon',
                expected=True)
        formats = [{
            'url': media_url,
            'format_id': 'http-mp3',
            'ext': 'mp3',
            'acodec': 'mp3',
            'vcodec': 'none',
            **({'http_headers': {'Referer': url}} if url else {}),
        }]

        title = self._html_search_regex(
            (r'<div class="title">(?P<title>.+?)</',
             r'<title>(?P<title>[^<]+)</title>',
             r'title:\s*([\'"])(?P<title>.+?)\1'),
            webpage, 'title', group='title')

        description = (
            self._html_search_regex(
                (r'<div class="description">(.+?)</div>',
                 r'<div class="description-mobile">(.+?)</div>',
                 r'<div class="box-txt">([^<]+?)</div>',
                 r'<div class="field-content"><p>(.+?)</p></div>'),
                webpage, 'description', default=None)
            or self._html_search_meta('description', webpage))

        thumb = self._html_search_regex(
            (r'<div class="podcast-image"><img src="(.+?)"></div>',
             r'<div class="container-embed"[^<]+url\((.+?)\);">',
             r'<div class="field-content"><img src="(.+?)"'),
            webpage, 'thumbnail', fatal=False, default=None)

        duration = parse_duration(self._html_search_regex(
            r'<span class="(?:durata|duration)">([\d:]+)</span>',
            webpage, 'duration', fatal=False, default=None))

        date = self._html_search_regex(
            r'class="data">\s*(?:<span>)?([\d\.]+)\s*</',
            webpage, 'date', default=None)

        date_alt = self._search_regex(
            r'(\d+[\./]\d+[\./]\d+)', title, 'date_alt', default=None)
        ppn = ppn or self._search_regex(
            r'ppN:\s*([\'"])(?P<ppn>.+?)\1',
            webpage, 'ppn', group='ppn', default=None)
        # if the date is not in the title
        # and title is the same as the show_title
        # add the date to the title
        if date and not date_alt and ppn and ppn.lower() == title.lower():
            title = f'{title} del {date}'
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': float_or_none(duration),
            'formats': formats,
            'thumbnail': thumb,
            'upload_date': unified_strdate(date),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return self._extract_info(webpage, video_id, url=url)


class LA7PodcastIE(LA7PodcastEpisodeIE):  # XXX: Do not subclass from concrete IE
    IE_NAME = 'la7.it:podcast'
    _VALID_URL = r'https?://(?:www\.)?la7(?:play)?\.it/(?P<id>[^/]+)/podcast/?(?:$|[#?])'

    _TESTS = [{
        'url': 'https://www.la7.it/propagandalive/podcast',
        'skip': 'extractor broken: Unable to extract title',
        'info_dict': {
            'id': 'propagandalive',
            'title': 'Propaganda Live',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://www.la7play.it/propagandalive/podcast',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        title = (
            self._html_search_regex(
                r'<h1.*?>(.+?)</h1>', webpage, 'title', fatal=False, default=None)
            or self._og_search_title(webpage))
        ppn = self._search_regex(
            r'window\.ppN\s*=\s*([\'"])(?P<ppn>.+?)\1',
            webpage, 'ppn', group='ppn', default=None)

        entries = []
        for episode in re.finditer(
                r'<div class="container-podcast-property">([\s\S]+?)(?:</div>\s*){3}',
                webpage):
            entries.append(self._extract_info(episode.group(1), ppn=ppn))

        return self.playlist_result(entries, playlist_id, title)
