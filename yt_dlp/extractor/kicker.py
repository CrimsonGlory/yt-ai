from .common import InfoExtractor
from .dailymotion import DailymotionIE
from ..utils import (
    int_or_none,
    unified_timestamp,
    url_or_none,
)


class KickerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kicker\.de/(?P<id>[\w-]+)/video'
    _TESTS = [{
        'url': 'https://www.kicker.de/wagner-ueber-pokal-torjaeger-johannesson-hatte-zu-kaempfen-1247261/video',
        'skip': 'HTTP 403/blocked',
        'md5': '9a92e6b5a973152a187e3bc610cffdcb',
        'info_dict': {
            'id': '1247261',
            'ext': 'mp4',
            'title': 'Wagner über Pokal-Torjäger Johannesson: "Hatte zu kämpfen"',
            'description': 'md5:300d108cdd568bab5c8f6d4788fe6b8d',
            'duration': 133,
            'thumbnail': r're:https://derivates\.kicker\.de/image/.+',
            'timestamp': 1787847372,
            'upload_date': '20260827',
        },
    }, {
        'url': 'https://www.kicker.de/pogba-dembel-co-die-top-11-der-abloesefreien-spieler-905049/video',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': 'km04mrK0DrRAVxy2GcA',
            'title': 'md5:b91d145bac5745ac58d5479d8347a875',
            'ext': 'mp4',
            'duration': 350,
            'description': 'md5:a5a3dd77dbb6550dbfb997be100b9998',
            'uploader_id': 'x2dfupo',
            'timestamp': 1654677626,
            'like_count': int,
            'uploader': 'kicker.de',
            'view_count': int,
            'age_limit': 0,
            'thumbnail': r're:https://s\d+\.dmcdn\.net/v/T-x741YeYAx8aSZ0Z/x1080',
            'tags': ['published', 'category.InternationalSoccer'],
            'upload_date': '20220608',
        },
    }, {
        'url': 'https://www.kicker.de/ex-unioner-in-der-bezirksliga-felix-kroos-vereinschallenge-in-pankow-902825/video',
        'skip': 'HTTP Error 403',
        'info_dict': {
            'id': 'k2omNsJKdZ3TxwxYSFJ',
            'title': 'md5:72ec24d7f84b8436fe1e89d198152adf',
            'ext': 'mp4',
            'uploader_id': 'x2dfupo',
            'duration': 331,
            'timestamp': 1652966015,
            'thumbnail': r're:https?://s\d+\.dmcdn\.net/v/TxU4Z1YYCmtisTbMq/x1080',
            'tags': ['FELIX KROOS', 'EINFACH MAL LUPPEN', 'KROOS', 'FSV FORTUNA PANKOW', 'published', 'category.Amateurs', 'marketingpreset.Spreekick'],
            'age_limit': 0,
            'view_count': int,
            'upload_date': '20220519',
            'uploader': 'kicker.de',
            'description': 'md5:0c2060c899a91c8bf40f578f78c5846f',
            'like_count': int,
        },
    }]
    _RSS_NS = {'media': 'http://search.yahoo.com/mrss/'}
    _FEEDS = (
        'https://newsfeed.kicker.de/firetvchannel/news',
        'https://newsfeed.kicker.de/firetvchannel/kickerformate',
        'https://newsfeed.kicker.de/firetvchannel/esport',
    )

    def _extract_from_rss(self, article_id):
        needle = f'-{article_id}/video'
        for feed_url in self._FEEDS:
            feed = self._download_xml(
                feed_url, article_id, fatal=False,
                note=f'Downloading RSS feed {feed_url.rsplit("/", 1)[-1]}')
            if feed is None:
                continue
            for item in feed.findall('./channel/item'):
                if needle not in (item.findtext('link') or ''):
                    continue
                media = item.find('media:content', self._RSS_NS)
                video_url = url_or_none(media.get('url') if media is not None else None)
                if not video_url:
                    continue
                thumbnail = item.find('media:thumbnail', self._RSS_NS)
                return {
                    'id': article_id,
                    'url': video_url,
                    'title': item.findtext('title'),
                    'description': item.findtext('media:description', namespaces=self._RSS_NS),
                    'duration': int_or_none(media.get('duration')),
                    'thumbnail': url_or_none(
                        thumbnail.get('url') if thumbnail is not None else None),
                    'timestamp': unified_timestamp(item.findtext('pubDate')),
                }
        return None

    def _real_extract(self, url):
        video_slug = self._match_id(url)
        article_id = self._search_regex(
            r'(\d+)$', video_slug, 'article id', default=video_slug)

        rss_info = self._extract_from_rss(article_id)
        if rss_info:
            return rss_info

        webpage = self._download_webpage(url, video_slug)
        dailymotion_video_id = self._search_regex(
            r'data-dmprivateid\s*=\s*[\'"](?P<video_id>\w+)', webpage,
            'video id', group='video_id')

        return self.url_result(
            f'https://www.dailymotion.com/video/{dailymotion_video_id}',
            ie=DailymotionIE, video_title=self._html_extract_title(webpage))
