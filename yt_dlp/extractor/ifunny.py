import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    orderedSet,
    remove_end,
    traverse_obj,
    try_call,
    url_or_none,
)


class IFunnyBaseIE(InfoExtractor):
    def _call_api(self, path, video_id, **kwargs):
        csrf = try_call(lambda: self._get_cookies('https://ifunny.co/')['x-csrf-token'].value)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': 'https://ifunny.co/',
            'X-Requested-With': 'fetch',
        }
        if csrf:
            headers['X-Csrf-Token'] = csrf
        return self._download_json(f'https://ifunny.co/api{path}', video_id, headers=headers, **kwargs)


class IFunnyIE(IFunnyBaseIE):
    IE_NAME = 'ifunny'
    IE_DESC = 'iFunny'
    _VALID_URL = r'https?://(?:www\.)?ifunny\.co/video/(?:[^/?#]*-)?(?P<id>[A-Za-z0-9]+)(?:[?#]|$)'
    _TESTS = [
        {
            'url': 'https://ifunny.co/video/A2GwDqRmA',
            'md5': '270fd3350d651b64e139d5d8cbe23434',
            'info_dict': {
                'id': 'A2GwDqRmA',
                'ext': 'mp4',
                'title': 'Video memes A2GwDqRmA by filthyfrankthe2nd',
                'thumbnail': r're:https://(?:img|imageproxy)\.getfn\.io/.+',
                'uploader': 'filthyfrankthe2nd',
                'uploader_id': 'filthyfrankthe2nd',
                'uploader_url': 'https://ifunny.co/user/filthyfrankthe2nd',
                'timestamp': 1693410059,
                'upload_date': '20230830',
                'width': 480,
                'height': 782,
            },
        },
        {
            'url': 'https://ifunny.co/video/A2GwDqRmA?s=cl',
            'only_matching': True,
        },
        {
            'url': 'https://ifunny.co/video/all-you-can-eat-buffet-near-me-fn0T3socD',
            'only_matching': True,
        },
    ]
    _GENERIC_SITE_DESCRIPTION = 'IFunny is fun of your life'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = url_or_none(self._og_search_video_url(webpage, default=None))
        if not video_url:
            video_url = url_or_none(
                self._html_search_regex(r'<video[^>]+data-src=["\']([^"\']+)', webpage, 'video url', default=None),
            )
        if not video_url:
            content = self._call_api(f'/v1/content/{video_id}', video_id, fatal=False) or {}
            if content.get('type') and content['type'] != 'video':
                self.raise_no_formats('This iFunny post is not a video', expected=True)
            video_url = url_or_none(content.get('url'))
        if not video_url:
            self.raise_no_formats('Unable to extract video URL', video_id=video_id)

        json_ld = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        json_ld.pop('url', None)

        title = self._og_search_title(webpage) or video_id
        title = re.sub(r':\s*\d+\s+comments?\s*$', '', remove_end(title, ' - iFunny'))

        description = self._og_search_description(webpage)
        if description and description.startswith(self._GENERIC_SITE_DESCRIPTION):
            description = None

        uploader = self._html_search_meta('author', webpage)
        thumbnail = self._html_search_regex(
            r'<video[^>]+data-poster=["\']([^"\']+)', webpage, 'thumbnail', default=None,
        ) or self._og_search_thumbnail(webpage)

        return {
            **json_ld,
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': url_or_none(thumbnail),
            'uploader': uploader,
            'uploader_id': uploader,
            'uploader_url': f'https://ifunny.co/user/{uploader}' if uploader else None,
            'width': int_or_none(self._og_search_property('video:width', webpage, default=None)),
            'height': int_or_none(self._og_search_property('video:height', webpage, default=None)),
        }


class IFunnyUserIE(IFunnyBaseIE):
    IE_NAME = 'ifunny:user'
    IE_DESC = 'iFunny user timeline'
    _VALID_URL = (
        r'https?://(?:www\.)?ifunny\.co/user/(?P<id>[A-Za-z0-9_]+)(?:/timeline(?:/(?P<next>[\d.]+))?)?(?:[?#]|$)'
    )
    _TESTS = [
        {
            'url': 'https://ifunny.co/user/Soundcloud_Brap',
            'info_dict': {
                'id': 'Soundcloud_Brap',
                'title': 'Soundcloud_Brap',
            },
            'playlist_mincount': 3,
            'params': {
                'extract_flat': 'in_playlist',
                'playlistend': 5,
                'skip_download': True,
            },
        },
        {
            'url': 'https://ifunny.co/user/ArizonaTeaMan',
            'only_matching': True,
        },
        {
            'url': 'https://ifunny.co/user/Soundcloud_Brap/timeline/1755490774.216',
            'only_matching': True,
        },
    ]

    def _video_ids_from_webpage(self, webpage):
        return orderedSet(re.findall(r'https?://(?:www\.)?ifunny\.co/video/(?:[^/?#"\']*-)?([A-Za-z0-9]+)', webpage))

    def _next_token_from_webpage(self, webpage):
        show_more = self._search_regex(
            r'<a[^>]+href="([^"]+)"[^>]*>\s*<span[^>]*>Show more', webpage, 'next page', default=None,
        )
        tokens = re.findall(r'/timeline/([\d.]+)', show_more or '')
        return tokens[-1] if tokens else None

    def _entries(self, user_id, start_token):
        seen = set()
        webpage = self._download_webpage(
            f'https://ifunny.co/user/{user_id}' + (f'/timeline/{start_token}' if start_token else ''),
            user_id,
            'Downloading user page',
        )
        for video_id in self._video_ids_from_webpage(webpage):
            if video_id not in seen:
                seen.add(video_id)
                yield self.url_result(f'https://ifunny.co/video/{video_id}', IFunnyIE, video_id)

        next_token = self._next_token_from_webpage(webpage)
        seen_tokens = set()
        while next_token and next_token not in seen_tokens:
            seen_tokens.add(next_token)
            page = self._call_api(
                f'/v1/user/{user_id}/timeline/{next_token}', user_id, note='Downloading user timeline', fatal=False,
            )
            if not page:
                break
            for item in traverse_obj(page, ('items', ..., {dict})):
                if item.get('type') != 'video':
                    continue
                video_id = item.get('id')
                if not video_id or video_id in seen:
                    continue
                seen.add(video_id)
                yield self.url_result(
                    traverse_obj(item, ('canonical', {url_or_none}), ('link', {url_or_none}))
                    or f'https://ifunny.co/video/{video_id}',
                    IFunnyIE,
                    video_id,
                    item.get('title'),
                )
            pagination = page.get('pagination') or {}
            if not pagination.get('hasNext'):
                break
            next_token = pagination.get('next')

    def _real_extract(self, url):
        user_id, start_token = self._match_valid_url(url).group('id', 'next')
        return self.playlist_result(self._entries(user_id, start_token), user_id, user_id)
