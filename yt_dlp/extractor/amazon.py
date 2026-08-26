import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    float_or_none,
    get_element_by_attribute,
    get_element_by_class,
    int_or_none,
    js_to_json,
    parse_duration,
    traverse_obj,
    url_or_none,
)


class AmazonStoreIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?amazon\.(?:[a-z]{2,3})(?:\.[a-z]{2})?/(?:[^/]+/)?(?:dp|gp/product)/(?P<id>[^/&#$?]+)'

    _TESTS = [{
        'url': 'https://www.amazon.co.uk/dp/B098XNCHLD/',
        'info_dict': {
            'id': 'B098XNCHLD',
            'title': str,
        },
        'playlist_mincount': 1,
        'playlist': [{
            'info_dict': {
                'id': 'A1F83G8C2ARO7P',
                'ext': 'mp4',
                'title': 'mcdodo usb c cable 100W 5a',
                'thumbnail': r're:^https?://.*\.jpg$',
                'duration': 34,
            },
        }],
        'expected_warnings': ['Unable to extract data'],
    }, {
        'url': 'https://www.amazon.in/Sony-WH-1000XM4-Cancelling-Headphones-Bluetooth/dp/B0863TXGM3',
        'info_dict': {
            'id': 'B0863TXGM3',
            'title': str,
        },
        'playlist_mincount': 4,
        'expected_warnings': ['Unable to extract data'],
    }, {
        'url': 'https://www.amazon.com/dp/B0845NXCXF/',
        'info_dict': {
            'id': 'B0845NXCXF',
            'title': str,
        },
        'playlist-mincount': 1,
        'expected_warnings': ['Unable to extract data'],
    }, {
        'url': 'https://www.amazon.es/Samsung-Smartphone-s-AMOLED-Quad-c%C3%A1mara-espa%C3%B1ola/dp/B08WX337PQ',
        'info_dict': {
            'id': 'B08WX337PQ',
            'title': str,
        },
        'playlist_mincount': 1,
        'expected_warnings': ['Unable to extract data'],
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        for retry in self.RetryManager():
            webpage = self._download_webpage(url, playlist_id)
            try:
                data_json = self._search_json(
                    r'var\s?obj\s?=\s?jQuery\.parseJSON\(\'', webpage, 'data', playlist_id,
                    transform_source=js_to_json)
            except ExtractorError as e:
                retry.error = e

        entries = [{
            'id': video['marketPlaceID'],
            'url': video['url'],
            'title': video.get('title'),
            'thumbnail': video.get('thumbUrl') or video.get('thumb'),
            'duration': video.get('durationSeconds'),
            'height': int_or_none(video.get('videoHeight')),
            'width': int_or_none(video.get('videoWidth')),
        } for video in (data_json.get('videos') or []) if video.get('isVideo') and video.get('url')]
        return self.playlist_result(entries, playlist_id=playlist_id, playlist_title=data_json.get('title'))


class AmazonReviewsIE(InfoExtractor):
    _VALID_URL = [
        r'https?://(?:www\.)?amazon\.(?:[a-z]{2,3})(?:\.[a-z]{2})?/gp/customer-reviews/(?P<id>[^/&#$?]+)',
        r'https?://(?:www\.)?amazon\.(?:[a-z]{2,3})(?:\.[a-z]{2})?/vdp/(?P<id>[0-9a-f]+)',
    ]
    _TESTS = [{
        'url': 'https://www.amazon.com/vdp/0358f63b34b749239d7c7203ff1be30b',
        'md5': '0cdc4e5308b5dc4bdcd8c459dcfc8719',
        'info_dict': {
            'id': 'R1A5ECPXAO8L5B',
            'ext': 'mp4',
            'title': 'Bright',
            'uploader': 'Ravel Franco',
            'duration': 29,
            'thumbnail': r're:^https?://.*\.(?:jpg|png)$',
        },
    }, {
        'url': 'https://www.amazon.com/gp/customer-reviews/R10VE9VUSY19L3/ref=cm_cr_arp_d_rvw_ttl',
        'skip': 'video gone',
        'info_dict': {
            'id': 'R10VE9VUSY19L3',
            'ext': 'mp4',
            'title': 'Get squad #Suspicious',
            'description': 'md5:7012695052f440a1e064e402d87e0afb',
            'uploader': 'Kimberly Cronkright',
            'average_rating': 1.0,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'expected_warnings': ['Review body was not found in webpage'],
    }, {
        'url': 'https://www.amazon.com/gp/customer-reviews/R10VE9VUSY19L3/ref=cm_cr_arp_d_rvw_ttl?language=es_US',
        'skip': 'video gone',
        'info_dict': {
            'id': 'R10VE9VUSY19L3',
            'ext': 'mp4',
            'title': 'Get squad #Suspicious',
            'description': 'md5:7012695052f440a1e064e402d87e0afb',
            'uploader': 'Kimberly Cronkright',
            'average_rating': 1.0,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'expected_warnings': ['Review body was not found in webpage'],
    }, {
        'url': 'https://www.amazon.in/gp/customer-reviews/RV1CO8JN5VGXV/',
        'skip': 'video gone',
        'info_dict': {
            'id': 'RV1CO8JN5VGXV',
            'ext': 'mp4',
            'title': 'Not sure about its durability',
            'description': 'md5:1a252c106357f0a3109ebf37d2e87494',
            'uploader': 'Shoaib Gulzar',
            'average_rating': 2.0,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'expected_warnings': ['Review body was not found in webpage'],
    }]

    def _extract_vse_formats(self, video_url, video_id, closed_captions=None):
        formats, subtitles = [], {}
        if url_or_none(video_url) and 'm3u8' in video_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                video_url, video_id, 'mp4', fatal=False)
        elif url_or_none(video_url):
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': 'http-mp4',
            })
        lang, _, cc_url = (closed_captions or '').partition(',')
        if url_or_none(cc_url):
            subtitles.setdefault(lang or 'en', []).append({
                'url': cc_url,
                'ext': 'vtt',
            })
        if not formats:
            self.raise_no_formats('No video found for this customer review', expected=True)
        return formats, subtitles

    def _extract_vdp(self, url, display_id):
        webpage = self._download_webpage(url, display_id)
        quoted = self._search_regex(
            r'liveFlagshipStates\["amazonlive-react-vse-metadata"\]\s*=\s*JSON\.parse\((".*?")\)\s*;',
            webpage, 'vse metadata')
        data = self._parse_json(self._parse_json(quoted, display_id), display_id)
        aci = data.get('aciContentId') or ''
        video_id = aci.split('.')[-1] if aci.startswith('amzn1.productreview.') else (
            data.get('id') or display_id)
        formats, subtitles = self._extract_vse_formats(
            data.get('url'), video_id, data.get('closedCaptions'))
        return {
            'id': video_id,
            'title': data.get('broadcastTitle'),
            'uploader': data.get('channelTitle'),
            'thumbnail': url_or_none(data.get('slateImageUrl')),
            'duration': parse_duration(data.get('formattedDuration')),
            'formats': formats,
            'subtitles': subtitles,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if '/vdp/' in url:
            return self._extract_vdp(url, video_id)

        for retry in self.RetryManager():
            webpage = self._download_webpage(url, video_id)
            if re.search(r'<title[^>]*>\s*Amazon Sign-In', webpage) or 'id="ap_email"' in webpage:
                self.raise_login_required(
                    'Amazon requires an account to view standalone customer review pages')
            review_body = get_element_by_attribute('data-hook', 'review-body', webpage)
            if not review_body:
                retry.error = ExtractorError('Review body was not found in webpage', expected=True)

        formats, subtitles = [], {}

        manifest_url = self._search_regex(
            r'data-video-url="([^"]+)"', review_body, 'm3u8 url', default=None)
        if url_or_none(manifest_url):
            fmts, subtitles = self._extract_m3u8_formats_and_subtitles(
                manifest_url, video_id, 'mp4', fatal=False)
            formats.extend(fmts)

        video_url = self._search_regex(
            r'<input[^>]+\bvalue="([^"]+)"[^>]+\bclass="video-url"', review_body, 'mp4 url', default=None)
        if url_or_none(video_url):
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': 'http-mp4',
            })

        if not formats:
            self.raise_no_formats('No video found for this customer review', expected=True)

        return {
            'id': video_id,
            'title': (clean_html(get_element_by_attribute('data-hook', 'review-title', webpage))
                      or self._html_extract_title(webpage)),
            'description': clean_html(traverse_obj(re.findall(
                r'<span(?:\s+class="cr-original-review-content")?>(.+?)</span>', review_body), -1)),
            'uploader': clean_html(get_element_by_class('a-profile-name', webpage)),
            'average_rating': float_or_none(clean_html(get_element_by_attribute(
                'data-hook', 'review-star-rating', webpage) or '').partition(' ')[0]),
            'thumbnail': self._search_regex(
                r'data-thumbnail-url="([^"]+)"', review_body, 'thumbnail', default=None),
            'formats': formats,
            'subtitles': subtitles,
        }
