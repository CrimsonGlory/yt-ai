import base64
import hashlib
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    determine_ext,
    extract_attributes,
    int_or_none,
    parse_resolution,
    traverse_obj,
    url_or_none,
    urlencode_postdata,
    urljoin,
)


class RezkaIE(InfoExtractor):
    IE_NAME = 'rezka'
    IE_DESC = 'HDrezka'
    _VALID_URL = r'https?://(?:www\.)?rezka\.ag/(?:films|series|cartoons|animation)/[^/?#]+/(?P<id>\d+)(?:-[^/?#]+)?(?:/(?P<translator>[^/?#]+))?'
    _STREAM_SALTS = (
        'IyMjI14hISMjIUBA',
        'QEBAQEAhIyMhXl5e',
        'JCQhIUAkJEBeIUAjJCRA',
        'JCQjISFAIyFAIyM=',
        'Xl5eIUAjIyEhIyM=',
    )
    _TESTS = [{
        'url': 'https://rezka.ag/films/melodrama/89607-karolina-kerolayn-2025-latest/238-subtitles.html',
        'md5': '9f0eb85e6a9683bd79d459ef02610595',
        'info_dict': {
            'id': '89607',
            'ext': 'mp4',
            'title': 'Каролина Кэролайн (2025)',
            'alt_title': 'Carolina Caroline (2025)',
            'description': 'md5:bc5a4f54fe01865bdcdcf13e76a55f92',
            'thumbnail': r're:https?://.+\.(?:jpg|jpeg|png)',
            'duration': 6300,
            'subtitles': {
                'ru': 'count:1',
                'en': 'count:1',
            },
        },
        'params': {
            'format': 'best[protocol=https]',
        },
    }, {
        'url': 'https://rezka.ag/films/melodrama/89607-karolina-kerolayn-2025-latest.html',
        'only_matching': True,
    }, {
        'url': 'https://rezka.ag/films/melodrama/89607-karolina-kerolayn-2025-latest/mimrcghb-subtitles.html',
        'only_matching': True,
    }, {
        'url': 'https://rezka.ag/series/documentary/92155-mif-shalke-na-vsyu-zhizn-2026.html',
        'only_matching': True,
    }]

    def _solve_anubis_pow(self, random_data, difficulty):
        prefix = '0' * (int_or_none(difficulty) or 0)
        for nonce in range(5_000_000):
            digest = hashlib.sha256(f'{random_data}{nonce}'.encode()).hexdigest()
            if digest.startswith(prefix):
                return nonce, digest
        raise ExtractorError('Unable to solve Anubis proof-of-work challenge', expected=True)

    def _download_rezka_webpage(self, url, video_id):
        webpage = self._download_webpage(url, video_id)
        challenge = traverse_obj(self._search_json(
            r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
            webpage, 'anubis challenge', video_id, default=None), 'challenge')
        if not challenge:
            return webpage

        random_data = challenge.get('randomData')
        challenge_id = challenge.get('id')
        method = challenge.get('method') or 'fast'
        if method != 'fast':
            raise ExtractorError(
                f'Unsupported Anubis challenge method {method!r}', expected=True)
        if not random_data or not challenge_id:
            raise ExtractorError('Unable to parse Anubis challenge', expected=True)

        nonce, response = self._solve_anubis_pow(
            random_data, challenge.get('difficulty'))
        webpage = self._download_webpage(
            urljoin(url, '/.within.website/x/cmd/anubis/api/pass-challenge'),
            video_id, 'Solving Anubis challenge', query={
                'id': challenge_id,
                'response': response,
                'nonce': str(nonce),
                'redir': url,
                'elapsedTime': '1',
            })
        if self._search_json(
                r'<script[^>]+id=["\']anubis_challenge["\'][^>]*>',
                webpage, 'anubis challenge', video_id, default=None):
            raise ExtractorError('Anubis challenge was not accepted', expected=True)
        if 'initCDN' not in webpage:
            webpage = self._download_webpage(
                url, video_id, 'Downloading webpage after Anubis')
        return webpage

    def _decode_stream_urls(self, data):
        if not data or not isinstance(data, str):
            return data
        if data.startswith(('[', 'http')):
            return data
        data = data.replace('#h', '')
        for _ in range(60):
            idx = data.find('//_//')
            if idx < 0:
                break
            after = data[idx + 5:]
            salt = next((s for s in self._STREAM_SALTS if after.startswith(s)), None)
            data = data[:idx] + after[len(salt) if salt else 16:]
        try:
            return base64.b64decode(data + '===').decode()
        except (ValueError, UnicodeDecodeError):
            return data

    def _parse_translators(self, webpage):
        translators = []
        for tag in re.findall(r'<a[^>]+data-translator_id="\d+"[^>]*>', webpage):
            attrs = extract_attributes(tag)
            classes = (attrs.get('class') or '').split()
            if 'b-translator__item' not in classes:
                continue
            translator_id = attrs.get('data-translator_id')
            if not translator_id:
                continue
            translators.append({
                'id': translator_id,
                'title': attrs.get('title'),
                'premium': 'b-prem_translator' in classes,
                'active': 'active' in classes,
                'camrip': attrs.get('data-camrip') or '0',
                'ads': attrs.get('data-ads') or '0',
                'director': attrs.get('data-director') or '0',
            })
        return translators

    def _select_translator(self, translators, url_translator):
        requested = (self._configuration_arg('translator') or [None])[0]
        if requested:
            want = requested.casefold()
            match = next((
                t for t in translators
                if t['id'] == requested or want in (t.get('title') or '').casefold()), None)
            if match:
                return match
            raise ExtractorError(f'Requested translator {requested!r} was not found', expected=True)

        if url_translator and url_translator.isdigit():
            match = next((t for t in translators if t['id'] == url_translator), None)
            if match:
                return match

        active = next((t for t in translators if t.get('active')), None)
        if active and not active.get('premium'):
            return active
        free = next((t for t in translators if not t.get('premium')), None)
        if free:
            if active and active.get('premium'):
                self.to_screen(
                    f'Default translation requires Premium; using {free.get("title") or free["id"]}')
            return free
        return active

    def _call_cdn(self, url, video_id, form, note='Downloading stream JSON'):
        return self._download_json(
            urljoin(url, '/ajax/get_cdn_series/'), video_id, note,
            data=urlencode_postdata(form), headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest',
            })

    def _parse_subtitles(self, subtitle, subtitle_lns=None):
        subtitles = {}
        if not subtitle or not isinstance(subtitle, str):
            return subtitles
        lns = subtitle_lns if isinstance(subtitle_lns, dict) else {}
        for mobj in re.finditer(r'\[(?P<lang>[^\]]+)\](?P<urls>https?://[^[]+)', subtitle):
            lang = lns.get(mobj.group('lang')) or mobj.group('lang')
            sub_url = mobj.group('urls').strip().rstrip(',')
            if ' or ' in sub_url:
                sub_url = sub_url.split(' or ')[-1].strip()
            if url_or_none(sub_url):
                subtitles.setdefault(lang, []).append({
                    'url': sub_url,
                    'ext': determine_ext(sub_url, 'vtt'),
                })
        return subtitles

    def _extract_formats(self, stream, video_id):
        formats, skipped_premium = [], False
        stream = self._decode_stream_urls(stream)
        if not stream:
            return formats, skipped_premium
        for raw_label, urls in re.findall(r'\[(.*?)\]([^[]+)', stream):
            if 'prem-quality' in raw_label or 'prem-icon' in raw_label:
                skipped_premium = True
                continue
            label = clean_html(raw_label) or raw_label
            height = parse_resolution(label).get('height')
            if not height and re.match(r'2[kK]\b', label):
                height = 1440
            for media_url in re.split(r'\s+or\s+', urls.strip().rstrip(',')):
                media_url = media_url.strip()
                if not url_or_none(media_url):
                    continue
                if media_url.endswith(':hls:manifest.m3u8') or determine_ext(media_url) == 'm3u8':
                    fmts, _ = self._extract_m3u8_formats_and_subtitles(
                        media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                    for fmt in fmts:
                        fmt.setdefault('height', height)
                    formats.extend(fmts)
                else:
                    formats.append({
                        'url': media_url,
                        'format_id': f'http-{label}',
                        'ext': 'mp4',
                        'height': height,
                    })
        return formats, skipped_premium

    def _real_extract(self, url):
        video_id, url_translator = self._match_valid_url(url).group('id', 'translator')
        if url_translator:
            url_translator = url_translator.removesuffix('.html')
            if '-' in url_translator and url_translator.split('-', 1)[0].isdigit():
                url_translator = url_translator.split('-', 1)[0]

        webpage = self._download_rezka_webpage(url, video_id)
        kind, post_id, page_translator, arg3, arg4 = self._search_regex(
            r'sof\.tv\.initCDN(Movies|Series)Events\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)',
            webpage, 'player init', group=(1, 2, 3, 4, 5))
        is_series = kind == 'Series'
        season = int_or_none((self._configuration_arg('season') or [None])[0])
        episode = int_or_none((self._configuration_arg('episode') or [None])[0])
        if is_series:
            season = season or int_or_none(arg3)
            episode = episode or int_or_none(arg4)

        player = self._search_json(
            r'sof\.tv\.initCDN(?:Movies|Series)Events\((?:[^,]+,){8}',
            webpage, 'player', video_id, default=None) or {}
        translators = self._parse_translators(webpage)
        selected = self._select_translator(translators, url_translator) or {
            'id': page_translator,
            'premium': False,
            'camrip': arg3 if not is_series else '0',
            'ads': arg4 if not is_series else '0',
            'director': '0',
        }

        if selected.get('premium') and not any(not t.get('premium') for t in translators):
            self.raise_login_required(
                'This video is only available with an HDrezka Premium account',
                metadata_available=True)

        need_ajax = (
            selected['id'] != page_translator
            or (is_series and (
                season != int_or_none(arg3) or episode != int_or_none(arg4))))
        stream, subtitle, subtitle_lns = (
            player.get('streams'), player.get('subtitle'), player.get('subtitle_lns'))
        if need_ajax:
            favs = self._html_search_regex(
                r'<input[^>]+id=["\']ctrl_favs["\'][^>]*value=["\']([^"\']+)',
                webpage, 'favs', default=None)
            if is_series:
                form = {
                    'id': post_id,
                    'translator_id': selected['id'],
                    'season': season,
                    'episode': episode,
                    'action': 'get_stream',
                }
            else:
                form = {
                    'id': post_id,
                    'translator_id': selected['id'],
                    'is_camrip': selected.get('camrip') or '0',
                    'is_ads': selected.get('ads') or '0',
                    'is_director': selected.get('director') or '0',
                    'action': 'get_movie',
                }
            if favs:
                form['favs'] = favs
            cdn = self._call_cdn(url, video_id, form) or {}
            if not cdn.get('success') and not cdn.get('url'):
                raise ExtractorError(
                    cdn.get('message') or 'Failed to load stream', expected=True)
            if cdn.get('premium_content') and not cdn.get('url'):
                self.raise_login_required(
                    'This translation is only available with an HDrezka Premium account',
                    metadata_available=True)
            stream = cdn.get('url') or stream
            subtitle = cdn.get('subtitle') if cdn.get('subtitle') is not False else subtitle
            subtitle_lns = cdn.get('subtitle_lns') or subtitle_lns

        formats, skipped_premium = self._extract_formats(stream, video_id)
        if not formats:
            if skipped_premium or selected.get('premium'):
                self.raise_login_required(
                    'Only Premium qualities are available for this video',
                    metadata_available=True)
            raise ExtractorError('No video formats found', expected=True)

        display_id = video_id
        if is_series and season and episode:
            display_id = f'{video_id}_s{season}e{episode}'

        orig_title = self._html_search_regex(
            r'class="b-post__origtitle"[^>]*>([^<]+)', webpage, 'original title', default=None)
        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'<h1[^>]*>([^<]+)', webpage, 'title', default=None))

        return {
            'id': display_id,
            'title': title,
            'alt_title': orig_title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': int_or_none(self._og_search_property(
                'duration', webpage, default=None)),
            'season_number': season if is_series else None,
            'episode_number': episode if is_series else None,
            'formats': formats,
            'subtitles': self._parse_subtitles(subtitle, subtitle_lns),
        }
