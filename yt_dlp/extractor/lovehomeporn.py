from .nuevo import NuevoBaseIE


class LoveHomePornIE(NuevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?lovehomeporn\.com/video/(?P<id>\d+)(?:/(?P<display_id>[^/?#&]+))?'
    _TESTS = [{
        'url': 'https://lovehomeporn.com/video/133980/fitness-instructor-comes-for-private-home-session-and-ends-up-riding-my-cock-hard',
        'info_dict': {
            'id': '133980',
            'display_id': 'fitness-instructor-comes-for-private-home-session-and-ends-up-riding-my-cock-hard',
            'ext': 'mp4',
            'title': 'Fitness Instructor Comes for Private Home Session and Ends Up Riding My Cock Hard',
            'age_limit': 18,
            'duration': 862.0,
            'thumbnail': r're:https://cdn\.static\.lovehomeporn\.com/.+',
        },
    }, {
        'url': 'http://lovehomeporn.com/video/48483/stunning-busty-brunette-girlfriend-sucking-and-riding-a-big-dick#menu',
        'info_dict': {
            'id': '48483',
            'display_id': 'stunning-busty-brunette-girlfriend-sucking-and-riding-a-big-dick',
            'ext': 'mp4',
            'title': 'Stunning busty brunette girlfriend sucking and riding a big dick',
            'age_limit': 18,
            'duration': 238.47,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Nuevo config XML no longer valid',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        info = self._extract_nuevo(
            f'http://lovehomeporn.com/media/nuevo/config.php?key={video_id}',
            video_id)
        info.update({
            'display_id': display_id,
            'age_limit': 18,
        })
        return info
