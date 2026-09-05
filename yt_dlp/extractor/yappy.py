from .common import InfoExtractor
from ..utils import (
    OnDemandPagedList,
    int_or_none,
    traverse_obj,
    unified_timestamp,
    url_or_none,
)


class YappyIE(InfoExtractor):
    _VALID_URL = r'https?://yappy\.media/video/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://yappy.media/video/47fea6d8586f48d1a0cf96a7342aabd2',
        'skip': 'stale test sample / site changed',
        'info_dict': {
            'id': '47fea6d8586f48d1a0cf96a7342aabd2',
            'ext': 'mp4',
            'title': 'Куда нажимать? Как снимать? Смотри видос и погнали!🤘🏻',
            'timestamp': 1661893200,
            'description': 'Куда нажимать? Как снимать? Смотри видос и погнали!🤘🏻',
            'thumbnail': 'https://cdn-st.ritm.media/static/pic/thumbnails/0c7c4d73388f47848acaf540d2e2bb8c-thumbnail.jpg',
            'upload_date': '20220830',
            'view_count': int,
            'like_count': int,
            'uploader_id': '59a0c8c485e5410b9c43474bf4c6a373',
            'categories': ['Образование и наука', 'Лайфхак', 'Технологии', 'Арт/искусство'],
            'repost_count': int,
            'uploader': 'YAPPY',
        },
    }, {
        'url': 'https://yappy.media/video/3862451954ad4bd58ae2ccefddb0bd33',
        'md5': '101d58be0850ddbebb76edca4713cd6e',
        'info_dict': {
            'id': '3862451954ad4bd58ae2ccefddb0bd33',
            'ext': 'mp4',
            'title': 'Опиши свой характер 3 словами🙃\n#психология #дружба #отношения',
            'description': 'Опиши свой характер 3 словами🙃\n#психология #дружба #отношения',
            'uploader': 'LENA SHTURMAN',
            'uploader_id': '6793ee3581974a3586fc01e157de6c99',
            'thumbnail': 'md5:ff43ef596dba4f4d44ee08deca842a39',
            'timestamp': 1674726985,
            'upload_date': '20230126',
            'view_count': int,
            'like_count': int,
            'repost_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_ld = self._search_json_ld(webpage, video_id)
        nextjs_data = self._search_nextjs_data(webpage, video_id)

        media_data = (
            traverse_obj(
                nextjs_data, ('props', 'pageProps', ('data', 'OpenGraphParameters')), get_all=False)
            or self._download_json(f'https://yappy.media/api/video/{video_id}', video_id))

        media_url = traverse_obj(media_data, ('link', {url_or_none})) or ''
        has_watermark = media_url.endswith('-wm.mp4')

        formats = [{
            'url': media_url,
            'ext': 'mp4',
            'format_note': 'Watermarked' if has_watermark else None,
            'preference': -10 if has_watermark else None,
        }] if media_url else []

        if has_watermark:
            formats.append({
                'url': media_url.replace('-wm.mp4', '.mp4'),
                'ext': 'mp4',
            })

        audio_link = traverse_obj(media_data, ('audio', 'link'))
        if audio_link:
            formats.append({
                'url': audio_link,
                'ext': 'mp3',
                'acodec': 'mp3',
                'vcodec': 'none',
            })

        return {
            'id': video_id,
            'title': (json_ld.get('description') or self._html_search_meta(['og:title'], webpage)
                      or self._html_extract_title(webpage)),
            'formats': formats,
            'thumbnail': (media_data.get('thumbnail')
                          or self._html_search_meta(['og:image', 'og:image:secure_url'], webpage)),
            'description': (media_data.get('description') or json_ld.get('description')
                            or self._html_search_meta(['description', 'og:description'], webpage)),
            'timestamp': unified_timestamp(media_data.get('publishedAt') or json_ld.get('timestamp')),
            'view_count': int_or_none(media_data.get('viewsCount') or json_ld.get('view_count')),
            'like_count': int_or_none(media_data.get('likesCount')),
            'uploader': traverse_obj(media_data, ('creator', 'firstName')),
            'uploader_id': traverse_obj(media_data, ('creator', ('uuid', 'nickname')), get_all=False),
            'categories': traverse_obj(media_data, ('categories', ..., 'name')) or None,
            'repost_count': int_or_none(media_data.get('sharingCount')),
        }


class YappyProfileIE(InfoExtractor):
    _VALID_URL = r'https?://yappy\.media/profile/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://yappy.media/profile/59a0c8c485e5410b9c43474bf4c6a373',
        'info_dict': {
            'id': '59a0c8c485e5410b9c43474bf4c6a373',
        },
        'playlist_mincount': 527,
    }]

    def _real_extract(self, url):
        profile_id = self._match_id(url)

        def fetch_page(page_num):
            page_num += 1
            videos = self._download_json(
                f'https://yappy.media/api/video/list/{profile_id}?page={page_num}',
                profile_id, f'Downloading profile page {page_num} JSON')

            for video in traverse_obj(videos, ('results', lambda _, v: v['uuid'])):
                yield self.url_result(
                    f'https://yappy.media/video/{video["uuid"]}', YappyIE,
                    video['uuid'], video.get('description'))

        return self.playlist_result(OnDemandPagedList(fetch_page, 15), profile_id)
