from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class XinpianchangIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?xinpianchang\.com/(?P<id>a\d+)'
    IE_DESC = '新片场'
    _TESTS = [
        {
            'url': 'https://www.xinpianchang.com/a13805701',
            'md5': 'ec93b242ac8475cf8886e4572b582be1',
            'info_dict': {
                'id': 'a13805701',
                'ext': 'mp4',
                'title': '创作人纪录片系列｜全网播放量破亿AI短片背后的Mx-Shell',
                'description': '《丧尸清道夫》爆火，全网播放量破亿，\n我们这一次走进了这个作品背后创作人Mx-Shell的生活，\n来看看他的故事。',
                'uploader': '场长Ethan',
                'uploader_id': '10000016',
                'duration': 548,
                'thumbnail': 'https://oss-xpc0.xpccdn.com/uploadfile/article/2026/9/3/4e6cd71453243e9458e323107c7a1686',
                'categories': ['纪录片', '人物/社会', '人物', '人物纪实'],
                'tags': ['AI', 'AIGC', 'Shotlab', '丧尸清道夫', 'Mx-Shell'],
            },
        }, {
        'url': 'https://www.xinpianchang.com/a13798806',
        'skip': 'stale test sample / site changed',
        'md5': '2118d84226070b2c95406832783301d6',
        'info_dict': {
            'id': 'a13798806',
            'ext': 'mp4',
            'title': '「无人驾驶」Driverless｜AIGC短片',
            'description': 'md5:ab84697f661cce8adf52dcf3c0c59c1e',
            'duration': 519,
            'thumbnail': r're:^https?://oss-xpc0\.xpccdn\.com/',
            'uploader': '田',
            'uploader_id': '10054991',
            'categories': ['剧情短片', '科幻', 'AIGC', '创意'],
            'tags': ['AIGC', 'AI短片', '剧情短片', 'AI'],
        },
    }, {
        'url': 'https://www.xinpianchang.com/a11766551',
        'md5': '0db6e8566cb82c01ec12b587b4a78cf8',
        'info_dict': {
            'id': 'a11766551',
            'ext': 'mp4',
            'title': '北京2022冬奥会闭幕式再见短片-冰墩墩下班了',
            'description': 'md5:4a730c10639a82190fabe921c0fa4b87',
            'duration': 151,
            'thumbnail': r're:^https?://oss-xpc0\.xpccdn\.com.+/assets/',
            'uploader': '正时文创',
            'uploader_id': '10357277',
            'categories': ['宣传片', '国家城市', '广告', '其他'],
            'tags': ['北京冬奥会', '冰墩墩', '再见', '告别', '冰墩墩哭了', '感动', '闭幕式', '熄火'],
        },
    }, {
        'url': 'https://www.xinpianchang.com/a11762904',
        'skip': 'DASH audio URL has no host',
        'info_dict': {
            'id': 'a11762904',
            'ext': 'mp4',
            'title': '冬奥会决胜时刻《法国派出三只鸡？》',
            'description': 'md5:55cb139ef8f48f0c877932d1f196df8b',
            'duration': 136,
            'thumbnail': r're:^https?://oss-xpc0\.xpccdn\.com.+/assets/',
            'uploader': '精品动画',
            'uploader_id': '10858927',
            'categories': ['动画', '三维CG'],
            'tags': ['France Télévisions', '法国3台', '蠢萌', '冬奥会'],
        },
    }, {
        'url': 'https://www.xinpianchang.com/a11779743?from=IndexPick&part=%E7%BC%96%E8%BE%91%E7%B2%BE%E9%80%89&index=2',
        'only_matching': True,
    }]

    def _extract_video_data(self, url, video_id):
        # Article HTML is gated by a Wangsu JS challenge; Next.js data is public.
        homepage = self._download_webpage(
            'https://www.xinpianchang.com/', video_id, note='Downloading homepage')
        build_id = self._search_nextjs_data(homepage, video_id)['buildId']
        article = self._download_json(
            f'https://www.xinpianchang.com/_next/data/{build_id}/{video_id}.json',
            video_id, note='Downloading article data',
            headers={'Referer': url, 'X-Nextjs-Data': '1'})
        video_data = traverse_obj(article, ('pageProps', 'detail', 'video', {dict}))
        if not traverse_obj(video_data, 'vid'):
            raise ExtractorError('Unable to extract video data', expected=True)
        return video_data

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._extract_video_data(url, video_id)

        data = self._download_json(
            f'https://mod-api.xinpianchang.com/mod/api/v2/media/{video_data["vid"]}', video_id,
            query={'appKey': video_data['appKey']})['data']
        formats, subtitles = [], {}
        for k, v in (data.get('resource') or {}).items():
            if k in ('dash', 'hls'):
                v_url = v.get('url')
                if not v_url:
                    continue
                if k == 'dash':
                    fmts, subs = self._extract_mpd_formats_and_subtitles(v_url, video_id=video_id)
                elif k == 'hls':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(v_url, video_id=video_id)
                formats.extend(fmts)
                subtitles = self._merge_subtitles(subtitles, subs)
            elif k == 'progressive':
                formats.extend([{
                    'url': url_or_none(prog.get('url')),
                    'width': int_or_none(prog.get('width')),
                    'height': int_or_none(prog.get('height')),
                    'ext': 'mp4',
                    'http_headers': {
                        # CDN auth requires Range + Referer
                        'Range': 'bytes=0-',
                        'Referer': 'https://www.xinpianchang.com/',
                    },
                } for prog in v if url_or_none(prog.get('url'))])

        return {
            'id': video_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'duration': int_or_none(data.get('duration')),
            'categories': data.get('categories'),
            'tags': data.get('keywords'),
            'thumbnail': data.get('cover'),
            'uploader': traverse_obj(data, ('owner', 'username', {str})),
            'uploader_id': traverse_obj(data, ('owner', 'id', {str_or_none})),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': {
                'Referer': 'https://www.xinpianchang.com/',
            },
        }
