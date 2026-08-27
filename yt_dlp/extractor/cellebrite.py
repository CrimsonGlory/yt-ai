from .vidyard import VidyardBaseIE, VidyardIE
from ..utils import ExtractorError, make_archive_id, url_basename


class CellebriteIE(VidyardBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cellebrite\.com/(?:[a-z]{2}/)?(?:[\w-]+/)*(?P<id>[\w-]+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://cellebrite.com/en/resources/webinars/the-ai-advantage-evidence-review/',
        'info_dict': {
            'id': 'msZ1hLy22NtktreiJZqp1Z',
            'display_id': '47603526',
            'ext': 'mp4',
            'title': 'Webinar: The AI Advantage - Evidence Review',
            'description': 'md5:e1b209e036d12adf3dc1e0e5bc408ee7',
            'thumbnail': r're:https?://.+\.(?:jpg|png)',
            'duration': 3732.67,
            '_old_archive_ids': ['cellebrite 47603526'],
        },
    }, {
        'url': 'https://cellebrite.com/en/how-to-lawfully-collect-the-maximum-amount-of-data-from-android-devices/',
        'skip': 'video gone',
        'info_dict': {
            'id': 'QV1U8a2yzcxigw7VFnqKyg',
            'display_id': '29018255',
            'ext': 'mp4',
            'title': 'How to Lawfully Collect the Maximum Amount of Data From Android Devices',
            'description': 'md5:0e943a9ac14c374d5d74faed634d773c',
            'thumbnail': 'https://cellebrite.com/wp-content/uploads/2022/07/How-to-Lawfully-Collect-the-Maximum-Amount-of-Data-From-Android-Devices.png',
            'duration': 134.315,
            '_old_archive_ids': ['cellebrite 29018255'],
        },
    }]

    def _real_extract(self, url):
        slug = self._match_id(url)
        webpage = self._download_webpage(url, slug, impersonate=True)
        vidyard_url = next(VidyardIE._extract_embed_urls(url, webpage), None)
        if not vidyard_url:
            raise ExtractorError('No Vidyard video embeds found on page')

        video_id = url_basename(vidyard_url)
        info = self._process_video_json(self._fetch_video_json(video_id)['chapters'][0], video_id)
        if info.get('display_id'):
            info['_old_archive_ids'] = [make_archive_id(self, info['display_id'])]
        if thumbnail := self._og_search_thumbnail(webpage, default=None):
            info.setdefault('thumbnails', []).append({'url': thumbnail})

        return {
            'description': self._og_search_description(webpage, default=None),
            **info,
        }
