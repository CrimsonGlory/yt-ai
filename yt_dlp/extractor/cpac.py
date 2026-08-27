from .common import InfoExtractor
from ..utils import (
    int_or_none,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    urljoin,
)


class CPACIE(InfoExtractor):
    IE_NAME = 'cpac'
    _VALID_URL = r'https?://(?:www\.)?cpac\.ca/(?:[^?#]+/)?(?P<fr>l-)?episode(?:/[^?#]*)?\?(?:[^#]*&)?id=(?P<id>[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12})'
    _TESTS = [{
        'url': 'https://www.cpac.ca/headline-politics/episode/alberta-premier-danielle-smith-discusses-us-tariffs--august-26-2026?id=2ca18255-b9a3-451b-a018-b36f730de151',
        'md5': 'b845e13ff1591d421c53b3b570a4b0e8',
        'info_dict': {
            'id': '2ca18255-b9a3-451b-a018-b36f730de151',
            'ext': 'mp4',
            'title': 'Alberta Premier Danielle Smith Discusses U.S. Tariffs – August 26, 2026',
            'description': 'md5:7f335d3cca31e8977eb2aec9f59558e4',
            'timestamp': 1787702400,
            'upload_date': '20260826',
            'thumbnail': 'https://images.cpac.ca/episode/thumbnail/2026/08/2ca18255-b9a3-451b-a018-b36f730de151/smith826.jpg',
            'categories': ['Headline Politics'],
        },
        'params': {
            'format': 'bestvideo',
            'hls_prefer_native': True,
        },
    }, {
        'url': 'https://www.cpac.ca/episode?id=fc7edcae-4660-47e1-ba61-5b7f29a9db0f',
        'skip': 'video gone',
        'md5': 'e46ad699caafd7aa6024279f2614e8fa',
        'info_dict': {
            'id': 'fc7edcae-4660-47e1-ba61-5b7f29a9db0f',
            'ext': 'mp4',
            'upload_date': '20220215',
            'title': 'News Conference to Celebrate National Kindness Week – February 15, 2022',
            'description': 'md5:466a206abd21f3a6f776cdef290c23fb',
            'timestamp': 1644901200,
        },
        'params': {
            'format': 'bestvideo',
            'hls_prefer_native': True,
        },
    }, {
        'url': 'https://www.cpac.ca/episode?id=2ca18255-b9a3-451b-a018-b36f730de151',
        'only_matching': True,
    }, {
        'url': 'https://www.cpac.ca/a-la-une/l-episode/pm-de-lalberta-danielle-smith--tarifs-douaniers-americains?id=2ca18255-b9a3-451b-a018-b36f730de151',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, is_fr = self._match_valid_url(url).group('id', 'fr')
        url_lang = 'fr' if is_fr else 'en'

        content = self._download_json(
            'https://www.cpac.ca/api/1/services/episode-info.json',
            video_id, query={'crafterSite': 'cpactv', 'id': video_id})
        details = try_get(content, lambda x: x['component']['details'], dict) or {}
        video_url = str_or_none(details.get('videoUrl'))
        formats = []
        if video_url:
            formats = self._extract_m3u8_formats(video_url, video_id, m3u8_id='hls', ext='mp4')
            for fmt in formats:
                # prefer language to match URL
                fmt_lang = fmt.get('language')
                if fmt_lang == url_lang:
                    fmt['language_preference'] = 10
                elif not fmt_lang:
                    fmt['language_preference'] = -1
                else:
                    fmt['language_preference'] = -10

        category = str_or_none(details.get(f'category_{url_lang}_t'))
        v_type = details.get('type')

        return {
            'id': video_id,
            'formats': formats,
            'title': str_or_none(details.get(f'title_{url_lang}_t')),
            'description': str_or_none(details.get(f'description_{url_lang}_t')),
            'timestamp': unified_timestamp(details.get('liveDateTime')),
            'categories': [category] if category else None,
            'thumbnail': urljoin(url, str_or_none(details.get(f'image_{url_lang}_s'))),
            'is_live': (v_type == 'live') if v_type is not None else None,
        }


class CPACPlaylistIE(InfoExtractor):
    IE_NAME = 'cpac:playlist'
    _VALID_URL = r'(?i)https?://(?:www\.)?cpac\.ca/(?:program|search|(?P<fr>emission|rechercher))\?(?:[^&]+&)*?(?P<id>(?:id=\d+|programId=\d+|key=[^&]+))'

    _TESTS = [{
        'url': 'https://www.cpac.ca/program?id=6',
        'skip': 'video gone',
        'info_dict': {
            'id': 'id=6',
            'title': 'Headline Politics',
            'description': 'Watch CPAC’s signature long-form coverage of the day’s pressing political events as they unfold.',
        },
        'playlist_count': 10,
    }, {
        'url': 'https://www.cpac.ca/search?key=hudson&type=all&order=desc',
        'skip': 'video gone',
        'info_dict': {
            'id': 'key=hudson',
            'title': 'hudson',
        },
        'playlist_count': 22,
    }, {
        'url': 'https://www.cpac.ca/search?programId=50',
        'skip': 'video gone',
        'info_dict': {
            'id': 'programId=50',
            'title': '50',
        },
        'playlist_count': 9,
    }, {
        'url': 'https://www.cpac.ca/emission?id=6',
        'only_matching': True,
    }, {
        'url': 'https://www.cpac.ca/rechercher?key=hudson&type=all&order=desc',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url_lang = 'fr' if any(x in url for x in ('/emission?', '/rechercher?')) else 'en'
        pl_type, list_type = ('program', 'itemList') if any(x in url for x in ('/program?', '/emission?')) else ('search', 'searchResult')
        api_url = (
            f'https://www.cpac.ca/api/1/services/contentModel.json?url=/site/website/{pl_type}/index.xml&crafterSite=cpacca&{video_id}')
        content = self._download_json(api_url, video_id)
        entries = []
        total_pages = int_or_none(try_get(content, lambda x: x['page'][list_type]['totalPages']), default=1)
        for page in range(1, total_pages + 1):
            if page > 1:
                api_url = update_url_query(api_url, {'page': page})
                content = self._download_json(
                    api_url, video_id,
                    note=f'Downloading continuation - {page}',
                    fatal=False)

            for item in try_get(content, lambda x: x['page'][list_type]['item'], list) or []:
                episode_url = urljoin(url, try_get(item, lambda x: x[f'url_{url_lang}_s']))
                if episode_url:
                    entries.append(episode_url)

        return self.playlist_result(
            (self.url_result(entry) for entry in entries),
            playlist_id=video_id,
            playlist_title=try_get(content, lambda x: x['page']['program'][f'title_{url_lang}_t']) or video_id.split('=')[-1],
            playlist_description=try_get(content, lambda x: x['page']['program'][f'description_{url_lang}_t']),
        )
