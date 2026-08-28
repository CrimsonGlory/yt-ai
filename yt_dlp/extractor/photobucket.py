import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class PhotobucketIE(InfoExtractor):
    _VALID_URL = (
        r'https?://(?:www\.)?photobucket\.com/share/(?P<id>[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})(?:/(?P<media_id>[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}))?',
        r'https?://(?:[a-z0-9]+\.)?photobucket\.com/.*(?:[?&]current=|_)(?P<id>[^/?&]+)\.(?P<ext>flv|mp4)',
    )
    _TESTS = [
        {
            'url': 'https://photobucket.com/share/a83b8738-3b23-4275-bcd3-46d86a78a546',
            'md5': '8e308ae7220db3d15c00e0ec8efe1665',
            'info_dict': {
                'id': '3c879b67-fc04-4976-8138-bcbe9e9b1b10',
                'ext': 'mp4',
                'title': 'UFO, or bird?',
                'thumbnail': 'https://hosting.photobucket.com/f7d3ced3-9e1c-4238-83b7-8b1f40f67e99/3c879b67-fc04-4976-8138-bcbe9e9b1b10.mp4',
                'timestamp': 1775790768,
                'upload_date': '20260410',
                'filesize': 1334154,
                'width': 854,
                'height': 218,
            },
        },
        {
            'url': 'https://photobucket.com/share/a83b8738-3b23-4275-bcd3-46d86a78a546/3c879b67-fc04-4976-8138-bcbe9e9b1b10',
            'only_matching': True,
        },
        {
            'url': 'http://media.photobucket.com/user/rachaneronas/media/TiredofLinkBuildingTryBacklinkMyDomaincom_zpsc0c3b9fa.mp4.html?filters[term]=search&filters[primary]=videos&filters[secondary]=images&sort=1&o=0',
            'skip': 'video gone',
            'md5': '7dabfb92b0a31f6c16cebc0f8e60ff99',
            'info_dict': {
                'id': 'zpsc0c3b9fa',
                'ext': 'mp4',
                'timestamp': 1367669341,
                'upload_date': '20130504',
                'uploader': 'rachaneronas',
                'title': 'Tired of Link Building? Try BacklinkMyDomain.com!',
            },
        },
    ]
    _GRAPHQL_URL = 'https://photobucket.com/api/graphql/v2'
    _SHARE_QUERY = '''query BucketShareById($shareId: ID!) {
        bucketShareById(shareId: $shareId) {
            id
            title
            shareStatus
            passwordProtected
        }
    }'''
    _MEDIA_QUERY = '''query BucketMediaByShareId($shareId: ID!, $nextToken: String) {
        bucketMediaByShareId(shareId: $shareId, nextToken: $nextToken) {
            nextToken
            items {
                id
                filename
                originalFilename
                isVideo
                mediaType
                title
                signedUrl
                imageUrl
                fileSize
                createdAt
                width
                height
            }
        }
    }'''

    def _call_graphql(self, query, variables, video_id, note):
        return self._download_json(
            self._GRAPHQL_URL,
            video_id,
            note=note,
            data=json.dumps({'query': query, 'variables': variables}).encode(),
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://photobucket.com',
                'Referer': 'https://photobucket.com/',
            },
        )

    def _fetch_share_media(self, share_id):
        items, next_token = [], None
        for page in range(1, 51):
            data = self._call_graphql(
                self._MEDIA_QUERY,
                {'shareId': share_id, 'nextToken': next_token},
                share_id,
                f'Downloading share media JSON page {page}',
            )
            page_data = traverse_obj(data, ('data', 'bucketMediaByShareId', {dict})) or {}
            items.extend(traverse_obj(page_data, ('items', ..., {dict})))
            next_token = page_data.get('nextToken')
            if not next_token:
                break
        return items

    def _parse_video(self, item, title=None):
        video_id = item['id']
        video_url = url_or_none(item.get('signedUrl'))
        if not video_url:
            self.raise_no_formats('No download URL', expected=True, video_id=video_id)
        return {
            'id': video_id,
            'url': video_url,
            'title': title or item.get('title') or video_id,
            'ext': determine_ext(item.get('filename') or video_url, 'mp4'),
            'thumbnail': url_or_none(item.get('imageUrl')),
            'filesize': int_or_none(item.get('fileSize')),
            'timestamp': unified_timestamp(item.get('createdAt')),
            'width': int_or_none(item.get('width')),
            'height': int_or_none(item.get('height')),
        }

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        media_id = mobj.groupdict().get('media_id')
        if '/share/' not in url:
            raise ExtractorError(
                'Photobucket no longer hosts public media pages. Use a sharing link (https://photobucket.com/share/...).',
                expected=True,
            )

        share_data = self._call_graphql(self._SHARE_QUERY, {'shareId': video_id}, video_id, 'Downloading share JSON')
        error = traverse_obj(share_data, ('errors', 0, 'message', {str}))
        share = traverse_obj(share_data, ('data', 'bucketShareById', {dict}))
        if not share:
            raise ExtractorError(error or 'The requested share does not exist or has been deleted', expected=True)
        if share.get('passwordProtected'):
            raise ExtractorError('This Photobucket share is password protected', expected=True)

        videos = [
            item
            for item in self._fetch_share_media(video_id)
            if item.get('id') and (item.get('isVideo') or (item.get('mediaType') or '').startswith('video/'))
        ]
        if media_id:
            videos = [item for item in videos if item['id'] == media_id]
        if not videos:
            raise ExtractorError('No video found for this Photobucket share', expected=True)
        if len(videos) > 1:
            return self.playlist_result(
                (
                    self.url_result(
                        f"https://photobucket.com/share/{video_id}/{item['id']}",
                        PhotobucketIE,
                        item['id'],
                        item.get('title'),
                    )
                    for item in videos
                ),
                video_id,
                share.get('title'),
            )

        return self._parse_video(videos[0], share.get('title'))
