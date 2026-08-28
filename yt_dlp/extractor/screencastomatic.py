from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    get_element_by_class,
    parse_duration,
    strip_or_none,
    unified_strdate,
    url_or_none,
    urlencode_postdata,
)
from ..utils.traversal import traverse_obj


class ScreencastOMaticIE(InfoExtractor):
    IE_DESC = 'Screencast-O-Matic (ScreenPal)'
    _VALID_URL = r'https?://(?:(?:www\.)?screencast-o-matic\.com|(?:go\.)?screenpal\.com)/(?:(?:watch|player)/|embed\?.*?\bsc=)(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'https://screencast-o-matic.com/watch/cqhtFZTDWy',
        'md5': '7970c26722fadffb83ae17e02a511f78',
        'info_dict': {
            'id': 'cqhtFZTDWy',
            'ext': 'mp4',
            'title': 'Widget Builder Intro',
            'description': 'This video covers the initial setup steps for the Widget Builder in Rebus, including preparing data and configuring the chart to display the data. It also provides guidance on creating and publishing a widget, as well as tips for navigating the Widget Builder stages.',
            'thumbnail': r're:https?://.*\.jpg$',
            'duration': 222,
            'upload_date': '20190527',
        },
    }, {
        'url': 'http://screencast-o-matic.com/watch/c2lD3BeOPl',
        'skip': 'video gone',
        'md5': '483583cb80d92588f15ccbedd90f0c18',
        'info_dict': {
            'id': 'c2lD3BeOPl',
            'ext': 'mp4',
            'title': 'Welcome to 3-4 Philosophy @ DECV!',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'as the title says! also: some general info re 1) VCE philosophy and 2) distance learning.',
            'duration': 369,
            'upload_date': '20141216',
        },
    }, {
        'url': 'http://screencast-o-matic.com/player/c2lD3BeOPl',
        'only_matching': True,
    }, {
        'url': 'http://screencast-o-matic.com/embed?ff=true&sc=cbV2r4Q5TL&fromPH=true&a=1',
        'only_matching': True,
    }, {
        'url': 'https://go.screenpal.com/watch/cqhtFZTDWy',
        'only_matching': True,
    }, {
        'url': 'https://go.screenpal.com/player/cqhtFZTDWy',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        player_url = f'https://go.screenpal.com/player/{video_id}'
        webpage = self._download_webpage(player_url, video_id)

        if 'That content doesn' in webpage or 'class="notFound"' in webpage:
            raise ExtractorError('Video gone or made private', expected=True, video_id=video_id)

        if (self._html_extract_title(webpage) == 'Protected Content'
                or 'This video is private and requires a password' in webpage):
            password = self.get_param('videopassword')

            if not password:
                raise ExtractorError('Password protected video, use --video-password <password>', expected=True)

            form = self._search_regex(
                r'(?is)<form[^>]*>(?P<form>.+?)</form>', webpage, 'login form', group='form')
            form_data = self._hidden_inputs(form)
            form_data.update({
                'scPassword': password,
            })

            webpage = self._download_webpage(
                'https://go.screenpal.com/player/password', video_id, 'Logging in',
                data=urlencode_postdata(form_data))

            if '<small class="text-danger">Invalid password</small>' in webpage:
                raise ExtractorError('Unable to login: Invalid password', expected=True)

        video_url = self._search_regex(
            r'player\.src\(\s*\{[^}]*?\bsrc:\s*"(https?://[^"]+)"',
            webpage, 'video url', default=None) or f'https://go.screenpal.com/player/stream/{video_id}'

        info = {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': (clean_html(get_element_by_class('title-text', webpage))
                      or self._html_extract_title(webpage)),
            'description': strip_or_none(clean_html(get_element_by_class('summary-text', webpage))),
            'http_headers': {'Referer': player_url},
        }

        entries = self._parse_html5_media_entries(player_url, webpage, video_id)
        if entries:
            entry = entries[0]
            info['thumbnail'] = entry.get('thumbnail')
            info['subtitles'] = entry.get('subtitles')

        oembed = self._download_json(
            f'https://go.screenpal.com/oembed/{video_id}', video_id,
            'Downloading oEmbed metadata', fatal=False)
        if oembed:
            info['title'] = info['title'] or oembed.get('title')
            info['thumbnail'] = info.get('thumbnail') or url_or_none(oembed.get('thumbnail_url'))
            info['duration'] = parse_duration(oembed.get('duration'))
            info['width'] = oembed.get('width')
            info['height'] = oembed.get('height')

        metadata = traverse_obj(self._download_json(
            f'https://go.screenpal.com/api/v2/translation/data/{video_id}/en',
            video_id, 'Downloading video metadata', fatal=False), ('metadata', {dict})) or {}
        info['title'] = info['title'] or metadata.get('title')
        info['description'] = info['description'] or strip_or_none(metadata.get('description')) or None
        info['upload_date'] = unified_strdate(metadata.get('publishedAt') or metadata.get('createdAt'))

        return info
