from .amp import AMPIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    traverse_obj,
    url_or_none,
)


class BleacherReportIE(InfoExtractor):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?bleacherreport\.com/articles/(?P<id>\d+)'
    _EMBED_IES = {
        'youtube': 'Youtube',
        'twitter': 'Twitter',
        'vine': 'Vine',
    }
    _TESTS = [{
        'url': 'http://bleacherreport.com/articles/2496438-fsu-stat-projections-is-jalen-ramsey-best-defensive-player-in-college-football',
        'md5': 'a3ffc3dc73afdbc2010f02d98f990f20',
        'info_dict': {
            'id': '2496438',
            'ext': 'mp4',
            'title': 'FSU Stat Projections: Is Jalen Ramsey Best Defensive Player in College Football?',
            'uploader_id': '3992341',
            'description': 'CFB, ACC, Florida State',
            'timestamp': 1434380212,
            'upload_date': '20150615',
            'uploader': 'Team Stream Now ',
        },
        'skip': 'Video removed',
    }, {
        'url': 'http://bleacherreport.com/articles/2586817-aussie-golfers-get-fright-of-their-lives-after-being-chased-by-angry-kangaroo',
        'skip': 'Old article API is gone',
        'md5': '6a5cd403418c7b01719248ca97fb0692',
        'info_dict': {
            'id': '2586817',
            'ext': 'webm',
            'title': 'Aussie Golfers Get Fright of Their Lives After Being Chased by Angry Kangaroo',
            'timestamp': 1446839961,
            'uploader': 'Sean Fay',
            'description': 'md5:b1601e2314c4d8eec23b6eafe086a757',
            'uploader_id': '6466954',
            'upload_date': '20151011',
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'https://bleacherreport.com/articles/25484400-nhl-27-drops-gameplay-and-presentation-deep-dive-video-detailing-video-games-new-features',
        'md5': 'aafed707585121d59eab0e0ba34a3cf6',
        'info_dict': {
            'id': 'OCIx-zOwCBc',
            'ext': 'mp4',
            'title': 'NHL 27 Drops Gameplay and Presentation Deep Dive Video Detailing Video Game\'s New Features',
            'description': 'EA Sports released a new deep-dive video showcasing NHL 27\'s gameplay and presentation on Tuesday.',
            'thumbnail': 'https://gsp-image-cdn.wmsports.io/cms/prod/bleacher-report/getty_images/2026-08/1458013182_large_cropped.jpg',
            'duration': 345,
            'timestamp': 1787674750,
            'upload_date': '20260825',
            'release_timestamp': 1787669706,
            'release_date': '20260825',
            'uploader': 'Zach Bachar',
            'uploader_id': '@easportsnhl',
            'uploader_url': 'https://www.youtube.com/@easportsnhl',
            'channel': 'EA SPORTS NHL',
            'channel_id': 'UCLydKeNR8rf-yoUu9J2acMg',
            'channel_url': 'https://www.youtube.com/channel/UCLydKeNR8rf-yoUu9J2acMg',
            'channel_follower_count': int,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'age_limit': 0,
            'categories': ['Gaming'],
            'tags': 'count:19',
            'creators': ['EA SPORTS NHL', 'NHL'],
            'chapters': [{
                'start_time': 0,
                'title': 'Introduction',
                'end_time': 19,
            }, {
                'start_time': 19,
                'title': 'Team-Specific Playbooks & Smarter Teammate AI',
                'end_time': 117,
            }, {
                'start_time': 117,
                'title': 'Community-Requested Gameplay Updates',
                'end_time': 133,
            }, {
                'start_time': 133,
                'title': 'New Commentary & Broadcast Presentation',
                'end_time': 236,
            }, {
                'start_time': 236,
                'title': 'Authentic Arenas, Goal Songs & Crowd Atmosphere',
                'end_time': 345,
            }],
            'playable_in_embed': True,
            'availability': 'public',
            'live_status': 'not_live',
            'media_type': 'video',
        },
        'add_ie': ['Youtube'],
    }]

    def _resolve_nextjs(self, obj, table, _seen=frozenset()):
        if isinstance(obj, str) and obj.startswith('$'):
            key = obj[1:]
            if key in table and key not in _seen:
                return self._resolve_nextjs(table[key], table, _seen | {key})
            return obj
        if isinstance(obj, dict):
            return {k: self._resolve_nextjs(v, table, _seen) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._resolve_nextjs(v, table, _seen) for v in obj]
        return obj

    def _extract_embed(self, article_id, article):
        elements = []
        for path in (
            ('featuredMedia',),
            ('slides', ..., 'featuredMedia'),
            ('slides', ..., 'elements', ...),
        ):
            found = traverse_obj(article, path)
            if isinstance(found, list):
                elements.extend(found)
            elif found:
                elements.append(found)

        for element in elements:
            content_type = traverse_obj(element, 'contentType')
            content = traverse_obj(element, 'content') or {}
            embed_url = url_or_none(content.get('url'))
            ie_key = self._EMBED_IES.get(content_type)
            if not ie_key or not embed_url:
                continue
            if content_type == 'youtube':
                yt_id = self._search_regex(
                    r'(?:embed/|watch\?v=|youtu\.be/)([0-9A-Za-z_-]{11})',
                    embed_url, 'youtube id', default=None)
                if yt_id:
                    embed_url = f'https://www.youtube.com/watch?v={yt_id}'
            return {
                '_type': 'url_transparent',
                'url': embed_url,
                'ie_key': ie_key,
                'id': article_id,
                'title': article.get('title'),
                'description': article.get('alternateDescription') or article.get('description') or None,
                'uploader': traverse_obj(article, ('author', 'name')),
                'timestamp': parse_iso8601(article.get('publishedDateTime') or article.get('createdAt')),
                'thumbnail': traverse_obj(article, ('image', 'url'), expected_type=url_or_none),
            }
        return None

    def _real_extract(self, url):
        article_id = self._match_id(url)
        webpage = self._download_webpage(url, article_id)
        nextjs_data = self._search_nextjs_v13_data(webpage, article_id, fatal=False)

        article = None
        for value in nextjs_data.values():
            candidate = value.get('data') if isinstance(value, dict) else None
            if not isinstance(candidate, dict):
                candidate = value if isinstance(value, dict) else None
            if not isinstance(candidate, dict) or candidate.get('__typename') != 'Article':
                continue
            if str(candidate.get('displayId')) != article_id:
                continue
            article = self._resolve_nextjs(candidate, nextjs_data)
            break

        if article:
            info = self._extract_embed(article_id, article)
            if info:
                return info

        raise ExtractorError('no video in the article', expected=True)


class BleacherReportCMSIE(AMPIE):
    _WEB_FALLBACK = True
    _VALID_URL = r'https?://(?:www\.)?bleacherreport\.com/video_embed\?id=(?P<id>[0-9a-f-]{36}|\d{5})'
    _TESTS = [{
        'url': 'http://bleacherreport.com/video_embed?id=8fd44c2f-3dc5-4821-9118-2c825a98c0e1&library=video-cms',
        'skip': 'vid.bleacherreport.com Akamai feed is gone',
        'md5': '670b2d73f48549da032861130488c681',
        'info_dict': {
            'id': '8fd44c2f-3dc5-4821-9118-2c825a98c0e1',
            'ext': 'mp4',
            'title': 'Cena vs. Rollins Would Expose the Heavyweight Division',
            'description': 'md5:984afb4ade2f9c0db35f3267ed88b36e',
            'upload_date': '20150723',
            'timestamp': 1437679032,

        },
        'expected_warnings': [
            'Unable to download f4m manifest',
        ],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._extract_feed_info(f'http://vid.bleacherreport.com/videos/{video_id}.akamai')
        info['id'] = video_id
        return info
