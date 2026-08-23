import re

from .common import InfoExtractor


class CloserToTruthIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?closertotruth\.com/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://closertotruth.com/series/solutions-the-mind-body-problem#video-3688',
        'info_dict': {
            'id': '0_zof1ktre',
            'display_id': 'solutions-the-mind-body-problem',
            'ext': 'mov',
            'title': 'Solutions to the Mind-Body Problem?',
            'upload_date': '20140221',
            'timestamp': 1392956007,
            'uploader_id': 'CTTXML',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://closertotruth.com/episodes/how-do-brains-work',
        'info_dict': {
            'id': '0_iuxai6g6',
            'display_id': 'how-do-brains-work',
            'ext': 'mov',
            'title': 'How do Brains Work?',
            'upload_date': '20140221',
            'timestamp': 1392956024,
            'uploader_id': 'CTTXML',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://closertotruth.com/interviews/1725',
        'info_dict': {
            'id': '1725',
            'title': 'AyaFr-002',
        },
        'playlist_mincount': 2,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        title = self._html_extract_title(webpage, 'video title')

        youtube_urls = re.findall(
            r'(?:data-video(?:-id)?|video_url)\s*=\s*["\'](https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)',
            webpage)
        youtube_urls.extend(re.findall(
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+', webpage))
        # Preserve order while unique-ing
        seen = set()
        yt_entries = []
        for yt_url in youtube_urls:
            if yt_url in seen:
                continue
            seen.add(yt_url)
            yt_entries.append(self.url_result(yt_url, 'Youtube'))
        if yt_entries:
            if len(yt_entries) == 1:
                return {
                    '_type': 'url_transparent',
                    'display_id': display_id,
                    'url': yt_entries[0]['url'],
                    'ie_key': 'Youtube',
                    'title': title,
                }
            return self.playlist_result(yt_entries, display_id, title)

        partner_id = self._search_regex(
            r'<script[^>]+src=["\'].*?\b(?:partner_id|p)/(\d+)',
            webpage, 'kaltura partner_id')

        select = self._search_regex(
            r'(?s)<select[^>]+id="select-version"[^>]*>(.+?)</select>',
            webpage, 'select version', default=None)
        if select:
            entry_ids = set()
            entries = []
            for mobj in re.finditer(
                    r'<option[^>]+value=(["\'])(?P<id>[0-9a-z_]+)(?:#.+?)?\1[^>]*>(?P<title>[^<]+)',
                    webpage):
                entry_id = mobj.group('id')
                if entry_id in entry_ids:
                    continue
                entry_ids.add(entry_id)
                entries.append({
                    '_type': 'url_transparent',
                    'url': f'kaltura:{partner_id}:{entry_id}',
                    'ie_key': 'Kaltura',
                    'title': mobj.group('title'),
                })
            if entries:
                return self.playlist_result(entries, display_id, title)

        entry_id = self._search_regex(
            r'<a[^>]+id=(["\'])embed-kaltura\1[^>]+data-kaltura=(["\'])(?P<id>[0-9a-z_]+)\2',
            webpage, 'kaltura entry_id', group='id')

        return {
            '_type': 'url_transparent',
            'display_id': display_id,
            'url': f'kaltura:{partner_id}:{entry_id}',
            'ie_key': 'Kaltura',
            'title': title,
        }
