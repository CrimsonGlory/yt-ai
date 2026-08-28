import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    format_field,
    get_element_by_class,
    get_element_by_id,
    get_element_html_by_attribute,
    get_element_html_by_class,
    get_elements_by_class,
    int_or_none,
    unified_timestamp,
    url_or_none,
    urlencode_postdata,
)
from ..utils.traversal import find_element, find_elements, traverse_obj


class NubilesPornIE(InfoExtractor):
    _NETRC_MACHINE = 'nubiles-porn'
    _VALID_URL = r'''(?x)
        https?://(?:members\.)?nubiles-porn\.com/video/
        (?:watch|shorts(?:/elevate)?)/
        (?P<id>\d+)
        (?:/(?P<display_id>[\w-]+))?
    '''

    _TESTS = [{
        'url': 'https://nubiles-porn.com/video/shorts/elevate/232430/lets-taste-his-cum-together-s6e5',
        'md5': '5d925b40268740bbc794c2dc9f6c5a17',
        'info_dict': {
            'id': '232430',
            'ext': 'mp4',
            'title': 'Lets Taste His Cum Together - S6:E5',
            'display_id': 'lets-taste-his-cum-together-s6e5',
            'age_limit': 18,
            'availability': 'public',
            'channel': 'Cum Swapping Sis',
            'channel_id': '65',
            'channel_url': 'https://members.nubiles-porn.com/video/website/65',
            'series': 'Cum Swapping Sis',
            'series_id': '65',
            'season': 'Season 6',
            'season_number': 6,
            'episode': 'Episode 5',
            'episode_number': 5,
        },
    }, {
        'url': 'https://members.nubiles-porn.com/video/watch/165320/trying-to-focus-my-one-track-mind-s3e1',
        'skip': 'Requires login',
        'md5': 'fa7f09da8027c35e4bdf0f94f55eac82',
        'info_dict': {
            'id': '165320',
            'title': 'Trying To Focus My One Track Mind - S3:E1',
            'ext': 'mp4',
            'display_id': 'trying-to-focus-my-one-track-mind-s3e1',
            'thumbnail': 'https://images.nubiles-porn.com/videos/trying_to_focus_my_one_track_mind/samples/cover1280.jpg',
            'description': 'md5:81f3d4372e0e39bff5c801da277a5141',
            'timestamp': 1676160000,
            'upload_date': '20230212',
            'channel': 'Younger Mommy',
            'channel_id': '64',
            'channel_url': 'https://members.nubiles-porn.com/video/website/64',
            'like_count': int,
            'average_rating': float,
            'age_limit': 18,
            'categories': ['Big Boobs', 'Big Naturals', 'Blowjob', 'Brunette', 'Cowgirl', 'Girl Orgasm', 'Girl-Boy',
                           'Glasses', 'Hardcore', 'Milf', 'Shaved Pussy', 'Tattoos', 'YoungerMommy.com'],
            'tags': list,
            'cast': ['Kenzie Love'],
            'availability': 'needs_auth',
            'series': 'Younger Mommy',
            'series_id': '64',
            'season': 'Season 3',
            'season_number': 3,
            'episode': 'Episode 1',
            'episode_number': 1,
        },
    }, {
        'url': 'https://nubiles-porn.com/video/watch/254201/its-too-hot-so-im-sleeping-naked',
        'only_matching': True,
    }]

    def _perform_login(self, username, password):
        login_webpage = self._download_webpage(
            'https://nubiles-porn.com/login', video_id=None, impersonate=True)
        inputs = self._hidden_inputs(login_webpage)
        inputs.update({'username': username, 'password': password})
        self._request_webpage(
            'https://nubiles-porn.com/authentication/login', None,
            data=urlencode_postdata(inputs), impersonate=True)

    def _download_nubiles_webpage(self, url, video_id):
        if not getattr(self, '_nubiles_primed', False):
            self._download_webpage(
                'https://nubiles-porn.com/', video_id,
                note='Priming tour session', impersonate=True, fatal=False)
            self._nubiles_primed = True
        return self._download_webpage(url, video_id, impersonate=True)

    def _real_extract(self, url):
        url_match = self._match_valid_url(url)
        video_id = url_match.group('id')
        display_id = url_match.group('display_id')
        season_number, episode_number = None, None
        se_m = re.search(r'-s(\d+)e(\d+)$', display_id or '')
        if se_m:
            season_number, episode_number = int(se_m.group(1)), int(se_m.group(2))

        page = self._download_nubiles_webpage(url, video_id)
        if '<title>Security Check</title>' in page or '/turnstile/challenge' in page:
            raise ExtractorError('Cloudflare Turnstile challenge', expected=True)

        slide = get_element_html_by_attribute('data-video-id', video_id, page)
        media_html = slide or get_element_html_by_class('watch-page-video-wrapper', page)
        if not media_html:
            self.raise_login_required('This video is only available for members')

        media_entries = self._parse_html5_media_entries(url, media_html, video_id)
        formats = traverse_obj(media_entries, (0, 'formats')) or []
        if not formats:
            self.raise_login_required('This video is only available for members')

        for f in formats:
            f['height'] = int_or_none(self._search_regex(
                r'_(\d+)\.mp4', f.get('url') or '', 'height', default=None))
            f['impersonate'] = True

        channel_id, channel_name = self._search_regex(
            r'/video/website/(?P<id>\d+).+>(?P<name>\w+).com',
            get_element_html_by_class('site-link', page) or '',
            'channel', default=None, group=('id', 'name')) or (None, None)
        if channel_name:
            channel_name = re.sub(r'([^A-Z]+)([A-Z]+)', r'\1 \2', channel_name)
        else:
            username_html = get_element_html_by_class('swipe-play-username', slide or '') or ''
            channel_id = self._search_regex(
                r'/video/(?:shorts/)?website/(\d+)', username_html, 'channel id', default=None)
            channel_name = clean_html(username_html) or None

        title = (
            clean_html(get_element_by_class('title', slide or ''))
            or self._search_regex(r'<h2>([^<]+)</h2>', page, 'title', default=None))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'display_id': display_id,
            'thumbnail': traverse_obj(media_entries, (0, 'thumbnail', {url_or_none})),
            'description': clean_html(get_element_html_by_class('content-pane-description', page)),
            'timestamp': unified_timestamp(get_element_by_class('date', page)),
            'channel': channel_name,
            'channel_id': channel_id,
            'channel_url': format_field(channel_id, None, 'https://members.nubiles-porn.com/video/website/%s'),
            'like_count': int_or_none(get_element_by_id('likecount', page)),
            'average_rating': float_or_none(get_element_by_class('score', page)),
            'age_limit': 18,
            'categories': traverse_obj(page, ({find_element(cls='categories')}, {find_elements(cls='btn')}, ..., {clean_html})) or None,
            'tags': traverse_obj(page, ({find_elements(cls='tags')}, 1, {find_elements(cls='btn')}, ..., {clean_html})) or None,
            'cast': get_elements_by_class('content-pane-performer', page) or None,
            'availability': 'public' if slide else 'needs_auth',
            'series': channel_name,
            'series_id': channel_id,
            'season_number': season_number,
            'episode_number': episode_number,
            'impersonate': True,
        }
