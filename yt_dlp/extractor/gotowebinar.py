import urllib.parse

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_qs,
    remove_end,
    str_or_none,
    unified_timestamp,
    url_or_none,
)
from ..utils.traversal import traverse_obj


class GoToWebinarIE(InfoExtractor):
    IE_DESC = 'GoTo Webinar recordings'
    _VALID_URL = r'https?://(?:www\.)?register\.gotowebinar\.com/recording/(?:viewRecording/(?P<webinar_key>\d+)/(?P<recording_key>\d+)/(?P<email>[^/?#]+)|recordingView)'
    _TESTS = [{
        'url': 'https://register.gotowebinar.com/recording/recordingView?webinarKey=1747286048478532187&registrantEmail=emilyekummer%40washoeschools.net',
        'md5': 'a1c260ce68f4d2edd69e0d2f8436d575',
        'info_dict': {
            'id': '4988555068499044704',
            'ext': 'mp4',
            'title': 'WASHOE COUNTY SCHOOL DISTRICT - After the Holidays: Managing That Debt',
            'filesize': 47622410,
            'timestamp': 1736465449,
            'upload_date': '20250109',
            'uploader': 'Webinar Coordinator',
            'uploader_id': 'webinartraining@compsych.com',
        },
    }, {
        'url': 'https://register.gotowebinar.com/recording/viewRecording/3820737359913857806/8942545096850977295/dwusa@mac.com?registrantKey=553718877925384203&type=ABSENTEEEMAILRECORDINGLINK',
        'only_matching': True,
    }, {
        'url': 'https://register.gotowebinar.com/recording/recordingView?webinarKey=4564472299797030416&registrantEmail=aausman%40biglever.com',
        'only_matching': True,
    }]

    _BROKER_API = 'https://globalattspa.gotowebinar.com/api'
    _REGISTRATION_API = 'https://api-registrationservice.services.goto.com/registrationservice/api'

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        query = parse_qs(url)
        webinar_key = mobj.group('webinar_key') or traverse_obj(query, ('webinarKey', 0))
        recording_key = mobj.group('recording_key') or traverse_obj(query, ('recordingKey', 0))
        email = urllib.parse.unquote(mobj.group('email') or '') or traverse_obj(query, ('registrantEmail', 0))
        registrant_key = traverse_obj(query, ('registrantKey', 0))
        rec_type = traverse_obj(query, ('type', 0))
        recurrence_key = traverse_obj(query, ('recurrenceKey', 0))
        display_id = recording_key or webinar_key or 'recording'

        if not webinar_key:
            raise ExtractorError('Unable to extract webinar key', expected=True)

        # Follow-up email links already include the registrant key and association type.
        if not (registrant_key and rec_type in (
                'ABSENTEEEMAILRECORDINGLINK', 'ATTENDEEEMAILRECORDINGLINK')):
            if '/viewRecording/' in url:
                registrant_key = self._lookup_registrant_key(webinar_key, email, display_id)
                rec_type = rec_type or 'FOLLOWUPEMAILRECORDINGLINK'
            else:
                registrant_key = registrant_key or self._lookup_registrant_key(
                    webinar_key, email, display_id)
                rec_type = rec_type or 'REGISTRATION'

        assets = self._download_recording_assets(
            webinar_key, registrant_key, rec_type, recurrence_key, display_id)
        recording_key = str_or_none(traverse_obj(assets, 'recordingKey')) or recording_key
        video_id = recording_key or webinar_key
        media_url = url_or_none(traverse_obj(assets, 'cdnLocation'))
        if not media_url:
            raise ExtractorError('Unable to extract recording URL', expected=True)

        webinar = self._download_json(
            f'{self._BROKER_API}/V2/webinars/{webinar_key}', video_id,
            note='Downloading webinar metadata', fatal=False) or {}
        recording = {}
        if recording_key:
            recording = self._download_json(
                f'{self._BROKER_API}/V2/webinars/{webinar_key}/registrants/{registrant_key}/recordings/{recording_key}',
                video_id, note='Downloading recording metadata', fatal=False) or {}

        title = (
            traverse_obj(webinar, 'subject', expected_type=str)
            or remove_end(traverse_obj(recording, 'title', expected_type=str) or '', '.mp4')
            or None)

        return {
            'id': video_id,
            'title': title,
            'url': media_url,
            'ext': 'mp4',
            'filesize': int_or_none(traverse_obj(recording, 'sizeInBytes')),
            'timestamp': unified_timestamp(
                traverse_obj(recording, 'createDate')
                or traverse_obj(webinar, ('webinarTimes', 0, 'startTime'))),
            'uploader': traverse_obj(webinar, ('replyTo', 'name'), expected_type=str),
            'uploader_id': traverse_obj(webinar, ('replyTo', 'email'), expected_type=str),
        }

    def _lookup_registrant_key(self, webinar_key, email, video_id):
        if not email:
            raise ExtractorError(
                'This recording URL is missing a registrant email or key', expected=True)
        registrant = self._download_json(
            f'{self._BROKER_API}/V2/webinars/{webinar_key}/registrants',
            video_id, query={'email': email},
            note='Downloading registrant metadata')
        registrant_key = str_or_none(traverse_obj(registrant, 'registrantKey'))
        if not registrant_key:
            raise ExtractorError('Unable to extract registrant key', expected=True)
        return registrant_key

    def _download_recording_assets(
            self, webinar_key, registrant_key, rec_type, recurrence_key, video_id):
        if recurrence_key:
            assets_url = (
                f'{self._REGISTRATION_API}/v1/recurrences/{recurrence_key}/webinars/'
                f'{webinar_key}/registrants/{registrant_key}/recordingAssets')
        else:
            assets_url = (
                f'{self._REGISTRATION_API}/v1/webinars/{webinar_key}/registrants/'
                f'{registrant_key}/recordingAssets')
        return self._download_json(
            assets_url, video_id, query={'type': rec_type, 'client': 'spa'},
            note='Downloading recording assets')
