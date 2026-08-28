from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    qualities,
    update_url_query,
    urljoin,
)


class PlaytvakIE(InfoExtractor):
    _WEB_FALLBACK = True
    IE_DESC = 'Playtvak.cz, iDNES.cz, Lidovky.cz and iDNES.tv'
    _VALID_URL = [
        r'https?://(?:.+?\.)?(?:playtvak|idnes|lidovky|metro)\.cz/.*\?(?:c|idvideo)=(?P<id>[^&]+)',
        r'https?://(?:tv|kino)\.idnes\.cz/(?:[^/?#]+/)*[^/?#]*\.(?P<id>[AV]\d{6}_\d{6}_[^/?#]+)',
    ]
    _TESTS = [{
        'url': 'http://www.playtvak.cz/embed.aspx?idvideo=V150729_141549_play-porad_kuko',
        'md5': 'b50218b8b60ee658b35cb3642bab27fe',
        'info_dict': {
            'id': 'V150729_141549_play-porad_kuko',
            'ext': 'mp4',
            'title': 'Co jste nevěděli o komunistických seriálech',
            'thumbnail': r're:(?i)^https?://.*\.(?:jpg|png)$',
            'duration': 483,
            'timestamp': 1438214460,
            'upload_date': '20150730',
            'is_live': False,
        },
    }, {
        'url': 'https://tv.idnes.cz/zahranicni/povoden-vlna-nepal-reka-lide-obeti-mesto-domy-voda.V260827_092718_idnestv_pech',
        'only_matching': True,
    }, {
        'url': 'http://www.playtvak.cz/vyzente-vosy-a-srsne-ze-zahrady-dn5-/hodinovy-manzel.aspx?c=A150730_150323_hodinovy-manzel_kuko',
        'skip': 'video gone',
        'md5': '4525ae312c324b4be2f4603cc78ceb4a',
        'info_dict': {
            'id': 'A150730_150323_hodinovy-manzel_kuko',
            'ext': 'mp4',
            'title': 'Vyžeňte vosy a sršně ze zahrady',
            'description': 'md5:4436e61b7df227a093778efb7e373571',
            'thumbnail': r're:(?i)^https?://.*\.(?:jpg|png)$',
            'duration': 279,
            'timestamp': 1438732860,
            'upload_date': '20150805',
            'is_live': False,
        },
    }, {  # live video test
        'url': 'http://slowtv.playtvak.cz/planespotting-0pr-/planespotting.aspx?c=A150624_164934_planespotting_cat',
        'skip': 'Site no longer exists or is broken',
        'info_dict': {
            'id': 'A150624_164934_planespotting_cat',
            'ext': 'flv',
            'title': 're:^Planespotting [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'Sledujte provoz na ranveji Letiště Václava Havla v Praze',
            'is_live': True,
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
    }, {  # another live stream, this one without Misc.videoFLV
        'url': 'https://slowtv.playtvak.cz/zive-sledujte-vlaky-v-primem-prenosu-dwi-/hlavni-nadrazi.aspx?c=A151218_145728_hlavni-nadrazi_plap',
        'skip': 'Site no longer exists or is broken',
        'info_dict': {
            'id': 'A151218_145728_hlavni-nadrazi_plap',
            'ext': 'flv',
            'title': 're:^Hlavní nádraží [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
    }, {  # idnes.cz
        'url': 'http://zpravy.idnes.cz/pes-zavreny-v-aute-rozbijeni-okynek-v-aute-fj5-/domaci.aspx?c=A150809_104116_domaci_pku',
        'skip': 'video gone',
        'md5': '819832ba33cd7016e58a6658577fe289',
        'info_dict': {
            'id': 'A150809_104116_domaci_pku',
            'ext': 'mp4',
            'title': 'Zavřeli jsme mraženou pizzu do auta. Upekla se',
            'description': 'md5:01e73f02329e2e5760bd5eed4d42e3c2',
            'thumbnail': r're:(?i)^https?://.*\.(?:jpg|png)$',
            'duration': 39,
            'timestamp': 1438969140,
            'upload_date': '20150807',
            'is_live': False,
        },
    }, {  # lidovky.cz
        'url': 'http://www.lidovky.cz/dalsi-demonstrace-v-praze-o-migraci-duq-/video.aspx?c=A150808_214044_ln-video_ELE',
        'skip': 'video gone',
        'md5': 'c7209ac4ba9d234d4ad5bab7485bcee8',
        'info_dict': {
            'id': 'A150808_214044_ln-video_ELE',
            'ext': 'mp4',
            'title': 'Táhni! Demonstrace proti imigrantům budila emoce',
            'description': 'md5:97c81d589a9491fbfa323c9fa3cca72c',
            'thumbnail': r're:(?i)^https?://.*\.(?:jpg|png)$',
            'timestamp': 1439052180,
            'upload_date': '20150808',
            'is_live': False,
        },
    }, {  # metro.cz
        'url': 'http://www.metro.cz/video-pod-billboardem-se-na-vltavske-roztocil-kolotoc-deti-vozil-jen-par-hodin-1hx-/metro-extra.aspx?c=A141111_173251_metro-extra_row',
        'skip': 'Unsupported URL / extractor broken',
        'md5': '84fc1deedcac37b7d4a6ccae7c716668',
        'info_dict': {
            'id': 'A141111_173251_metro-extra_row',
            'ext': 'mp4',
            'title': 'Recesisté udělali z billboardu kolotoč',
            'description': 'md5:7369926049588c3989a66c9c1a043c4c',
            'thumbnail': r're:(?i)^https?://.*\.(?:jpg|png)$',
            'timestamp': 1415725500,
            'upload_date': '20141111',
            'is_live': False,
        },
    }]

    def _player_item(self, json_info):
        for item in (json_info or {}).get('items') or ():
            if item.get('type') in ('video', 'stream'):
                return item
        return None

    def _download_player_json(self, info_url, video_id, fatal=True):
        def transform_source(s):
            if not s:
                return '{}'
            start, end = s.find('{'), s.rfind('}')
            if start == -1 or end == -1:
                return '{}'
            return s[start:end + 1]

        return self._download_json(
            info_url, video_id, fatal=fatal, transform_source=transform_source) or {}

    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_info = self._download_player_json(
            update_url_query(
                f'https://servix.idnes.cz/media/video.aspx?idvideo={video_id}',
                {'type': 'js', 'reklama': '0'}),
            video_id, fatal=False)
        webpage = None
        item = self._player_item(json_info)

        if not item:
            # iDNES pay-or-consent wall; these cookies skip the interstitial.
            self._set_cookie('.idnes.cz', 'dCMP', 'click=1')
            self._set_cookie('.idnes.cz', 'kolbda', '2')
            webpage = self._download_webpage(url, video_id)
            info_url = self._html_search_regex(
                r'Misc\.video(?:FLV)?\(\s*{\s*data\s*:\s*"([^"]+)"', webpage, 'info url')
            json_info = self._download_player_json(
                update_url_query(urljoin(url, info_url), {'reklama': '0', 'type': 'js'}),
                video_id)
            item = self._player_item(json_info)
        if not item:
            raise ExtractorError('No suitable stream found')

        quality = qualities(('low', 'middle', 'high'))

        formats = []
        for fmt in item['video']:
            video_url = fmt.get('file')
            if not video_url:
                continue

            format_ = fmt['format']
            format_id = '{}_{}'.format(format_, fmt['quality'])
            preference = None

            if format_ in ('mp4', 'webm'):
                ext = format_
            elif format_ == 'rtmp':
                ext = 'flv'
            elif format_ == 'apple':
                ext = 'mp4'
                # Some streams have mp3 audio which does not play
                # well with ffmpeg filter aac_adtstoasc
                preference = -10
            elif format_ == 'adobe':  # f4m manifest fails with 404 in 80% of requests
                continue
            else:  # Other formats not supported yet
                continue

            formats.append({
                'url': video_url,
                'ext': ext,
                'format_id': format_id,
                'quality': quality(fmt.get('quality')),
                'preference': preference,
            })

        title = item['title']
        is_live = item['type'] == 'stream'
        description = None
        if webpage:
            description = self._og_search_description(webpage, default=None) or self._html_search_meta(
                'description', webpage, 'description', default=None)
        timestamp = None
        duration = None
        if not is_live:
            duration = int_or_none(item.get('length'))
            timestamp = parse_iso8601(item.get('published'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': urljoin('https:', item.get('image')),
            'duration': duration,
            'timestamp': timestamp,
            'is_live': is_live,
            'formats': formats,
        }
