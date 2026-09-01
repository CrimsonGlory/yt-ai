from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    join_nonempty,
    parse_iso8601,
    str_or_none,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class ScratchIE(InfoExtractor):
    IE_NAME = 'scratch'
    IE_DESC = 'Scratch'
    _VALID_URL = r'https?://(?:www\.)?scratch\.mit\.edu/projects/(?P<id>\d+)/?(?:[?#]|$)'
    _TESTS = [{
        'url': 'https://scratch.mit.edu/projects/1107181129/',
        'md5': '6561485779e59d8028fb324624949a5e',
        'info_dict': {
            'id': '1107181129',
            'ext': 'wav',
            'title': 'Adventure with Scratch Cat',
            'alt_title': 'Meow',
            'description': 'md5:c78827c264b867cdd041d57b0e11d0fa',
            'thumbnail': r're:https://cdn2\.scratch\.mit\.edu/get_image/project/1107181129_',
            'duration': float,
            'timestamp': 1734462151,
            'upload_date': '20241217',
            'uploader': 'Scratchteam',
            'uploader_id': 'Scratchteam',
            'uploader_url': 'https://scratch.mit.edu/users/Scratchteam/',
            'view_count': int,
            'like_count': int,
            'repost_count': int,
        },
    }, {
        'url': 'https://scratch.mit.edu/projects/1111552152/',
        'info_dict': {
            'id': '1111552152',
            'title': 'Folding a Paper Plane Tutorial',
            'description': 'md5:cbe7893a48c041a2db1466a31d8a4704',
        },
        'playlist_count': 2,
    }, {
        'url': 'https://scratch.mit.edu/projects/1107181129',
        'only_matching': True,
    }, {
        'url': 'https://www.scratch.mit.edu/projects/1107181129/',
        'only_matching': True,
    }]
    _ASSET_URL = 'https://assets.scratch.mit.edu/internalapi/asset/{}/get/'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            f'https://api.scratch.mit.edu/projects/{video_id}', video_id,
            headers={'Accept': 'application/json'}, expected_status=404)
        if not traverse_obj(data, ('id', {int_or_none})):
            raise ExtractorError(
                'This Scratch project is unshared or does not exist', expected=True)

        token = traverse_obj(data, ('project_token', {str}))
        project = self._download_json(
            f'https://projects.scratch.mit.edu/{video_id}', video_id,
            query={'token': token} if token else {})
        sounds = self._extract_sounds(project)

        uploader = traverse_obj(data, ('author', 'username', {str}))
        description = join_nonempty(
            'instructions', 'description', delim='\n\n', from_dict=data) or None
        common = {
            'title': traverse_obj(data, ('title', {str})) or video_id,
            'description': description,
            'thumbnail': url_or_none(data.get('image')),
            'uploader': uploader,
            'uploader_id': uploader,
            'uploader_url': f'https://scratch.mit.edu/users/{uploader}/' if uploader else None,
            **traverse_obj(data, {
                'timestamp': ('history', ('shared', 'created'), {parse_iso8601}, any),
                'view_count': ('stats', 'views', {int_or_none}),
                'like_count': ('stats', 'loves', {int_or_none}),
                'repost_count': ('stats', 'remixes', {int_or_none}),
            }),
        }

        if not sounds:
            self.raise_no_formats(
                'This Scratch project has no sounds', expected=True, video_id=video_id)
            return {'id': video_id, **common}

        entries = [
            self._extract_sound(video_id, sound, idx, common)
            for idx, sound in enumerate(sounds)]
        if len(entries) == 1:
            entries[0]['id'] = video_id
            return entries[0]
        return self.playlist_result(
            entries, video_id, common.get('title'), description)

    def _extract_sound(self, video_id, sound, idx, common):
        ext = sound['ext']
        rate = sound.get('rate')
        return {
            **common,
            'id': f'{video_id}-{idx}',
            'alt_title': sound.get('name'),
            'duration': float_or_none(sound.get('sample_count'), scale=rate) if rate else None,
            'formats': [{
                'url': self._ASSET_URL.format(sound['md5ext']),
                'ext': ext,
                'format_id': ext,
                'vcodec': 'none',
                'acodec': {
                    'mp3': 'mp3',
                    'wav': 'wav',
                    'ogg': 'vorbis',
                }.get(ext),
                'asr': rate,
                'http_headers': {'Referer': 'https://scratch.mit.edu/'},
            }],
        }

    def _extract_sounds(self, project):
        sounds, seen = [], set()

        def add_sound(raw):
            parsed = self._parse_sound(raw)
            if not parsed or parsed['md5ext'] in seen:
                return
            seen.add(parsed['md5ext'])
            sounds.append(parsed)

        targets = traverse_obj(project, ('targets', ..., {dict}))
        if targets:
            for target in targets:
                for sound in traverse_obj(target, ('sounds', ..., {dict})):
                    add_sound(sound)
            return sounds

        def walk_scratch2(obj):
            if not isinstance(obj, dict):
                return
            for sound in traverse_obj(obj, ('sounds', ..., {dict})):
                add_sound(sound)
            for child in obj.get('children') or []:
                walk_scratch2(child)

        walk_scratch2(project)
        return sounds

    @staticmethod
    def _parse_sound(sound):
        data_format = (str_or_none(sound.get('dataFormat')) or '').lower() or None
        md5ext = str_or_none(sound.get('md5ext') or sound.get('md5'))
        asset_id = str_or_none(sound.get('assetId'))
        if not md5ext and asset_id and data_format:
            md5ext = f'{asset_id}.{data_format}'
        if not md5ext or '.' not in md5ext:
            return None
        if not data_format:
            data_format = md5ext.rsplit('.', 1)[-1].lower()
        return {
            'name': str_or_none(sound.get('name') or sound.get('soundName')),
            'md5ext': md5ext,
            'asset_id': asset_id or md5ext.rsplit('.', 1)[0],
            'ext': data_format,
            'rate': int_or_none(sound.get('rate')),
            'sample_count': int_or_none(sound.get('sampleCount')),
        }
